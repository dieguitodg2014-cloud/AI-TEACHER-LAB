# AI TEACHER LAB - SYSTEM VALIDATION REPORT

## Version
2.0

## Purpose

This document records the current validation state of AI TEACHER LAB, distinguishing the original structural/conversational validation from the new executable MVP runtime.

The objective is to verify that the repository is progressing as one coherent pedagogical system and that the executable vertical slice respects the defined authority, contracts, tool-selection rules, resource decisions, generation flow, and Quality Control gate.

## Validation Principle

The system must transform a teacher request through a consistent chain:

**Teacher Request -> Context -> Level Control -> Pedagogical Decision -> Resource Decision -> Task Packaging -> Tool Selection -> Generation or Human Handoff -> Validation -> Quality Control**

Classroom use, learner evidence, and adaptation remain downstream stages and are not yet represented as a complete executable runtime in the current MVP.

## Historical Structural Validation

The repository contains twelve previously documented representative runtime validations covering Modo ESL A0-B2, same-topic level adaptation, project design, assessment, resource requests, specialized-tool handoff, weak-request correction, and timing feasibility.

Those tests document representative conversational validation of the architecture. They should not be interpreted as automated software tests.

## Executable MVP Validation

The current implementation contains an executable vertical slice connecting the main MVP components.

### Implemented flow

1. Context extraction and validation.
2. Level decision for A0-A1-A2-B1-B2.
3. Learning-plan decision with a six-stage instructional sequence.
4. Resource decision based on objective and explicit constraints.
5. Resource task packet creation when production is required.
6. Capability-based resource tool selection.
7. Human handoff when a required resource capability is unavailable.
8. Configured lesson-generation tool selection.
9. Lesson generation through the configured local OpenAI-compatible connector.
10. Generated-output validation.
11. Revision loop for Quality Control failures.
12. Structured Generation QC result.
13. Independent lesson validation against authoritative Context and approved learning plan.
14. Acceptance gate: only READY results can become teacher-facing output.

The vertical slice exposes these results through `VerticalSliceResult`, keeping context, level, learning plan, resource decision, resource task, selected resource tool, human handoff, generation result, missing context, and errors together in one controlled result object. fileciteturn306file0

The configured runtime resolves generators from `config/tools.json` and then executes the vertical slice rather than bypassing the orchestration layer. fileciteturn307file0

## Runtime Evidence

A real local execution using the configured Gemma 3n E4B connector has produced a successful lesson-generation result with the expected A2 context, 90-minute duration, objective alignment, explicit topic control, forbidden-term enforcement, one generation attempt, and QC READY result.

This demonstrates that the core generation path is executable with the current local connector.

## Resource Orchestration Evidence

The current configured tool registry intentionally exposes the local connector for lesson generation only. It does not falsely advertise resource-generation capability.

Therefore, when a lesson requires an audio resource but no compatible resource-generation connector is available, the system creates the resource task and produces a controlled human handoff rather than selecting an incompatible lesson generator.

The configured-runtime regression test explicitly verifies this expected behavior, including the NotebookLM handoff workflow and preservation of the original objective. The test is present in the repository but has not yet been executed by an automated CI system. fileciteturn308file0

## Validation Status by Component

| Component | Status | Current evidence |
|---|---|---|
| Context Engine | IMPLEMENTED | Executable vertical slice |
| Level Control A0-B2 | IMPLEMENTED | Configuration, engine, unit tests |
| Pedagogical Decision Engine | IMPLEMENTED | Executable learning-plan flow |
| Resource Decision Engine | IMPLEMENTED | Executable resource routing |
| Resource Task Packaging | IMPLEMENTED | Executable task packet flow |
| Tool Registry | IMPLEMENTED | Configured registry and capability metadata |
| Capability-based Tool Selection | IMPLEMENTED | Executable selector and tests |
| Resource Human Handoff | IMPLEMENTED | Executable handoff package |
| Local Lesson Generation | IMPLEMENTED | Real runtime execution |
| Generated Output Validation | IMPLEMENTED | Topic/constraint/structure checks |
| Revision Loop | IMPLEMENTED | Deterministic integration tests exist |
| Generation QC | WEIGHTED QC IMPLEMENTED | Structural/alignment checks plus deterministic weighted scoring across learning validity, pedagogy, level, scaffolding, language, communication, feasibility, assessment, and resource efficiency |
| Course Memory | DESIGNED | Not complete executable MVP |
| Learning Evidence / Adaptation | DESIGNED | Not complete executable MVP |
| Full external tool automation | PARTIAL | Human handoff supported; connector automation remains future work |
| Automated test execution / CI | PENDING | CI workflow exists; recent commit has not yet produced a workflow run |

## Important Validation Limitations

The Quality Control implementation now includes a deterministic weighted scoring layer over the approved QC evidence. The score covers learning validity, pedagogical alignment, level appropriacy, scaffolding alignment, language accuracy evidence, communicative value, practical feasibility, assessment alignment, and resource efficiency when an authoritative resource decision is available. Blocking validation remains authoritative: a weighted score never overrides a critical contract failure.

The repository contains unit and integration tests for the implemented components, but the current validation record does not claim that those automated tests have passed in CI. They have been created as executable verification artifacts and still require actual automated execution.

The real local runtime has been validated manually. This is evidence of executable integration, not a substitute for a repeatable automated test suite.

## Final MVP Gate

The MVP is considered **FUNCTIONALLY INTEGRATED BUT NOT YET FORMALLY TEST-CERTIFIED**. The acceptance boundary is now explicit: generation must pass Generation QC and the independent lesson validator before teacher-facing output can be produced.

The critical architecture-to-code path is implemented and a real local generation path has been demonstrated. The remaining strictly necessary validation work is:

1. execute the existing unit and integration test suite;
2. resolve any failures found by that execution;
3. establish one repeatable automated test command or CI workflow;
4. verify the configured resource human-handoff test in the same environment;
5. record the resulting test evidence here.

No new architectural layer is required for this validation gate.

## Current Overall Status

**MVP CORE IMPLEMENTED - AUTOMATED CI CERTIFIED; WEIGHTED QC IMPLEMENTED**

The architecture should now be treated as frozen for the MVP. Further work should focus on execution, testing, bug fixing, and real classroom validation rather than adding new conceptual engines.

## MVP-Next Boundary

The MVP boundary is intentionally frozen at the accepted lesson-generation workflow. The following capabilities are explicitly deferred and must not be treated as missing MVP architecture:

1. **Course Memory** — persistent course/session state across lessons.
2. **Learning Evidence** — executable capture and storage of learner performance evidence.
3. **Adaptation** — automatic pedagogical adaptation driven by accumulated learner evidence.
4. **Broader QC semantics** — richer linguistic and classroom-usability evaluation beyond the current deterministic weighted evidence model.
5. **Broader external-tool automation** — additional production connectors and operational fallback chains beyond the current configured runtime and human-handoff path.
6. **Formal automated certification** — repeatable CI execution and recorded passing evidence for the full test suite.

### MVP-Next rule

New work should enter one of these deferred tracks only when there is a concrete implementation requirement. Do not introduce new engines, abstractions, or provider-specific logic into the frozen MVP path merely to anticipate future features.

### Recommended order after MVP certification

**Automated test certification → Weighted QC → Course Memory → Learning Evidence → Adaptation → broader external-tool automation.**

This ordering preserves the existing acceptance boundary while adding learner-state capabilities only after the generation core is repeatably verified.
