import uvicorn

from ppt_agent.api.app import app
from ppt_agent.config import settings


def main():
    uvicorn.run("ppt_agent.api.app:app", host=settings.api_host, port=settings.api_port, reload=True)


if __name__ == "__main__":
    main()
