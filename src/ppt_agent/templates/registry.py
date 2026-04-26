import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


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
            templates.append({
                "name": spec["name"],
                "key": d.name,
                "description": spec.get("description", ""),
            })
    return templates
