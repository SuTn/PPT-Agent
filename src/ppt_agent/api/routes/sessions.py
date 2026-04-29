import asyncio
import json
import re
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ppt_agent.agent.state import SessionEntry, SessionIndex, PipelineStep, SessionState
from ppt_agent.api.deps import get_agent
from ppt_agent.api.streaming import event_stream_generator
from ppt_agent.config import _current_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.tools.export import do_export
from ppt_agent.tools.slide_gen import _generate_one_slide, _is_valid_html

router = APIRouter()


class MessageRequest(BaseModel):
    content: str


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
    agent=Depends(get_agent),
):
    _validate_session(session_id)
    config = {"configurable": {"thread_id": session_id}}

    return StreamingResponse(
        event_stream_generator(agent, message, config, session_id),
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
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    file_path = session_dir / "slides" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        str(file_path),
        headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:;"},
    )


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
