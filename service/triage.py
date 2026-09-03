"""Deterministic decision support for the demonstration triage route."""

from __future__ import annotations

from service.models import TriageRequest

EMERGENCY_TERMS = {"chest pain", "difficulty breathing", "unconscious", "severe bleeding"}
URGENT_TERMS = {"high fever", "dehydration", "persistent vomiting", "severe pain"}


def assess_triage(request: TriageRequest) -> tuple[str, str]:
    symptoms = {symptom.strip().lower() for symptom in request.symptoms}
    if symptoms & EMERGENCY_TERMS:
        return "emergency", "Seek emergency care immediately; do not wait for an online response."
    if symptoms & URGENT_TERMS or request.age_years < 1:
        return "urgent", "Arrange an in-person clinical assessment today."
    return "routine", "Arrange routine clinical review and monitor for worsening symptoms."

