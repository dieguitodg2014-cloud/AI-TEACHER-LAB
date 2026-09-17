"""Presentation-only renderer for TeacherLessonCard v1."""

from __future__ import annotations

from html import escape

from core.workflow.teacher_lesson_card import TeacherLessonCard


def render_teacher_lesson_card(card: TeacherLessonCard) -> str:
    """Render an immutable TeacherLessonCard as self-contained HTML.

    This function only reads the approved card. It does not make pedagogical,
    provider, QC, resource, or acceptance decisions.
    """
    activities = "".join(
        "<li>"
        f"<strong>{escape(activity.purpose)}</strong> "
        f"<span>{activity.minutes} min</span>"
        f"<div>{escape(activity.interaction)}</div>"
        + (
            f"<p>{escape(activity.student_production)}</p>"
            if activity.student_production
            else ""
        )
        + (
            f"<p><em>Assessment:</em> {escape(activity.assessment_link)}</p>"
            if activity.assessment_link
            else ""
        )
        + "</li>"
        for activity in card.activities
    )

    assessment = card.assessment
    resource_html = ""
    if card.resource is not None:
        resource_html = (
            "<section class=\"resource\"><h2>Resource</h2>"
            f"<p><strong>{escape(str(card.resource.get('required_output', '')))}</strong></p>"
            f"<p>{escape(str(card.resource.get('purpose', '')))}</p>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(card.objective)}</title>
</head>
<body>
<main>
<header>
<h1>{escape(card.objective)}</h1>
<p><strong>{escape(card.level)}</strong> · {escape(card.audience)} · {card.duration_minutes} min</p>
</header>
<section>
<h2>Lesson sequence</h2>
<ol>{activities}</ol>
</section>
<section>
<h2>Assessment</h2>
<p><strong>{escape(str(assessment.get('type', '')))}</strong></p>
<p>{escape(str(assessment.get('target', '')))}</p>
<p>{escape(str(assessment.get('evidence', '')))}</p>
</section>
{resource_html}
</main>
</body>
</html>"""
