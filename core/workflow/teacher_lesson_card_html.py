"""HTML presentation renderer for the stable Teacher Lesson Card contract.

This module is presentation-only. It consumes the UI-neutral card model and
never makes pedagogical, provider, QC, or acceptance decisions.
"""

from __future__ import annotations

from html import escape
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value))


def render_teacher_lesson_card_html(card: dict[str, Any]) -> str:
    """Render a Teacher Lesson Card as dependency-free, safe HTML."""
    header = card.get("header") or {}
    activities = card.get("activities") or []
    assessment = card.get("assessment")
    resource = card.get("resource")
    accepted = card.get("accepted_resource")
    errors = card.get("errors") or []

    activity_items = []
    for activity in activities:
        details = []
        if activity.get("minutes") is not None:
            details.append(f"<span>{_text(activity['minutes'])} min</span>")
        if activity.get("interaction"):
            details.append(f"<span>{_text(activity['interaction'])}</span>")
        activity_items.append(
            "<li>"
            f"<h3>{_text(activity.get('number'))}. {_text(activity.get('title'))}</h3>"
            f"<div class=\"meta\">{' · '.join(details)}</div>"
            f"<p><strong>Student production:</strong> {_text(activity.get('student_production'))}</p>"
            f"<p><strong>Assessment link:</strong> {_text(activity.get('assessment_link'))}</p>"
            "</li>"
        )

    accepted_html = ""
    if isinstance(accepted, dict):
        content = accepted.get("content")
        accepted_html = (
            "<section><h2>Accepted resource</h2>"
            f"<div class=\"resource\"><p><strong>Type:</strong> {_text(accepted.get('resource_type'))}</p>"
            f"<div>{_text(content)}</div></div></section>"
        )

    errors_html = "".join(f"<li>{_text(error)}</li>" for error in errors)
    errors_section = f"<section><h2>Issues</h2><ul>{errors_html}</ul></section>" if errors else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_text(header.get('title'))}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
header {{ border-bottom: 1px solid #ccc; padding-bottom: 1rem; }}
.meta {{ opacity: .75; font-size: .9rem; }}
section {{ margin-top: 1.5rem; }}
li {{ margin: .9rem 0; }}
.resource {{ border: 1px solid #ccc; padding: 1rem; border-radius: .5rem; }}
</style>
</head>
<body>
<header>
<h1>{_text(header.get('title'))}</h1>
<p><strong>Status:</strong> {_text(header.get('status'))}</p>
<p><strong>Level:</strong> {_text(header.get('level'))} · <strong>Audience:</strong> {_text(header.get('audience'))} · <strong>Duration:</strong> {_text(header.get('duration_minutes'))} min</p>
</header>
<section><h2>Learning objective</h2><p>{_text(card.get('objective'))}</p></section>
<section><h2>Lesson activities</h2><ol>{''.join(activity_items)}</ol></section>
<section><h2>Assessment</h2><pre>{_text(assessment)}</pre></section>
<section><h2>Teacher notes</h2><p>{_text(card.get('teacher_notes'))}</p></section>
<section><h2>Resource</h2><pre>{_text(resource)}</pre></section>
{accepted_html}
{errors_section}
</body>
</html>
"""
