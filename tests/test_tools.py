"""Smoke tests for non-LLM components."""

import pytest
from pydantic import ValidationError


def test_template_registry():
    from ppt_agent.templates.registry import list_all_templates, load_template

    templates = list_all_templates()
    assert len(templates) == 5

    for t in templates:
        spec = load_template(t["key"])
        assert "name" in spec
        assert "colors" in spec
        assert "typography" in spec
        assert "component_styles" in spec


def test_list_templates_tool():
    from ppt_agent.tools.template import list_templates

    result = list_templates.invoke({})
    assert "simple_business" in result
    assert len(result) > 100


def test_select_template_tool():
    from ppt_agent.tools.template import select_template

    result = select_template.invoke({"template_key": "simple_business"})
    assert "简约商务" in result


def test_select_template_invalid():
    from ppt_agent.tools.template import select_template

    result = select_template.invoke({"template_key": "nonexistent"})
    assert "不存在" in result


def test_config():
    from ppt_agent.config import settings

    assert settings.model
    assert str(settings.output_dir).endswith("output")


def test_renderer_import():
    from ppt_agent.export.renderer import render_html_to_png
    assert callable(render_html_to_png)


def test_pptx_builder():
    from pathlib import Path
    from ppt_agent.export.pptx_builder import build_pptx
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_pptx = Path(tmpdir) / "test.pptx"
        build_pptx([], dummy_pptx)
        assert dummy_pptx.exists()


# --- New model validation tests ---


def test_evidence_model():
    from ppt_agent.agent.state import Evidence

    ev = Evidence(claim="CAGR 36.8%", evidence_type="data", detail="Growth rate", source="Gartner")
    assert ev.claim == "CAGR 36.8%"
    assert ev.evidence_type == "data"
    assert ev.source == "Gartner"

    with pytest.raises(ValidationError):
        Evidence(claim="test", evidence_type="invalid_type")


def test_supporting_point_model():
    from ppt_agent.agent.state import SupportingPoint, Evidence

    sp = SupportingPoint(
        message="Market is growing fast",
        evidence=[
            Evidence(claim="CAGR 36.8%", evidence_type="data"),
            Evidence(claim="OpenAI case study", evidence_type="case_study"),
        ],
    )
    assert sp.message == "Market is growing fast"
    assert len(sp.evidence) == 2

    sp_empty = SupportingPoint(message="Simple point")
    assert sp_empty.evidence == []


def test_narrative_framework_scqa():
    from ppt_agent.agent.state import NarrativeFramework

    nf = NarrativeFramework(
        framework="scqa",
        situation="AI market is growing",
        complication="Competition intensifies",
        core_question="How to compete?",
        core_answer="Invest in differentiation",
    )
    assert nf.framework == "scqa"
    assert nf.situation == "AI market is growing"


def test_narrative_framework_custom():
    from ppt_agent.agent.state import NarrativeFramework

    nf = NarrativeFramework(framework="chronological")
    assert nf.framework == "chronological"

    nf2 = NarrativeFramework()
    assert nf2.framework == "scqa"  # default


def test_outline_valid():
    from ppt_agent.agent.state import Outline

    outline = Outline.model_validate({
        "title": "AI Market Overview",
        "audience": "executives",
        "objective": "persuade",
        "narrative": {
            "framework": "scqa",
            "situation": "AI market growing",
            "complication": "Competition rising",
            "core_question": "How to compete?",
            "core_answer": "Differentiate",
        },
        "slides": [
            {"page": 1, "layout": "cover", "headline": "AI Market Overview 2025"},
            {"page": 2, "layout": "content", "headline": "Market reached $184B", "supporting_points": []},
        ],
    })
    assert outline.title == "AI Market Overview"
    assert outline.audience == "executives"
    assert outline.objective == "persuade"
    assert outline.narrative.framework == "scqa"
    assert len(outline.slides) == 2
    assert outline.slides[1].headline == "Market reached $184B"


def test_outline_with_supporting_points():
    from ppt_agent.agent.state import Outline

    outline = Outline.model_validate({
        "title": "Deep Dive",
        "slides": [
            {
                "page": 1,
                "layout": "content",
                "headline": "AI market tripled in 3 years",
                "body_text": "Strong momentum across all segments.",
                "supporting_points": [
                    {
                        "message": "Market size tripled",
                        "evidence": [
                            {"claim": "CAGR 36.8%", "evidence_type": "data", "source": "Gartner"},
                            {"claim": "OpenAI revenue doubled", "evidence_type": "case_study"},
                        ],
                    },
                    {"message": "Enterprise adoption is accelerating", "evidence": []},
                ],
                "speaker_notes": "Key slide for the narrative.",
                "section": "situation",
            },
        ],
    })
    slide = outline.slides[0]
    assert slide.headline == "AI market tripled in 3 years"
    assert slide.body_text == "Strong momentum across all segments."
    assert len(slide.supporting_points) == 2
    assert slide.supporting_points[0].evidence[0].evidence_type == "data"
    assert slide.speaker_notes == "Key slide for the narrative."
    assert slide.section == "situation"


