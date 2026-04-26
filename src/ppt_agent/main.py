import asyncio
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from ppt_agent.agent.agent import create_ppt_agent
from ppt_agent.config import settings


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


async def cli():
    agent = create_ppt_agent()
    thread_id = "cli-session"
    config = {"configurable": {"thread_id": thread_id}}
    seen_ids: set = set()

    print(f"PPT-Agent (model: {settings.model})")
    print("输入需求开始制作 PPT，输入 /quit 退出\n")

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

        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config,
            )
            _print_new_messages(result, seen_ids)
        except GraphInterrupt:
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
