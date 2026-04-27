from fastapi import Request


async def get_agent(request: Request):
    return request.app.state.agent
