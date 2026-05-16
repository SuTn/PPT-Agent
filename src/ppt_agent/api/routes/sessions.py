import asyncio
import json
import re
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ppt_agent.agent.state import SessionEntry, SessionIndex, PipelineStep, SessionState
from ppt_agent.api.deps import get_agent
from ppt_agent.api.streaming import event_stream_generator
from ppt_agent.config import _current_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.slide import AI_EDIT_SYSTEM_PROMPT
from ppt_agent.tools.export import do_export
from ppt_agent.tools.slide_gen import _generate_one_slide, _is_valid_html
from ppt_agent.agent.agent import create_ppt_agent
from ppt_agent.templates.registry import apply_template_to_session

router = APIRouter()


class MessageRequest(BaseModel):
    content: str


class TemplateRequest(BaseModel):
    template_key: str


class AiEditRequest(BaseModel):
    instruction: str


@router.post("")
async def create_session(title: str = ""):
    session_id = uuid.uuid4().hex[:8]
    session_dir = settings.output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    state = SessionState(session_id=session_id, created_at=now, title=title)
    state.save(session_dir / "session.json")

    index = SessionIndex(settings.output_dir / "index.json")
    index.add(SessionEntry(session_id=session_id, created_at=now, title=title))

    return {"session_id": session_id, "created_at": now}


@router.patch("/{session_id}/template")
async def set_session_template(session_id: str, body: TemplateRequest):
    _validate_session(session_id)
    session_dir = settings.output_dir / session_id
    try:
        spec = apply_template_to_session(body.template_key, session_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "message": f"模板「{spec['name']}」已选择",
        "template_key": body.template_key,
        "template_name": spec["name"],
        "step": "template_done",
    }


@router.get("")
async def list_sessions():
    index = SessionIndex(settings.output_dir / "index.json")
    return {"sessions": [e.model_dump() for e in index.list_all()]}


@router.get("/{session_id}")
async def get_session(session_id: str, agent=Depends(get_agent)):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    state = SessionState.load(session_dir / "session.json")

    # Load chat history from checkpointer
    config = {"configurable": {"thread_id": session_id}}
    messages = []
    try:
        snapshot = await agent.aget_state(config)
        if snapshot and snapshot.values:
            for msg in snapshot.values.get("messages", []):
                messages.append(_msg_to_dict(msg))
    except Exception:
        pass

    result = state.model_dump()
    result["messages"] = messages
    return result


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    shutil.rmtree(session_dir)
    return {"message": "Deleted"}


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    body: MessageRequest,
    agent=Depends(get_agent),
):
    from langchain_core.messages import HumanMessage

    _validate_session(session_id)
    config = {"configurable": {"thread_id": session_id}}

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=body.content)]},
        config,
    )
    return {"messages": [_msg_to_dict(m) for m in result.get("messages", [])]}


