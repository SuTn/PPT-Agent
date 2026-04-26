"""Smoke tests for non-LLM components."""


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
        # create a dummy 1x1 PNG
        from pptx import Presentation
        dummy_pptx = Path(tmpdir) / "test.pptx"
        # just test that build_pptx can be called with empty list
        build_pptx([], dummy_pptx)
        assert dummy_pptx.exists()
