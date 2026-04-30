import asyncio
import json
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

from ppt_agent.config import _current_session_dir, settings
from ppt_agent.progress import create_queue, remove_queue


def _format_sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def event_stream_generator(
    agent, message: str, config: dict, session_id: str
) -> AsyncGenerator[str, None]:
    queue = create_queue(session_id)
    session_dir = settings.output_dir / session_id
    token = _current_session_dir.set(session_dir)

    try:
        # Run agent in background task
        result_holder: dict = {}

        async def run_agent():
            try:
                result = await agent.ainvoke(
                    {"messages": [HumanMessage(content=message)]},
                    config,
                )
                result_holder["result"] = result
            except Exception as e:
                result_holder["error"] = e

        agent_task = asyncio.create_task(run_agent())

        # Yield slide progress events from queue while agent runs
        while not agent_task.done():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.3)
                yield _format_sse(event)
            except asyncio.TimeoutError:
                continue

        # Drain remaining queue events
        while not queue.empty():
            try:
                event = queue.get_nowait()
                yield _format_sse(event)
            except asyncio.QueueEmpty:
                break

        # Process agent result → yield message history events
        if "error" in result_holder:
            yield _format_sse(
                {"type": "error", "message": str(result_holder["error"])}
            )
            yield "data: [DONE]\n\n"
            return

        result = result_holder["result"]
        seen_ids = set()

        for msg in result.get("messages", []):
            msg_id = getattr(msg, "id", None)
            if msg_id and msg_id in seen_ids:
                continue
            if msg_id:
                seen_ids.add(msg_id)

            if msg.type == "ai":
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        # Skip generate_slides tool_call — slides shown via queue
                        if tc["name"] == "generate_slides":
                            continue
                        yield _format_sse(
                            {
                                "type": "tool_call",
                                "name": tc["name"],
                                "args": tc["args"],
                            }
                        )
                if msg.content:
                    yield _format_sse({"type": "content", "content": msg.content})

            elif msg.type == "tool":
                content = str(msg.content)
                if len(content) > 1000 and msg.name != "generate_outline":
                    content = content[:1000] + "...(truncated)"
                yield _format_sse(
                    {"type": "tool_result", "name": msg.name, "content": content}
                )

        yield "data: [DONE]\n\n"

    except Exception as e:
        yield _format_sse({"type": "error", "message": str(e)})
    finally:
        _current_session_dir.reset(token)
        remove_queue(session_id)