def test_outline_defaults():
    from ppt_agent.agent.state import Outline

    outline = Outline.model_validate({
        "title": "Simple",
        "slides": [{"page": 1, "layout": "cover", "headline": "Hello"}],
    })
    assert outline.audience == ""
    assert outline.objective == "report"
    assert outline.narrative.framework == "scqa"
    assert outline.slides[0].supporting_points == []
    assert outline.slides[0].body_text == ""
    assert outline.slides[0].speaker_notes == ""
    assert outline.slides[0].section == ""


def test_outline_missing_title():
    from ppt_agent.agent.state import Outline

    with pytest.raises(ValidationError):
        Outline.model_validate({"slides": []})


def test_outline_empty_slides():
    from ppt_agent.agent.state import Outline

    with pytest.raises(ValidationError, match="不能为空"):
        Outline.model_validate({"title": "T", "slides": []})


def test_outline_invalid_layout():
    from ppt_agent.agent.state import Outline

    with pytest.raises(ValidationError):
        Outline.model_validate({
            "title": "T",
            "slides": [{"page": 1, "layout": "invalid", "headline": "X"}],
        })


def test_outline_missing_headline():
    from ppt_agent.agent.state import Outline

    with pytest.raises(ValidationError):
        Outline.model_validate({
            "title": "T",
            "slides": [{"page": 1, "layout": "content"}],
        })


def test_outline_objective_values():
    from ppt_agent.agent.state import Outline

    for obj in ["persuade", "report", "educate", "inspire"]:
        o = Outline.model_validate({"title": "T", "slides": [{"page": 1, "layout": "cover", "headline": "X"}], "objective": obj})
        assert o.objective == obj

    with pytest.raises(ValidationError):
        Outline.model_validate({"title": "T", "slides": [{"page": 1, "layout": "cover", "headline": "X"}], "objective": "invalid"})


# --- Session state tests ---


def test_session_state():
    from ppt_agent.agent.state import SessionState, PipelineStep
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        from pathlib import Path
        path = Path(tmpdir) / "session.json"

        state = SessionState(session_id="abc12345")
        state.save(path)

        loaded = SessionState.load(path)
        assert loaded.step == PipelineStep.IDLE
        assert loaded.session_id == "abc12345"
        assert loaded.research_file == ""


def test_session_state_research_step():
    from ppt_agent.agent.state import SessionState, PipelineStep
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        from pathlib import Path
        path = Path(tmpdir) / "session.json"

        state = SessionState(session_id="test123", step=PipelineStep.RESEARCH_DONE, research_file="/some/path/research_notes.md")
        state.save(path)

        loaded = SessionState.load(path)
        assert loaded.step == PipelineStep.RESEARCH_DONE
        assert loaded.research_file == "/some/path/research_notes.md"


def test_session_index():
    from ppt_agent.agent.state import SessionIndex, SessionEntry, PipelineStep
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        from pathlib import Path
        index_path = Path(tmpdir) / "index.json"
        index = SessionIndex(index_path)

        index.add(SessionEntry(session_id="s1", title="PPT 1", created_at="2026-01-01"))
        index.add(SessionEntry(session_id="s2", title="PPT 2", created_at="2026-01-02"))

        entries = index.list_all()
        assert len(entries) == 2
        assert entries[0].session_id == "s2"  # newest first (insert at 0)

        index.update("s1", title="Updated PPT 1", step=PipelineStep.EXPORTED)
        entries = index.list_all()
        updated = [e for e in entries if e.session_id == "s1"][0]
        assert updated.title == "Updated PPT 1"
        assert updated.step == PipelineStep.EXPORTED


# --- Upload & parse tests ---


def test_upload_nonexistent_file():
    from ppt_agent.tools.upload import upload_and_parse

    result = upload_and_parse.invoke({"file_path": "/nonexistent/file.txt"})
    assert "不存在" in result


def test_upload_empty_file(tmp_path):
    from ppt_agent.tools.upload import upload_and_parse

    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    result = upload_and_parse.invoke({"file_path": str(empty_file)})
    assert "为空" in result


