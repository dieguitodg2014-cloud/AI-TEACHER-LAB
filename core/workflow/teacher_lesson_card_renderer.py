"""Presentation-only renderer for TeacherLessonCard v4."""

from __future__ import annotations

from html import escape

from core.workflow.teacher_lesson_card import TeacherLessonCard


def render_teacher_lesson_card(card: TeacherLessonCard) -> str:
    """Render an immutable TeacherLessonCard as self-contained HTML.

    This function only reads the accepted card. It does not make pedagogical,
    provider, QC, resource, or acceptance decisions.
    """
    activities = "".join(
        "<li>"
        + (f"<div><strong>Stage:</strong> {escape(activity.stage)}</div>" if activity.stage else "")
        + f"<strong>{escape(activity.purpose)}</strong> "
        f"<span>{activity.minutes} min</span>"
        f"<div><strong>Interaction:</strong> {escape(activity.interaction)}</div>"
        f"<div><strong>Skill:</strong> {escape(activity.skill)}</div>"
        f"<div><strong>Cognitive demand:</strong> {escape(activity.cognitive_demand)}</div>"
        f"<div><strong>Scaffolding:</strong> {activity.scaffolding}/4</div>"
        + (
            f"<p><strong>Language target:</strong> {escape(activity.language_target)}</p>"
            if activity.language_target
            else ""
        )
        + (
            f"<p><strong>Teacher instructions:</strong> {escape(activity.instructions)}</p>"
            if activity.instructions
            else ""
        )
        + (
            f"<p><strong>Student production:</strong> {escape(activity.student_production)}</p>"
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

    execution = card.execution_content
    execution_sections = []
    if execution.teacher_explanation:
        execution_sections.append(f"<p><strong>Teacher explanation:</strong> {escape(execution.teacher_explanation)}</p>")
    if execution.target_language:
        execution_sections.append("<p><strong>Target language:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.target_language) + "</ul>")
    if execution.language_bank:
        execution_sections.append("<p><strong>Language bank:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.language_bank) + "</ul>")
    if execution.teacher_talk:
        execution_sections.append("<p><strong>Teacher talk:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.teacher_talk) + "</ul>")
    if execution.ccqs:
        execution_sections.append("<p><strong>CCQs:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.ccqs) + "</ul>")
    if execution.examples:
        execution_sections.append("<p><strong>Examples:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.examples) + "</ul>")
    if execution.common_errors:
        execution_sections.append("<p><strong>Common errors:</strong></p><pre>" + escape(str(dict(execution.common_errors))) + "</pre>")
    if execution.scaffolding:
        execution_sections.append("<p><strong>Scaffolding:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.scaffolding) + "</ul>")
    if execution.materials:
        execution_sections.append("<p><strong>Materials:</strong> " + escape(", ".join(execution.materials)) + "</p>")
    if execution.worksheet:
        execution_sections.append("<p><strong>Student worksheet:</strong></p><pre>" + escape(str(dict(execution.worksheet))) + "</pre>")
    if execution.role_cards:
        execution_sections.append("<p><strong>Role cards:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.role_cards) + "</ul>")
    if execution.answer_key:
        execution_sections.append("<p><strong>Answer key:</strong></p><pre>" + escape(str(dict(execution.answer_key))) + "</pre>")
    if execution.assessment_checklist:
        execution_sections.append("<p><strong>Assessment checklist:</strong></p><ul>" + "".join(f"<li>{escape(item)}</li>" for item in execution.assessment_checklist) + "</ul>")
    if execution.exit_ticket:
        execution_sections.append("<p><strong>Exit ticket:</strong></p><pre>" + escape(str(dict(execution.exit_ticket))) + "</pre>")
    execution_html = ""
    if execution_sections:
        execution_html = "<section><h2>Teacher execution support</h2>" + "".join(execution_sections) + "</section>"

    assessment = card.assessment
    context_html = (
        "<section><h2>Approved lesson context</h2>"
        f"<p><strong>Topic:</strong> {escape(card.topic or '')}</p>"
        f"<p><strong>Prior knowledge:</strong> {escape(', '.join(card.prior_knowledge))}</p>"
        f"<p><strong>Constraints:</strong> {escape(', '.join(card.constraints))}</p>"
        "</section>"
    )

    resource_html = ""
    if card.resource is not None:
        resource_html = (
            '<section class="resource"><h2>Resource</h2>'
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
{context_html}
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
{execution_html}
{resource_html}
</main>
</body>
</html>"""
