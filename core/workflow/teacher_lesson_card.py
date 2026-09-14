"""Presentation adapter for the stable Teacher Lesson Card contract.

This module is intentionally presentation-only. It consumes the teacher-facing
contract and produces a UI-neutral card model; it does not make pedagogical,
provider, QC, or acceptance decisions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.workflow.teacher_interface import TeacherLessonResult, teacher_result_to_dict


def build_teacher_lesson_card(result: TeacherLessonResult) -> dict[str, Any]:
    """Build a web-friendly, UI-neutral representation of a lesson card."""
    payload = teacher_result_to_dict(result)
    activities = [
        {
            "number": index,
            "title": activity.get("purpose") or activity.get("name") or "Activity",
            "minutes": activity.get("minutes"),
            "interaction": activity.get("interaction"),
            "student_production": activity.get("student_production"),
            "assessment_link": activity.get("assessment_link"),
        }
        for index, activity in enumerate(payload["activities"], start=1)
    ]

    resource = payload["resource"]
    accepted_resource = None
    if payload["status"] == "ACCEPTED" and isinstance(resource, dict):
        output = resource.get("output")
        if isinstance(output, dict):
            accepted_resource = deepcopy(output)

    return {
        "header": {
            "title": payload["title"],
            "status": payload["status"],
            "level": payload["level"],
            "audience": payload["audience"],
            "duration_minutes": payload["duration_minutes"],
        },
        "objective": payload["objective"],
        "activities": activities,
        "assessment": deepcopy(payload["assessment"]),
        "teacher_notes": (
            payload["lesson"].get("teacher_notes")
            if isinstance(payload["lesson"], dict)
            else None
        ),
        "resource": {
            "action": resource.get("action"),
            "type": resource.get("type"),
            "purpose": resource.get("purpose"),
            "required": resource.get("required"),
        } if isinstance(resource, dict) else None,
        "accepted_resource": accepted_resource,
        "handoff": deepcopy(payload["handoff"]),
        "errors": list(payload["errors"]),
    }
