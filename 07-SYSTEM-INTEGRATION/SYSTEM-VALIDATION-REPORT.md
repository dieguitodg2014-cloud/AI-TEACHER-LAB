# AI TEACHER LAB - SYSTEM VALIDATION REPORT

## Version
2.0

## Purpose

This document records the current validation state of AI TEACHER LAB, distinguishing the original structural/conversational validation from the new executable MVP runtime.

The objective is to verify that the repository is progressing as one coherent pedagogical system and that the executable vertical slice respects the defined authority, contracts, tool-selection rules, resource decisions, generation flow, and Quality Control gate.

## Validation Principle

The system must transform a teacher request through a consistent chain:

**Teacher Request -> Context -> Level Control -> Pedagogical Decision -> Resource Decision -> Task Packaging -> Tool Selection -> Generation or Human Handoff -> Validation -> Quality Control**

Classroom use remains downstream of the executable runtime. MVP-Next now includes an explicit post-lesson learner-state cycle: completed lesson -> observable evidence -> Course Memory -> bounded Adaptation.

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

A real local execution using the configured Gemma 3n E4B connector was attempted against LM Studio on the developer machine. The pedagogical pipeline reached the configured local lesson-generation provider with the expected A2 context, 90-minute duration, objective, approved topic, prior knowledge, and constraints, but the provider did not return a lesson within the configured 120-second timeout. The runtime result was `FAILED` with `EXECUTION_ERROR / PROVIDER_TIMEOUT` after one provider attempt.

A separate direct LM Studio smoke test confirmed that `127.0.0.1:1234` was reachable and that Gemma could answer small requests, while larger lesson-generation requests exceeded the current runtime timeout on the tested hardware/configuration. This is a manual environment limitation and is not treated as evidence that the repository CI path is broken.

The local runtime therefore remains an environment-specific manual validation target rather than a certified production execution path.

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
| Course Memory | IMPLEMENTED | Immutable course/session state with in-memory and durable JSON stores |
| Learning Evidence | IMPLEMENTED | Immutable observable evidence with in-memory and durable JSON stores |
| Adaptation | IMPLEMENTED | Deterministic bounded next-step recommendation; level and contract preserved |
| Learning-state integration | IMPLEMENTED | Explicit completion boundary connecting evidence, memory, and adaptation |
| Full external tool automation | PARTIAL | Human handoff supported; connector automation remains future work |
| Automated test execution / CI | CERTIFIED | Repository test suite certified through GitHub Actions |

## Important Validation Limitations

The Quality Control implementation now includes a deterministic weighted scoring layer over the approved QC evidence. The score covers learning validity, pedagogical alignment, level appropriacy, scaffolding alignment, language accuracy evidence, communicative value, practical feasibility, assessment alignment, and resource efficiency when an authoritative resource decision is available. Blocking validation remains authoritative: a weighted score never overrides a critical contract failure.

The repository contains unit and integration tests for the implemented components, and the MVP certification path has been executed successfully in GitHub Actions. The certification PR passed its CI check. Main-branch CI remains the authoritative post-merge verification for each merge.

The real local runtime has been validated manually. This is evidence of executable integration, not a substitute for a repeatable automated test suite.

## Final MVP Gate

The MVP is considered **FUNCTIONALLY INTEGRATED AND AUTOMATED-CI CERTIFIED**. The acceptance boundary is explicit: generation must pass Generation QC and the independent lesson validator before teacher-facing output can be produced.

The critical architecture-to-code path is implemented, the automated test suite has been certified in CI, and the weighted QC layer is now part of the generation QC result. The configured local runtime remains a separate manual environment check and is not treated as a substitute for CI.

No new architectural layer is required for the frozen MVP validation gate.

## Current Overall Status

**MVP CORE IMPLEMENTED - AUTOMATED CI CERTIFIED; WEIGHTED QC IMPLEMENTED; MVP-NEXT LEARNING STATE INTEGRATED**

The architecture should now be treated as frozen for the MVP. Further work should focus on execution, testing, bug fixing, and real classroom validation rather than adding new conceptual engines.

## MVP-Next Boundary

The MVP boundary is intentionally frozen at the accepted lesson-generation workflow. The following items describe the completed MVP-Next extensions and the remaining deferred scope:

1. **Course Memory** — completed in MVP-Next.
2. **Learning Evidence** — completed in MVP-Next.
3. **Adaptation** — completed in MVP-Next.
4. **Broader QC semantics** — richer linguistic and classroom-usability evaluation beyond the current deterministic weighted evidence model.
5. **Broader external-tool automation** — additional production connectors and operational fallback chains beyond the current configured runtime and human-handoff path.
6. **Broader automated certification scope** — additional runtime/environment-specific certification beyond the repository CI suite.

### MVP-Next rule

New work should enter one of these deferred tracks only when there is a concrete implementation requirement. Do not introduce new engines, abstractions, or provider-specific logic into the frozen MVP path merely to anticipate future features.

### Recommended order after MVP certification

**Automated test certification → Weighted QC → Course Memory → Learning Evidence → Adaptation → integrated MVP-Next validation → broader external-tool automation.**

This ordering preserves the existing acceptance boundary while adding learner-state capabilities only after the generation core is repeatably verified.
