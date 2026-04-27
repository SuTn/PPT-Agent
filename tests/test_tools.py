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


def test_outline_rich_keypoints():
    from ppt_agent.agent.state import Outline, KeyPoint

    outline = Outline.model_validate({
        "title": "Rich",
        "slides": [
            {
                "page": 1,
                "layout": "content",
                "title": "核心数据",
                "key_points": [
                    {
                        "text": "市场规模达到 1000 亿",
                        "emphasis": "high",
                        "sub_points": ["同比增长 30%", "连续三年高增长"],
                    },
                    {"text": "补充说明", "emphasis": "low"},
                ],
            },
        ],
    })
    kp = outline.slides[0].key_points[0]
    assert isinstance(kp, KeyPoint)
    assert kp.text == "市场规模达到 1000 亿"
    assert kp.emphasis == "high"
    assert len(kp.sub_points) == 2
    assert outline.slides[0].key_points[1].emphasis == "low"


def test_outline_string_keypoints_compat():
    from ppt_agent.agent.state import Outline, KeyPoint

    outline = Outline.model_validate({
        "title": "Compat",
        "slides": [
            {"page": 1, "layout": "content", "title": "内容", "key_points": ["简单要点"]},
        ],
    })
    kp = outline.slides[0].key_points[0]
    assert isinstance(kp, KeyPoint)
    assert kp.text == "简单要点"
    assert kp.sub_points == []
    assert kp.emphasis == "medium"


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

        state = SessionState(session_id="abc12345")
        state.save(path)

        loaded = SessionState.load(path)
        assert loaded.step == PipelineStep.IDLE
        assert loaded.session_id == "abc12345"


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
    # The session dir may vary, find it
    for m in materials:
        content = m.read_text(encoding="utf-8")
        assert "document one" in content
        assert "document two" in content
        break


def test_materials_section_empty():
    from ppt_agent.prompts.outline import _materials_section

    result = _materials_section("")
    assert result == ""

    result = _materials_section("   ")
    assert result == ""


def test_materials_section_with_content():
    from ppt_agent.prompts.outline import _materials_section

    result = _materials_section("Some reference material here.")
    assert "参考材料" in result
    assert "Some reference material here." in result
