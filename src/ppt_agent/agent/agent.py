from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from ppt_agent.agent.prompts import SYSTEM_PROMPT
from ppt_agent.config import settings
from ppt_agent.llm import get_model
from ppt_agent.tools.outline import generate_outline
from ppt_agent.tools.slide_gen import generate_slides
from ppt_agent.tools.template import list_templates, select_template
from ppt_agent.tools.export import export_pptx
from ppt_agent.tools.upload import upload_and_parse


def create_ppt_agent(checkpointer):
    return create_deep_agent(
        model=get_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            generate_outline,
            select_template,
            list_templates,
            generate_slides,
            export_pptx,
            upload_and_parse,
        ],
        checkpointer=checkpointer,
        backend=FilesystemBackend(root_dir=str(settings.output_dir)),
    )
