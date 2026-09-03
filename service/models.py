"""Typed HTTP request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class TriageRequest(BaseModel):
    patient_id: str = Field(pattern=r"^[A-Za-z0-9-]{3,40}$")
    symptoms: list[str] = Field(min_length=1, max_length=12)
    age_years: int = Field(ge=0, le=120)


class TriageResponse(BaseModel):
    patient_id: str
    urgency: Literal["emergency", "urgent", "routine"]
    guidance: str
    assessed_by: str
    trace_id: str


class AgentRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)


class AgentResponse(BaseModel):
    answer: str
    mode: Literal["offline", "online"]
    asked_by: str
    trace_id: str

