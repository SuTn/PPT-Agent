from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from ppt_agent.agent.prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_FAST
from ppt_agent.config import settings
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

def create_ppt_agent(checkpointer, mode: str = "fast"):
    system_prompt = SYSTEM_PROMPT_FAST if mode == "fast" else SYSTEM_PROMPT
    return create_deep_agent(
        model=get_model(),
        system_prompt=system_prompt,
        tools=list(ALL_TOOLS),
        checkpointer=checkpointer,
        backend=FilesystemBackend(root_dir=str(settings.output_dir)),
    )
