import asyncio
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from ppt_agent.agent.agent import create_ppt_agent
from ppt_agent.agent.state import PipelineStep, SessionEntry, SessionIndex, SessionState
from ppt_agent.config import _current_session_dir, settings
from ppt_agent.tools.upload import upload_and_parse


def _print_new_messages(result: dict, seen: set) -> set:
    for msg in result.get("messages", []):
        msg_id = getattr(msg, "id", None)
        if msg_id and msg_id in seen:
            continue
        if msg_id:
            seen.add(msg_id)

        if msg.type == "ai":
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n[TOOL] 调用: {tc['name']}({tc['args']})")
            if msg.content:
                print(f"\n助手: {msg.content}\n")
        elif msg.type == "tool":
            content = str(msg.content)
            if len(content) > 500:
                content = content[:500] + f"... ({len(str(msg.content))} chars)"
            print(f"\n[TOOL 结果] {msg.name}: {content}")


def _create_new_session() -> str:
    """Create a new session directory and index entry, return the session_id."""
    session_id = uuid.uuid4().hex[:8]
    session_dir = settings.output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    state = SessionState(
        session_id=session_id,
        created_at=now,
    )
    state.save(session_dir / "session.json")

    index = SessionIndex(settings.output_dir / "index.json")
    index.add(SessionEntry(
        session_id=session_id,
        created_at=now,
    ))

    return session_id


async def cli():
    agent = create_ppt_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    seen_ids: set = set()
    current_session_id: str | None = None

    print(f"PPT-Agent (model: {settings.model})")
    print("输入需求开始制作 PPT，输入 /new 新建，输入 /upload 上传文件，输入 /quit 退出\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("再见！")
            break

        if user_input == "/new":
            session_id = _create_new_session()
            session_dir = settings.output_dir / session_id
            _current_session_dir.set(session_dir)
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            seen_ids = set()
            current_session_id = session_id
            print(f"[新会话] {session_id}\n")
            continue

        if user_input == "/upload":
            # Auto-create session if none active
            if current_session_id is None:
                session_id = _create_new_session()
                session_dir = settings.output_dir / session_id
                _current_session_dir.set(session_dir)
                thread_id = str(uuid.uuid4())
                config = {"configurable": {"thread_id": thread_id}}
                seen_ids = set()
                current_session_id = session_id
            try:
                file_path = input("文件路径: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not file_path:
                continue
            if file_path == "/quit":
                break
            result = upload_and_parse.invoke({"file_path": file_path})
            print(f"\n[上传] {result}\n")
            continue

        # Auto-create session if none active
        if current_session_id is None:
            # Check if last session was completed (auto-reset scenario)
            session_id = _create_new_session()
            session_dir = settings.output_dir / session_id
            _current_session_dir.set(session_dir)
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            seen_ids = set()
            current_session_id = session_id
        else:
            # Check if previous PPT was exported — auto-start new session
            session_dir = settings.output_dir / current_session_id
            state = SessionState.load(session_dir / "session.json")
            if state.step == PipelineStep.EXPORTED:
                session_id = _create_new_session()
                session_dir = settings.output_dir / session_id
                _current_session_dir.set(session_dir)
                thread_id = str(uuid.uuid4())
                config = {"configurable": {"thread_id": thread_id}}
                seen_ids = set()
                current_session_id = session_id

        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config,
            )
            _print_new_messages(result, seen_ids)
        except GraphInterrupt:
            # Print partial messages from the interrupted invocation
            try:
                state_snapshot = await agent.aget_state(config)
                if state_snapshot and state_snapshot.values:
                    _print_new_messages(state_snapshot.values, seen_ids)
            except Exception:
                pass
            print("\n[等待确认] 输入 'ok' 继续，或输入修改意见：")
            try:
                feedback = input("你: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if feedback == "/quit":
                break
            try:
                result = await agent.ainvoke(Command(resume=feedback), config)
                _print_new_messages(result, seen_ids)
            except Exception as e:
                print(f"\n[错误] {e}\n")
        except KeyboardInterrupt:
            print("\n[已中断]")
        except Exception as e:
            print(f"\n[错误] {e}\n")


def main():
    asyncio.run(cli())


if __name__ == "__main__":
    main()
