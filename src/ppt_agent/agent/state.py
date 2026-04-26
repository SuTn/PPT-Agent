from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Outline schema (P2: structural validation)
# ---------------------------------------------------------------------------

class SlideItem(BaseModel):
    page: int = Field(ge=1)
    layout: Literal["cover", "toc", "content", "section", "ending"]
    title: str
    key_points: list[str] = Field(default_factory=list)

    @field_validator("key_points", mode="before")
    @classmethod
    def ensure_list(cls, v):
        return v if isinstance(v, list) else []


class Outline(BaseModel):
    title: str
    slides: list[SlideItem]

    @field_validator("slides")
    @classmethod
    def at_least_one_slide(cls, v):
        if not v:
            raise ValueError("slides 不能为空")
        return v


# ---------------------------------------------------------------------------
# Session state (P2: explicit file protocol)
# ---------------------------------------------------------------------------

class PipelineStep(str, Enum):
    IDLE = "idle"
    OUTLINE_DONE = "outline_done"
    TEMPLATE_DONE = "template_done"
    SLIDES_DONE = "slides_done"
    EXPORTED = "exported"


class SessionState(BaseModel):
    step: PipelineStep = PipelineStep.IDLE
    title: str = ""
    outline_file: str = ""
    style_spec_file: str = ""
    slides_dir: str = ""
    pptx_file: str = ""
    template_key: str = ""

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SessionState:
        if not path.exists():
            return cls()
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
