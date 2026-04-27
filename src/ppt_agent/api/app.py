from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import MemorySaver

from ppt_agent.agent.agent import create_ppt_agent
from ppt_agent.api.routes import sessions, templates, upload
from ppt_agent.config import _current_session_dir, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = create_ppt_agent(checkpointer=MemorySaver())
    yield


app = FastAPI(title="PPT-Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def session_context_middleware(request: Request, call_next):
    # Extract session_id from URL path /api/v1/sessions/{session_id}/...
    parts = request.url.path.split("/")
    session_id = None
    if len(parts) >= 5 and parts[1] == "api" and parts[2] == "v1" and parts[3] == "sessions":
        session_id = parts[4]

    token = None
    if session_id:
        session_dir = settings.output_dir / session_id
        token = _current_session_dir.set(session_dir)
    try:
        return await call_next(request)
    finally:
        if token:
            _current_session_dir.reset(token)


app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
