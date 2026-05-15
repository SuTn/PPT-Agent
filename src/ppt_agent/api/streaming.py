import asyncio
import json
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

from ppt_agent.config import _current_session_dir, settings
from ppt_agent.progress import create_queue, get_queue, has_queue, remove_queue

# PPT-specific tools visible in the chat UI.
# Filesystem tools from FilesystemBackend (ls, glob, read, write, etc.)
# and deepagents internals (write_todos, etc.) are hidden.
_VISIBLE_TOOLS = frozenset({
    "research_topic",
    "generate_outline",
    "generate_slides",
    "upload_and_parse",
    "export_pptx",
    "select_template",
})


def _format_sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _start_agent_stream(agent, message: str, config: dict, session_id: str, queue: asyncio.Queue):
    """Run agent.astream() and push all events into the queue.

    The queue is created by the caller (event_stream_generator) so it
    always exists before the SSE generator tries to read from it.
    """
    session_dir = settings.output_dir / session_id
    token = _current_session_dir.set(session_dir)
    try:
        async for chunk in agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config,
            stream_mode="updates",
        ):
            for node_name, update in chunk.items():
                if node_name == "model":
                    for msg in update.get("messages", []):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                name = tc["name"]
                                if name in _VISIBLE_TOOLS and name != "generate_slides":
                                    await queue.put({
                                        "type": "tool_call",
                                        "name": name,
                                        "args": tc.get("args", {}),
                                    })
                        if msg.content:
                            await queue.put({"type": "content", "content": msg.content})

                elif node_name == "tools":
                    for msg in update.get("messages", []):
                        if msg.type == "tool":
                            name = msg.name or ""
                            if name not in _VISIBLE_TOOLS:
                                continue
                            content = str(msg.content)
                            if len(content) > 1000 and name != "generate_outline":
                                content = content[:1000] + "...(truncated)"
                            await queue.put({
                                "type": "tool_result",
                                "name": name,
                                "content": content,
                            })
    except Exception as e:
        await queue.put({"type": "error", "message": str(e)})
    finally:
        await queue.put({"type": "_done"})
        _current_session_dir.reset(token)
        remove_queue(session_id)


async def event_stream_generator(
    agent, message: str, config: dict, session_id: str
) -> AsyncGenerator[str, None]:
    """SSE generator that yields events from the agent's queue.

    If a queue already exists (reconnect after page refresh), yield from it
    instead of starting a new agent run.
    """
    if has_queue(session_id):
        queue = get_queue(session_id)
    else:
        # Create queue BEFORE starting the task so it's immediately available
        queue = create_queue(session_id)
        asyncio.create_task(_start_agent_stream(agent, message, config, session_id, queue))

    if not queue:
        yield _format_sse({"type": "error", "message": "Failed to create event queue"})
        return

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                # If queue was removed, agent task has finished
                if not has_queue(session_id):
                    break
                continue
            if event.get("type") == "_done":
                break
            yield _format_sse(event)

        yield "data: [DONE]\n\n"
    except Exception as e:
        yield _format_sse({"type": "error", "message": str(e)})
