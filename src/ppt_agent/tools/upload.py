import os
from pathlib import Path

from langchain_core.tools import tool
from markitdown import MarkItDown

from ppt_agent.config import get_session_dir

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@tool
def upload_and_parse(file_path: str) -> str:
    """解析用户上传的文件，将内容提取为 Markdown 并保存到当前会话的 materials.md。

    支持的文件格式：.docx, .xlsx, .pptx, .pdf, .html, .csv, .json, .xml, .txt, 图片等。
    文件大小限制 20MB。

    Args:
        file_path: 上传文件的本地路径。
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return f"文件不存在: {file_path}"

    size = os.path.getsize(path)
    if size > MAX_FILE_SIZE:
        return f"文件过大（{size / 1024 / 1024:.1f}MB），限制 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"

    try:
        md = MarkItDown()
        result = md.convert(str(path))
        content = result.text_content
    except Exception as e:
        return f"文件解析失败: {e}"

    if not content or not content.strip():
        return f"文件内容为空: {path.name}"

    materials_path = get_session_dir() / "materials.md"
    materials_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to existing materials with separator
    if materials_path.exists():
        existing = materials_path.read_text(encoding="utf-8")
        content = existing + f"\n\n---\n\n# 来源: {path.name}\n\n" + content
    else:
        content = f"# 上传材料\n\n## 来源: {path.name}\n\n" + content

    materials_path.write_text(content, encoding="utf-8")

    preview = content[:300].replace("\n", " ")
    return f"已解析: {path.name}（{size / 1024:.1f}KB）\n内容预览: {preview}..."
