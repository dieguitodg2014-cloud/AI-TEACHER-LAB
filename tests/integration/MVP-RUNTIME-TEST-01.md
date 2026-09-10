# MVP Runtime Test 01

## Purpose

Verify the first executable vertical slice for the A2 Present Perfect Golden Case.

## Golden Case

- Level: A2
- Audience: adult ESL learners
- Duration: 90 minutes
- Objective: Discuss past experiences and ask follow-up questions.
- Prior knowledge: Past Simple
- Constraint: Students struggle with question formation.

## Expected flow

REQUEST → CONTEXT → LEVEL CONTROL → PEDAGOGICAL DECISION → TOOL SELECTION → GENERATION → VALIDATION/QC → APPROVAL

## Verification status

The repository contains integration coverage for:

1. Successful generation and QC approval.
2. Failed first generation followed by successful revision.
3. Persistent generation failure bounded by three attempts.
4. Capability-based tool selection.
5. Human handoff when a generator is unavailable.
6. Planning-only execution when generation dependencies are absent.

## Important limitation

These tests have been written into the repository but have not been executed by a CI workflow or runtime environment in this audit. Therefore this document records test coverage, not a claim that the tests passed.

## MVP boundary

The current implementation is sufficient to validate the core decision-and-generation workflow with injected tools/generators. Real provider connectors, production model execution, richer QC, and operational fallback chains belong to the next integration stage.
