from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Outline schema (P2: structural validation)
# ---------------------------------------------------------------------------

class KeyPoint(BaseModel):
    text: str
    sub_points: list[str] = Field(default_factory=list)
    emphasis: Literal["high", "medium", "low"] = "medium"

    @field_validator("sub_points", mode="before")
    @classmethod
    def ensure_list(cls, v):
        return v if isinstance(v, list) else []

    @field_validator("text", mode="before")
    @classmethod
    def allow_string(cls, v):
        return v if isinstance(v, str) else str(v)


class SlideItem(BaseModel):
    page: int = Field(ge=1)
    layout: Literal["cover", "toc", "content", "section", "ending"]
    title: str
    key_points: list[KeyPoint] = Field(default_factory=list)

    @field_validator("key_points", mode="before")
    @classmethod
    def coerce_keypoints(cls, v):
        if not isinstance(v, list):
            return []
        coerced = []
        for item in v:
            if isinstance(item, str):
                coerced.append(KeyPoint(text=item))
            elif isinstance(item, dict):
                coerced.append(KeyPoint.model_validate(item))
        return coerced


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
    session_id: str = ""
    step: PipelineStep = PipelineStep.IDLE
    title: str = ""
    outline_file: str = ""
    style_spec_file: str = ""
    slides_dir: str = ""
    pptx_file: str = ""
    template_key: str = ""
    created_at: str = ""

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SessionState:
        if not path.exists():
            return cls()
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return cls()


class SessionEntry(BaseModel):
    session_id: str
    title: str = ""
    step: PipelineStep = PipelineStep.IDLE
    template_key: str = ""
    created_at: str = ""


class SessionIndex:
    """Manages the list of all PPT sessions (output/index.json)."""

    def __init__(self, index_path: Path):
        self._path = index_path

    def _read(self) -> list[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _write(self, entries: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, entry: SessionEntry) -> None:
        entries = self._read()
        entries.insert(0, entry.model_dump())
        self._write(entries)

    def update(self, session_id: str, **fields) -> None:
        entries = self._read()
        for e in entries:
            if e["session_id"] == session_id:
                e.update(fields)
                break
        self._write(entries)

    def list_all(self) -> list[SessionEntry]:
        return [SessionEntry.model_validate(e) for e in self._read()]
