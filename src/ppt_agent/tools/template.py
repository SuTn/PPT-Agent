from langchain_core.tools import tool

from ppt_agent.config import get_session_dir
from ppt_agent.templates.registry import apply_template_to_session, list_all_templates


@tool
def list_templates() -> str:
    """列出所有可用的 PPT 模板。当用户想查看或选择模板风格时调用。"""
    templates = list_all_templates()
    if not templates:
        return "暂无可用模板。"
    lines = []
    for t in templates:
        lines.append(f"- {t['key']}: {t['name']} — {t['description']}")
    return "\n".join(lines)


@tool
def select_template(template_key: str) -> str:
    """选择一个模板风格。根据模板 key（如 simple_business）加载对应的 style_spec。

    Args:
        template_key: 模板目录名称，如 simple_business, tech_dark, education 等。
                      调用 list_templates 查看所有可用模板。
    """
    try:
        spec = apply_template_to_session(template_key, get_session_dir())
    except ValueError as e:
        return str(e)
    return f"已选择模板「{spec['name']}」，style_spec 已保存。"
