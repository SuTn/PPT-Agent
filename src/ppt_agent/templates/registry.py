import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent
SKELETONS_DIR = TEMPLATES_DIR / "skeletons"


def load_template(name: str) -> dict:
    spec_path = TEMPLATES_DIR / name / "style_spec.json"
    if not spec_path.exists():
        raise ValueError(f"模板 '{name}' 不存在: {spec_path}")
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_all_templates() -> list[dict]:
    templates = []
    for d in sorted(TEMPLATES_DIR.iterdir()):
        if d.is_dir() and (d / "style_spec.json").exists():
            spec = load_template(d.name)
            colors = spec.get("colors", {})
            templates.append({
                "name": spec["name"],
                "key": d.name,
                "description": spec.get("description", ""),
                "colors": {
                    "primary": colors.get("primary", "#4f46e5"),
                    "secondary": colors.get("secondary", "#818cf8"),
                    "accent": colors.get("accent", "#f59e0b"),
                    "background": colors.get("background", "#ffffff"),
                },
            })
    return templates


def load_skeleton(layout: str, template_name: str = "") -> str:
    """Load skeleton HTML for a layout type.

    Looks for template-specific skeleton first, then falls back to shared skeletons.
    """
    # Template-specific skeleton
    if template_name:
        specific = TEMPLATES_DIR / template_name / "skeletons" / f"{layout}.html"
        if specific.exists():
            return specific.read_text(encoding="utf-8")

    # Shared skeleton
    shared = SKELETONS_DIR / f"{layout}.html"
    if shared.exists():
        return shared.read_text(encoding="utf-8")

    raise ValueError(f"Skeleton not found for layout '{layout}'")


def render_skeleton(
    skeleton_html: str,
    style_spec: dict,
    headline: str,
    page: int,
    total: int,
    content: str,
    speaker_notes: str = "",
) -> str:
    """Fill a skeleton with style_spec values and slide content.

    Replaces {{var}} placeholders with style_spec values, and {var} placeholders
    with slide data.
    """
    colors = style_spec.get("colors", {})
    typo = style_spec.get("typography", {})
    layout_spec = style_spec.get("layout", {})

    style_map = {
        "primary": colors.get("primary", "#1a365d"),
        "secondary": colors.get("secondary", "#2b6cb0"),
        "accent": colors.get("accent", "#ed8936"),
        "accent_2": colors.get("accent_2", colors.get("accent", "#ed8936")),
        "background": colors.get("background", "#ffffff"),
        "card_bg": colors.get("card_bg", colors.get("background", "#ffffff")),
        "text_color": colors.get("text", "#2d3748"),
        "text_light": colors.get("text_light", "#718096"),
        "border_color": colors.get("border", "#e2e8f0"),
        "title_font": typo.get("title_font", "'Microsoft YaHei', sans-serif"),
        "body_font": typo.get("body_font", typo.get("title_font", "'Microsoft YaHei', sans-serif")),
        "title_size": typo.get("title_size", "44px"),
        "subtitle_size": typo.get("subtitle_size", "28px"),
        "body_size": typo.get("body_size", "20px"),
        "small_size": typo.get("small_size", "16px"),
        "line_height": typo.get("line_height", "1.6"),
        "title_bar_height": layout_spec.get("title_bar_height", "6px"),
    }

    html = skeleton_html

    # Replace {{var}} style placeholders first (CSS variables from style_spec)
    for key, value in style_map.items():
        html = html.replace("{{" + key + "}}", value)

    # Replace {var} data placeholders
    html = html.replace("{headline}", headline)
    html = html.replace("{page}", str(page))
    html = html.replace("{total}", str(total))
    html = html.replace("{content}", content)

    notes_html = ""
    if speaker_notes:
        notes_html = f"\n<!-- speaker_notes: {speaker_notes} -->"
    html = html.replace("{speaker_notes}", notes_html)

    return html
