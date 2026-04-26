from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from ppt_agent.agent.prompts import SYSTEM_PROMPT
from ppt_agent.agent.subagents import slide_generator
from ppt_agent.config import settings
from ppt_agent.llm import get_model
from ppt_agent.tools.outline import generate_outline
from ppt_agent.tools.template import list_templates, select_template
from ppt_agent.tools.export import export_pptx


def create_ppt_agent():
    return create_deep_agent(
        model=get_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            generate_outline,
            select_template,
            list_templates,
            export_pptx,
        ],
        subagents=[slide_generator],
        checkpointer=MemorySaver(),
        backend=FilesystemBackend(root_dir=str(settings.output_dir)),
    )
