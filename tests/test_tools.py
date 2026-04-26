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


# --- Outline validation tests ---


def test_outline_valid():
    from ppt_agent.agent.state import Outline

    outline = Outline.model_validate({
        "title": "Test",
        "slides": [
            {"page": 1, "layout": "cover", "title": "封面", "key_points": []},
            {"page": 2, "layout": "content", "title": "内容", "key_points": ["A", "B"]},
        ],
    })
    assert outline.title == "Test"
    assert len(outline.slides) == 2


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
            "slides": [{"page": 1, "layout": "invalid", "title": "X", "key_points": []}],
        })


def test_outline_missing_fields():
    from ppt_agent.agent.state import Outline

    with pytest.raises(ValidationError):
        Outline.model_validate({
            "title": "T",
            "slides": [{"page": 1}],
        })


def test_outline_key_points_default():
    from ppt_agent.agent.state import Outline

    outline = Outline.model_validate({
        "title": "T",
        "slides": [{"page": 1, "layout": "cover", "title": "X"}],
    })
    assert outline.slides[0].key_points == []


def test_session_state():
    from ppt_agent.agent.state import SessionState, PipelineStep
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        from pathlib import Path
        path = Path(tmpdir) / "session.json"

        state = SessionState()
        state.save(path)

        loaded = SessionState.load(path)
        assert loaded.step == PipelineStep.IDLE