def test_upload_text_file(tmp_path):
    import os
    from ppt_agent.tools.upload import upload_and_parse, MAX_FILE_SIZE

    # Test file size limit
    big_file = tmp_path / "big.txt"
    big_file.write_bytes(b"x" * (MAX_FILE_SIZE + 1))
    result = upload_and_parse.invoke({"file_path": str(big_file)})
    assert "过大" in result

    # Test normal text file
    text_file = tmp_path / "notes.txt"
    text_file.write_text("This is some test content for the PPT.\nKey point: AI is growing fast.", encoding="utf-8")
    result = upload_and_parse.invoke({"file_path": str(text_file)})
    assert "已解析" in result
    assert "notes.txt" in result


def test_upload_append_multiple(tmp_path):
    from ppt_agent.tools.upload import upload_and_parse

    file1 = tmp_path / "doc1.txt"
    file1.write_text("Content from document one.", encoding="utf-8")
    result1 = upload_and_parse.invoke({"file_path": str(file1)})
    assert "已解析" in result1

    file2 = tmp_path / "doc2.txt"
    file2.write_text("Content from document two.", encoding="utf-8")
    result2 = upload_and_parse.invoke({"file_path": str(file2)})
    assert "已解析" in result2
    assert "doc2.txt" in result2

    # Verify materials.md contains both
    materials = tmp_path.glob("**/materials.md")
    for m in materials:
        content = m.read_text(encoding="utf-8")
        assert "document one" in content
        assert "document two" in content
        break


# --- Prompt helper tests ---


def test_materials_section_empty():
    from ppt_agent.prompts.outline import _materials_section

    assert _materials_section("") == ""
    assert _materials_section("   ") == ""


def test_materials_section_with_content():
    from ppt_agent.prompts.outline import _materials_section

    result = _materials_section("Some reference material here.")
    assert "参考材料" in result
    assert "Some reference material here." in result


def test_research_section_empty():
    from ppt_agent.prompts.outline import _research_section

    assert _research_section("") == ""
    assert _research_section("   ") == ""


def test_research_section_with_content():
    from ppt_agent.prompts.outline import _research_section

    result = _research_section("Key finding: market is growing.")
    assert "研究笔记" in result
    assert "Key finding: market is growing." in result


# --- Research tool tests (mock LLM) ---


def test_research_tool_saves_notes(tmp_path, monkeypatch):
    """Verify research tool writes research_notes.md and updates state."""
    import asyncio
    from pathlib import Path
    from ppt_agent.tools.research import research_topic
    from ppt_agent.agent.state import SessionState, PipelineStep
    from ppt_agent import config

    # Set session dir
    session_dir = tmp_path / "test_session"
    session_dir.mkdir()
    config._current_session_dir.set(session_dir)

    # Create initial session state
    state = SessionState(session_id="test")
    state.save(session_dir / "session.json")

    # Mock the LLM model
    class MockResponse:
        def __init__(self, content):
            self.content = content

    class MockModel:
        async def ainvoke(self, messages, **kwargs):
            # Step 1 (analyze) → Step 2 (per dimension) → Step 3 (synthesize)
            if isinstance(messages, list) and len(messages) == 1:
                text = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
                if "分析" in text or "维度" in text:
                    return MockResponse('{"analysis_summary": "Test analysis", "dimensions": [{"name": "Test", "focus": "Focus", "questions": ["Q1"]}]}')
                elif "综合" in text or "研究报告" in text:
                    return MockResponse("# 研究笔记：Test\n\n## 分析摘要\nTest summary\n")
            return MockResponse("## Test Dimension\n### 核心发现\n- Finding 1\n")

    monkeypatch.setattr("ppt_agent.tools.research.get_model", lambda: MockModel())

    result = asyncio.get_event_loop().run_until_complete(
        research_topic.coroutine(topic="AI Market", requirements="executive summary")
    )

    assert "研究完成" in result
    assert (session_dir / "research_notes.md").exists()

    loaded_state = SessionState.load(session_dir / "session.json")
    assert loaded_state.step == PipelineStep.RESEARCH_DONE
    assert loaded_state.research_file != ""


def test_pipeline_step_order():
    """Verify RESEARCH_DONE comes before OUTLINE_DONE."""
    from ppt_agent.agent.state import PipelineStep

    steps = list(PipelineStep)
    assert steps.index(PipelineStep.RESEARCH_DONE) < steps.index(PipelineStep.OUTLINE_DONE)
    assert steps.index(PipelineStep.IDLE) < steps.index(PipelineStep.RESEARCH_DONE)
