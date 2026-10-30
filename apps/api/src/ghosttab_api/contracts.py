from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TaskInput(ClosedModel):
    title: str = Field(min_length=1, max_length=200)
    goal: str = Field(min_length=1, max_length=2000)


class EvidenceInput(ClosedModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=12000)
    url: str = Field(default="", max_length=2000)

    @field_validator("url")
    @classmethod
    def safe_link(cls, value):
        if value and not value.startswith("https://"):
            raise ValueError("Source links must start with https://")
        return value


class Citation(ClosedModel):
    evidence_id: str
    quote: str = Field(min_length=1, max_length=1500)


class GroundedPoint(ClosedModel):
    text: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(min_length=1, max_length=8)


class PreparedBrief(ClosedModel):
    summary: GroundedPoint
    facts: list[GroundedPoint] = Field(max_length=12)
    next_steps: list[GroundedPoint] = Field(max_length=8)
    unknowns: list[str] = Field(max_length=12)
    draft: str = Field(max_length=6000)


class DraftInput(ClosedModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    draft: str = Field(max_length=6000)
    expected_draft: str = Field(max_length=6000)


class LifecycleInput(ClosedModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    action: Literal["review", "complete", "reopen"]
    expected_generation: int = Field(ge=1)
    expected_completed_at: float | None
    snapshot_id: str | None = Field(default=None, max_length=36)
    expected_draft: str | None = Field(default=None, max_length=6000)


class EventInput(ClosedModel):
    event_id: str = Field(min_length=1, max_length=1024, pattern=r"^[a-zA-Z0-9_@.-]+$")
