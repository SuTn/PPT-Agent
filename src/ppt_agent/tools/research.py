import asyncio
import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from ppt_agent.agent.state import PipelineStep, SessionState, sync_session_index
from ppt_agent.config import get_session_dir, settings
from ppt_agent.llm import get_model
from ppt_agent.prompts.research import (
    RESEARCH_ANALYZE_PROMPT,
    RESEARCH_DIMENSION_PROMPT,
    RESEARCH_SYNTHESIZE_PROMPT,
    _audience_section,
    _objective_section,
    _research_materials_section,
    _research_requirements_section,
    _search_results_section,
    _time_section,
)
from ppt_agent.search import get_search_provider, cleanup_browser_threads

_MAX_RETRIES = 3


def _extract_json(text: str) -> str:
    """Extract JSON from LLM output — fenced block or balanced braces."""
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return m.group(1)

    first = text.find("{")
    if first == -1:
        return text.strip()

    depth = 0
    in_str = False
    esc = False
    for i in range(first, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"' and not esc:
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[first : i + 1]
    return text.strip()


def _try_parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


async def _read_materials(session_dir: Path) -> str:
    path = session_dir / "materials.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


async def _step1_analyze(
    topic: str, requirements: str, materials: str, audience: str, objective: str, model
) -> list[dict]:
    """Analyze topic and identify research dimensions."""
    prompt = RESEARCH_ANALYZE_PROMPT.format(
        topic=topic,
        requirements_section=_research_requirements_section(requirements),
        audience_section=_audience_section(audience),
        objective_section=_objective_section(objective),
        materials_section=_research_materials_section(materials),
    )

    messages = [HumanMessage(content=prompt)]
    hint = "你上一次输出的不是合法的 JSON。请严格输出纯 JSON，不要包含注释、尾逗号或其他文本。"

    for attempt in range(_MAX_RETRIES):
        result = await model.ainvoke(messages)
        raw = _extract_json(result.content)
        parsed = _try_parse_json(raw)
        if parsed and "dimensions" in parsed:
            return parsed["dimensions"]
        messages.append(result)
        messages.append(HumanMessage(content=f"{hint}\n\n请重试。"))

    # Fallback: use default dimensions
    return [
        {"name": "核心概念", "focus": "主题的核心定义和基本原理", "search_queries": [f"{topic} 核心概念 定义", f"{topic} 基本原理 关键组成"]},
        {"name": "现状与数据", "focus": "当前的行业现状和关键数据", "search_queries": [f"{topic} 行业数据 最新趋势", f"{topic} 市场规模 增长率"]},
        {"name": "挑战与机遇", "focus": "面临的主要挑战和发展机遇", "search_queries": [f"{topic} 挑战 难点", f"{topic} 发展机遇 前景"]},
        {"name": "案例与实践", "focus": "典型案例和实践经验", "search_queries": [f"{topic} 成功案例 最佳实践", f"{topic} 实施经验 教训"]},
    ]


async def _step2_research_dimension(
    sem: asyncio.Semaphore,
    topic: str,
    requirements: str,
    materials: str,
    dim: dict,
    model,
    audience: str = "",
) -> str:
    """Research a single dimension, optionally with web search."""
    async with sem:
        # Web search for this dimension (if configured)
        search_results = []
        search_provider = get_search_provider()
        if search_provider:
            # Use pre-generated search queries, or fall back to topic + focus
            queries = dim.get("search_queries", [])
            if not queries:
                queries = [f"{topic} {dim.get('focus', '')}"]
            query = queries[0]
            try:
                search_results = await search_provider.search(query, max_results=5)
            except Exception:
                pass

        audience_value_hint = "这个维度的核心发现如何帮助说服/教育/打动观众"
        if audience:
            audience_value_hint = f"这个维度的核心发现如何帮助打动「{audience}」，他们最关心什么"

        prompt = RESEARCH_DIMENSION_PROMPT.format(
            topic=topic,
            requirements_section=_research_requirements_section(requirements),
            audience_section=_audience_section(audience),
            dimension_name=dim.get("name", ""),
            dimension_focus=dim.get("focus", ""),
            materials_section=_research_materials_section(materials),
            search_section=_search_results_section(search_results),
            audience_value_hint=audience_value_hint,
            time_section=_time_section(),
        )
        result = await model.ainvoke([HumanMessage(content=prompt)])
        return result.content


async def _step3_synthesize(
    topic: str,
    materials: str,
    dimension_research: str,
    model,
    audience: str = "",
    objective: str = "",
) -> str:
    """Synthesize all dimension research into final research_notes.md."""
    prompt = RESEARCH_SYNTHESIZE_PROMPT.format(
        topic=topic,
        audience_section=_audience_section(audience),
        objective_section=_objective_section(objective),
        dimension_research=dimension_research,
        materials_section=_research_materials_section(materials),
        time_section=_time_section(),
    )
    result = await model.ainvoke([HumanMessage(content=prompt)])
    return result.content


@tool
async def research_topic(topic: str, requirements: str = "", audience: str = "", objective: str = "") -> str:
    """深度研究演示文稿主题，生成结构化研究笔记。适用于复杂或专业领域的主题。

    Args:
        topic: 演示文稿主题。
        requirements: 用户补充需求（关注点、特殊要求等）。
        audience: 目标受众（如：企业高管、技术团队、客户等）。
        objective: 演示目标（persuade/report/educate/inspire）。
    """
    session_dir = get_session_dir()
    model = get_model()
    sem = asyncio.Semaphore(settings.research_concurrency)

    materials = await _read_materials(session_dir)

    # Step 1: analyze topic → dimensions
    dimensions = await _step1_analyze(topic, requirements, materials, audience, objective, model)

    # Step 2: research each dimension concurrently
    tasks = [
        _step2_research_dimension(sem, topic, requirements, materials, dim, model, audience)
        for dim in dimensions
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    dimension_research_parts = []
    failed = []
    for dim, result in zip(dimensions, results):
        if isinstance(result, Exception):
            failed.append(f"{dim.get('name', '?')}: {result}")
        else:
            dimension_research_parts.append(
                f"## {dim.get('name', '')}\n\n{result}"
            )

    if not dimension_research_parts:
        return f"研究失败：所有维度的研究均出错。\n" + "\n".join(failed)

    dimension_research = "\n\n".join(dimension_research_parts)

    # Step 3: synthesize into final research_notes.md
    research_notes = await _step3_synthesize(topic, materials, dimension_research, model, audience, objective)

    # Persist
    notes_path = session_dir / "research_notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(research_notes, encoding="utf-8")

    # Update session state
    state_path = session_dir / "session.json"
    state = SessionState.load(state_path)
    state.step = PipelineStep.RESEARCH_DONE
    state.research_file = str(notes_path)
    state.save(state_path)
    sync_session_index(state.session_id, step=state.step.value)

    dim_names = "、".join(d.get("name", "?") for d in dimensions)
    summary = f"研究完成，共 {len(dimensions)} 个维度：{dim_names}"
    if failed:
        summary += f"\n警告：{len(failed)} 个维度研究失败：\n" + "\n".join(failed)

    # Include a preview so the agent can present findings to the user
    preview = research_notes[:800] if len(research_notes) > 800 else research_notes
    result = f"{summary}\n\n研究笔记摘要：\n{preview}"

    cleanup_browser_threads()
    return result
