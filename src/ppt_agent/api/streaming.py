import json
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

from ppt_agent.config import _current_session_dir, settings


async def event_stream_generator(agent, message: str, config: dict, session_id: str) -> AsyncGenerator[str, None]:
    seen_ids = set()

    # Set session context for this generator
    session_dir = settings.output_dir / session_id
    token = _current_session_dir.set(session_dir)

    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config,
        )

        for msg in result.get("messages", []):
            msg_id = getattr(msg, "id", None)
            if msg_id and msg_id in seen_ids:
                continue
            if msg_id:
                seen_ids.add(msg_id)

            if msg.type == "ai":
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        event = {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if msg.content:
                    event = {"type": "content", "content": msg.content}
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif msg.type == "tool":
                content = str(msg.content)
                if len(content) > 1000:
                    content = content[:1000] + "...(truncated)"
                event = {"type": "tool_result", "name": msg.name, "content": content}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        event = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    finally:
        _current_session_dir.reset(token)
