# Teacher Lesson Card v1

## Purpose

The Teacher Lesson Card is the stable presentation contract between the AI Teacher Lab workflow and any teacher-facing client (CLI, web UI, mobile UI, or future classroom application).

It presents pedagogical decisions already made by the workflow. It does not make new pedagogical decisions and must not expose internal orchestration objects as part of the teacher contract.

## Contract

The serialized `TeacherLessonResult` contains these top-level fields, in this order:

1. `status`
2. `title`
3. `level`
4. `audience`
5. `duration_minutes`
6. `objective`
7. `lesson`
8. `activities`
9. `assessment`
10. `resource`
11. `handoff`
12. `errors`

## Teacher view

A normal successful lesson should present:

- **Title** — the lesson topic or a useful lesson title.
- **Status** — the current workflow state.
- **Level** — approved learner level.
- **Audience** — intended learners.
- **Duration** — planned classroom time.
- **Learning objective** — the approved learning objective.
- **Lesson activities** — ordered classroom activities with purpose, interaction, timing, student production, and assessment connection when available.
- **Assessment** — assessment type, target, evidence, and success criteria.
- **Teacher notes** — notes returned by the generated lesson when available.
- **Resource** — resource decision metadata.
- **Accepted resource** — the exact produced resource only when it has crossed the resource acceptance boundary.
- **Next action** — actionable handoff information when production or revision requires teacher/provider action.
- **Issues** — workflow errors or blocking information.

## Resource safety rule

A teacher-facing client must never treat a proposed, failed, or revision-required resource as an accepted classroom resource.

The `resource.output` field is populated only when the workflow result is `ACCEPTED` and the generated result is a dictionary. The output is defensively copied before being exposed through the teacher contract.

This preserves the existing sequence:

`resource decision -> production -> validation/QC -> acceptance -> teacher output`

## Status behavior

### `PLANNED`

The pedagogical plan is usable, but no accepted resource or generated lesson output is available yet.

### `ACCEPTED`

The resource has crossed the acceptance boundary and may be presented as an accepted classroom resource.

### `READY`

A generated lesson is ready through the lesson-generation path. Resource acceptance remains governed by the resource pipeline when a resource is involved.

### `REVISION_REQUIRED`

The output is not ready for classroom use. The teacher-facing result should emphasize the next action rather than presenting the resource as accepted.

### `HUMAN_HANDOFF`

The workflow requires external/provider or human action. Internal provider details should remain outside the stable teacher contract except for actionable handoff information.

### `MISSING_CONTEXT` / `FAILED`

The teacher should see the missing information or issue in a readable form and should not receive a misleading impression that a complete lesson is ready.

## Presentation formats

The stable card can be consumed without changing the workflow. The current CLI exposes:

- `teacher-text` — concise classroom-readable text; default.
- `teacher` — stable teacher-facing JSON.
- `teacher-html` — dependency-free HTML generated from the UI-neutral Lesson Card.
- `internal` — orchestration output retained for diagnostics and development.

The HTML renderer is presentation-only and escapes teacher/request content before inserting it into the document. It does not perform pedagogical, provider, QC, or acceptance decisions.

## Design boundary

The Lesson Card is intentionally a projection layer:

`Teacher request -> existing workflow -> TeacherLessonResult -> client`

The client should not depend directly on `TaskPacket`, `ToolCandidate`, capability-validation records, provider revisions, regression guards, or other orchestration internals.

This keeps future UI work replaceable without changing the pedagogical and resource-control pipeline.
