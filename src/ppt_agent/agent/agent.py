from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from ppt_agent.agent.prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_FAST
from ppt_agent.config import _current_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.tools.research import research_topic
from ppt_agent.tools.outline import generate_outline
from ppt_agent.tools.slide_gen import generate_slides
from ppt_agent.tools.upload import upload_and_parse

ALL_TOOLS = [
    research_topic,
    generate_outline,
    generate_slides,
    upload_and_parse,
]


class SessionFilesystemBackend(FilesystemBackend):
    """FilesystemBackend scoped to the current session directory.

    Overrides ``cwd`` so that all filesystem tools (ls, glob, grep, read, etc.)
    only see files within the active session directory.  Uses virtual_mode to
    enforce path containment and present clean virtual paths (e.g. ``/materials.md``).
    """

    def __init__(self) -> None:
        super().__init__(root_dir=str(settings.output_dir), virtual_mode=True)
        self._output_root: Path = self._cwd  # type: ignore[attr-defined]

    @property
    def cwd(self) -> Path:  # type: ignore[override]
        session_dir = _current_session_dir.get(None)
        if session_dir is not None:
            return Path(session_dir).resolve()
        return self._output_root

    @cwd.setter
    def cwd(self, value: Path) -> None:
        self._cwd = value  # type: ignore[attr-defined]


def create_ppt_agent(checkpointer, mode: str = "fast", session_context: str = ""):
    system_prompt = SYSTEM_PROMPT_FAST if mode == "fast" else SYSTEM_PROMPT
    if session_context:
        system_prompt = system_prompt + "\n\n" + session_context
    return create_deep_agent(
        model=get_model(),
        system_prompt=system_prompt,
        tools=list(ALL_TOOLS),
        checkpointer=checkpointer,
        backend=SessionFilesystemBackend(),
    )
