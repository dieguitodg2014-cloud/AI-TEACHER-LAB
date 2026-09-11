# AI TEACHER LAB

AI TEACHER LAB is an integrated pedagogical and AI-assisted system for designing, reviewing, improving, organizing, and delivering classroom-ready ESL/EFL instruction.

## System principle

AI TEACHER LAB is not a repository of random activities or disconnected lesson plans. It is a coherent pedagogical system. Every instructional product must be aligned with learning outcomes, learner level, communicative purpose, assessment evidence, resources, and practical classroom constraints.

## Core architecture

- `01-MASTER-SYSTEM/` - system identity, pedagogical direction, framework, quality control, and AI tool coordination.
- `02-LEVEL-CONTROL/` - level adaptation from A0 through B2.
- `03-ESL-ENGINE/` - lesson design and MODO ESL rules.
- `04-ASSESSMENT/` - assessment design and alignment.
- `05-PROJECTS/` - course, unit, module, camp, workshop, and multi-session project design.
- `06-RESOURCES/` - selection, creation, adaptation, reuse, versioning, and quality control of instructional resources.
- `07-SYSTEM-INTEGRATION/` - coordination, authority, information flow, dependencies, and cross-engine integrity.

## Governing sequence

**Teacher request -> diagnosis -> learning purpose -> level control -> scope routing -> design -> evidence/assessment -> resource selection or creation -> specialized production -> quality control -> classroom use -> learner evidence -> revision**

## Authority principle

The system uses specialized engines, but pedagogical authority remains centralized. The Master System and teacher-defined instructional purpose govern the system. Specialized engines solve specific problems within that framework.

## Quality principle

No material is considered finished merely because it is grammatically correct or visually attractive. It must also be pedagogically valid, level-appropriate, communicative, feasible, usable, and aligned with its intended learning outcome.

## Integration principle

**AI TEACHER LAB is one system with specialized engines, not several independent AI assistants placed in the same folder.**

Secondary AI tools may accelerate research, production, visualization, audio, presentation, formatting, or offline support, but they must not silently change the approved pedagogical intent.

## Local runtime

The repository includes an executable runtime path for real lesson generation. The current configured runtime uses an OpenAI-compatible local connector, which can connect to LM Studio without storing provider credentials in the repository.

### LM Studio configuration

Start LM Studio, load the intended local model, and start its OpenAI-compatible server. The default endpoint expected by AI TEACHER LAB is:

`http://127.0.0.1:1234/v1/chat/completions`

The model name can be supplied through the environment variable `AI_TEACHER_LAB_PROVIDER_MODEL`. The endpoint can be overridden with `AI_TEACHER_LAB_PROVIDER_URL`. An API key is optional and can be supplied with `AI_TEACHER_LAB_PROVIDER_API_KEY` when the local server requires one.

Example for the local Gemma setup:

```bash
export AI_TEACHER_LAB_PROVIDER_URL="http://127.0.0.1:1234/v1/chat/completions"
export AI_TEACHER_LAB_PROVIDER_MODEL="google/gemma-3n-e4b"
```

### Run a lesson request

From the repository root:

```bash
python run_lesson.py --request "Create a 90-minute A2 ESL lesson for adults about the present perfect. Students should talk about their life experiences."
```

The CLI sends the request through the existing runtime rather than bypassing the pedagogical engines. The runtime resolves the configured generator, applies the approved learning and assessment decisions, requests the lesson artifact, and returns the serialized result as JSON.

For a structured request:

```bash
python run_lesson.py --level A2 --audience "adult ESL learners" --duration 90 --objective "Students will talk about their life experiences using the present perfect." --topic "Present Perfect"
```

A non-READY result exits with a non-zero status so that runtime failures are visible to scripts and future interfaces.

## Provider governance

The configuration records provider roles separately from executable connectors. ChatGPT remains the pedagogical authority, Gemini the secondary provider, NotebookLM a specialized source-based resource creator, and the local Gemma runtime a fallback/backup provider. The repository does not pretend that unavailable external production connectors exist.

## Current status

The core system architecture is established through seven integrated layers, with an executable request-to-generation runtime now available for local provider testing. Further development should prioritize real end-to-end execution, provider reliability, and classroom use before adding unnecessary complexity.
