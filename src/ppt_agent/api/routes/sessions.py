import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ppt_agent.agent.state import SessionEntry, SessionIndex, SessionState
from ppt_agent.api.deps import get_agent
from ppt_agent.api.streaming import event_stream_generator
from ppt_agent.config import settings

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
