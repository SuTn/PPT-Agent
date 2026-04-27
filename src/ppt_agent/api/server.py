import asyncio
import sys

import uvicorn

from ppt_agent.api.app import app
from ppt_agent.config import settings


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run("ppt_agent.api.app:app", host=settings.api_host, port=settings.api_port, reload=True)


if __name__ == "__main__":
    main()