@router.get("/{session_id}/stream")
async def stream_message(
    session_id: str,
    message: str,
    mode: str = "",
    request: Request = None,
    agent=Depends(get_agent),
):
    _validate_session(session_id)
    session_dir = settings.output_dir / session_id
    state = SessionState.load(session_dir / "session.json")

    if state.step.value not in (
        PipelineStep.TEMPLATE_DONE.value,
        PipelineStep.RESEARCH_DONE.value,
        PipelineStep.OUTLINE_DONE.value,
        PipelineStep.SLIDES_DONE.value,
        PipelineStep.EXPORTED.value,
    ):
        raise HTTPException(status_code=400, detail="请先选择模板")

    # Update mode if provided
    if mode in ("fast", "standard"):
        state.mode = mode
        state.save(session_dir / "session.json")

    # Create agent with mode-specific prompt
    checkpointer = request.app.state.checkpointer
    effective_agent = create_ppt_agent(checkpointer, mode=state.mode or "fast")

    config = {"configurable": {"thread_id": session_id}}

    return StreamingResponse(
        event_stream_generator(effective_agent, message, config, session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{session_id}/events")
async def stream_events(session_id: str):
    """Reconnect to a running agent task's event stream (e.g. after page refresh)."""
    _validate_session(session_id)
    from ppt_agent.progress import has_queue
    if not has_queue(session_id):
        raise HTTPException(status_code=404, detail="No running task for this session")
    return StreamingResponse(
        event_stream_generator(None, "", {}, session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{session_id}/download")
async def download_pptx(session_id: str):
    _validate_session(session_id)
    state = SessionState.load(settings.output_dir / session_id / "session.json")
    if not state.pptx_file:
        raise HTTPException(status_code=404, detail="PPTX not yet generated")
    return FileResponse(state.pptx_file, filename=state.pptx_file.split("/")[-1])


@router.get("/{session_id}/slides")
async def list_slides(session_id: str):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    slides_dir = session_dir / "slides"
    if not slides_dir.exists():
        return {"slides": []}
    slides = []
    for f in sorted(slides_dir.iterdir()):
        if f.suffix == ".html":
            name_match = re.match(r"slide_(\d+)_(.+)", f.stem)
            page = int(name_match.group(1)) if name_match else 0
            layout = name_match.group(2) if name_match else "content"
            png_path = f.with_suffix(".png")
            slides.append({
                "page": page,
                "layout": layout,
                "filename": f.name,
                "has_png": png_path.exists(),
            })
    return {"slides": slides}


@router.get("/{session_id}/slides/{filename}")
async def get_slide_file(session_id: str, filename: str):
    _validate_session(session_id)
    if not re.match(r"^slide_\d+_[a-z_]+\.html$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path = settings.output_dir / session_id / "slides" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        str(file_path),
        headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:;"},
    )


@router.put("/{session_id}/slides/{filename}")
async def save_slide(session_id: str, filename: str, body: dict):
    _validate_session(session_id)

    if not re.match(r"^slide_\d+_[a-z_]+\.html$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    session_dir = settings.output_dir / session_id
    file_path = session_dir / "slides" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    html_content = body.get("html", "")
    if not html_content or not _is_valid_html(html_content):
        raise HTTPException(status_code=400, detail="Invalid HTML content")

    backup = file_path.with_suffix(".html.bak")
    shutil.copy2(file_path, backup)

    try:
        file_path.write_text(html_content, encoding="utf-8")
        png_path = file_path.with_suffix(".png")
        if png_path.exists():
            png_path.unlink()
        page = int(re.match(r"slide_(\d+)", filename).group(1))
        return {"filename": filename, "page": page, "size": len(html_content.encode("utf-8"))}
    except Exception as e:
        shutil.copy2(backup, file_path)
        raise HTTPException(status_code=500, detail=f"Save failed: {e}")
    finally:
        backup.unlink(missing_ok=True)


@router.get("/{session_id}/research")
async def get_research_notes(session_id: str):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    notes_path = session_dir / "research_notes.md"
    if not notes_path.exists():
        raise HTTPException(status_code=404, detail="Research notes not found")
    content = notes_path.read_text(encoding="utf-8")
    return {"content": content}


@router.get("/{session_id}/outline")
async def get_outline(session_id: str):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    outline_path = session_dir / "outline.json"
    if not outline_path.exists():
        raise HTTPException(status_code=404, detail="Outline not found")
    return json.loads(outline_path.read_text(encoding="utf-8"))


@router.post("/{session_id}/export")
async def export_session(session_id: str):
    _validate_session(session_id)
    session_dir = settings.output_dir / session_id
    state = SessionState.load(session_dir / "session.json")
    if state.step != PipelineStep.SLIDES_DONE and state.step != PipelineStep.EXPORTED:
        raise HTTPException(status_code=400, detail="幻灯片未就绪，无法导出")
    result = await do_export(session_dir)
    return {"message": result}


@router.post("/{session_id}/slides/{page}/retry")
async def retry_slide(session_id: str, page: int):
    _validate_session(session_id)
    session_dir = settings.output_dir / session_id
    state = SessionState.load(session_dir / "session.json")
    if state.step not in (PipelineStep.SLIDES_DONE, PipelineStep.EXPORTED):
        raise HTTPException(status_code=400, detail="幻灯片未就绪")

    outline_path = session_dir / "outline.json"
    style_spec_path = session_dir / "style_spec.json"
    if not outline_path.exists() or not style_spec_path.exists():
        raise HTTPException(status_code=400, detail="大纲或模板文件缺失")

    outline = json.loads(outline_path.read_text("utf-8"))
    style_spec = json.loads(style_spec_path.read_text("utf-8"))
    slide_info = next((s for s in outline["slides"] if s["page"] == page), None)
    if not slide_info:
        raise HTTPException(status_code=404, detail=f"第 {page} 页不存在")

    filename = f"slide_{page:02d}_{slide_info['layout']}.html"
    filepath = session_dir / "slides" / filename

    # Backup original file
    backup = filepath.with_suffix(".html.bak")
    if filepath.exists():
        shutil.copy2(filepath, backup)

    try:
        token = _current_session_dir.set(session_dir)
        try:
            model = get_model()
            sem = asyncio.Semaphore(1)
            _, html = await _generate_one_slide(
                sem, model, slide_info, len(outline["slides"]), style_spec, state.template_key or ""
            )
        finally:
            _current_session_dir.reset(token)

        if not html or not _is_valid_html(html):
            raise HTTPException(status_code=500, detail="重新生成失败：HTML 内容无效")

        filepath.write_text(html, encoding="utf-8")
        backup.unlink(missing_ok=True)
        return {"page": page, "filename": filename, "status": "regenerated"}
    except HTTPException:
        raise
    except Exception as e:
        # Restore backup on failure
        if backup.exists():
            shutil.copy2(backup, filepath)
            backup.unlink()
        raise HTTPException(status_code=500, detail=f"重新生成失败: {e}")


@router.post("/{session_id}/slides/{filename}/ai-edit")
async def ai_edit_slide(session_id: str, filename: str, body: AiEditRequest):
    _validate_session(session_id)
    if not re.match(r"^slide_\d+_[a-z_]+\.html$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    session_dir = settings.output_dir / session_id
    file_path = session_dir / "slides" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Slide not found")

    current_html = file_path.read_text(encoding="utf-8")

    from langchain_core.messages import SystemMessage, HumanMessage

    model = get_model()
    messages = [
        SystemMessage(content=AI_EDIT_SYSTEM_PROMPT),
        HumanMessage(content=f"当前幻灯片 HTML：\n\n{current_html}\n\n修改指令：{body.instruction}"),
    ]
    result = await model.ainvoke(messages)
    new_html = result.content.strip()

    # Strip markdown code block if present
    if new_html.startswith("```"):
        new_html = re.sub(r"^```(?:html)?\n?", "", new_html)
        new_html = re.sub(r"\n?```$", "", new_html)

    if not new_html or not _is_valid_html(new_html):
        raise HTTPException(status_code=500, detail="AI 生成的 HTML 无效")

    return {"html": new_html}


def _validate_session(session_id: str):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")


def _msg_to_dict(msg):
    d = {"type": msg.type}
    if msg.content:
        d["content"] = msg.content
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        d["tool_calls"] = msg.tool_calls
    if hasattr(msg, "name"):
        d["name"] = msg.name
    return d
