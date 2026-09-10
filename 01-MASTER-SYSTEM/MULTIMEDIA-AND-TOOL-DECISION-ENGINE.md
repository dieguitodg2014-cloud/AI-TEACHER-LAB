# Multimedia & Tool Decision Engine

**Version:** 1.0

## Purpose

The Multimedia & Tool Decision Engine determines whether additional resources or AI-generated multimedia are pedagogically necessary and, when they are necessary, which available tool is most appropriate.

AI TEACHER LAB must not generate resources merely because a tool can generate them.

The engine exists to optimize pedagogical value, teacher usability, learner experience, time, and tool use.

## Governing Principle

> **Do not create a resource unless it serves a clear pedagogical purpose.**

Technology is selected after the learning need has been identified.

**Pedagogical purpose -> learner need -> evidence required -> learning experience -> resource need -> tool selection -> production -> QC**

## Decision Authority

The Pedagogical Director remains the final decision-maker for pedagogical resource selection.

The decision engine may recommend:

- a resource should be created;
- a resource should not be created;
- an existing resource should be reused;
- a resource should be adapted;
- a specific AI tool should be used;
- no external AI tool is necessary.

Specialized tools cannot override the pedagogical decision.

## Mandatory Decision Questions

Before requesting production from any specialized tool, determine:

1. What is the learning problem?
2. What must learners be able to do?
3. What evidence is required?
4. What learning experience is necessary to reach that evidence?
5. Does a resource materially improve that learning experience?
6. Could the teacher or students accomplish the same purpose more simply without a new resource?
7. Should an existing resource be reused or adapted?
8. If a new resource is justified, which tool is best suited to produce it?
9. What constraints must the tool preserve?
10. How will the finished resource be evaluated through QC?

## Resource Decision Categories

### CREATE

Create a new resource when it provides clear additional pedagogical value and cannot be adequately replaced by an existing resource or simpler classroom procedure.

### REUSE

Reuse an existing resource when it already meets the learning objective, level, context, and usability requirements.

### ADAPT

Adapt an existing resource when its core value is appropriate but its level, context, language, format, or learner profile requires modification.

### OMIT

Do not create a resource when it adds little or no pedagogical value, duplicates another resource, increases cognitive or classroom load unnecessarily, or exists primarily for visual novelty.

## Tool Selection Logic

Tool selection follows function, not popularity.

### NotebookLM

Preferred for source-based classroom multimedia when its current capabilities match the need, especially:

- classroom presentations;
- audiovisual transformations;
- audio resources;
- video or audiovisual learning resources;
- study materials;
- coherent transformations of an approved pedagogical source.

### Canva

Preferred when precise visual design or specialized graphic production provides clear value, including:

- infographics;
- flashcards;
- classroom cards;
- posters;
- visual organizers;
- graphic adaptations;
- designs requiring specific visual control.

### Gemini or other multimodal tools

May be selected when a particular multimodal or creative production requirement is better served by that tool, provided the approved pedagogical intent remains unchanged.

### Local Bionic / local models

May be selected for offline, privacy-sensitive, emergency, or local-support scenarios when feasible. Output remains subject to full QC.

### No Tool

The engine must be able to select no specialized tool when direct teacher use of the approved lesson materials is the best solution.

## Tool Selection Criteria

When more than one tool could produce a suitable resource, compare:

1. pedagogical fit;
2. source fidelity;
3. level fidelity;
4. language control;
5. interaction support;
6. classroom usability;
7. production effort;
8. teacher editing burden;
9. multimodal value;
10. reliability and current availability.

Pedagogical fit has priority over visual quality, novelty, speed, and quantity.

## Resource Value Test

A proposed resource should answer:

> **What can learners do better, understand more clearly, practice more effectively, or demonstrate more authentically because this resource exists?**

If no meaningful answer can be given, the resource should normally be omitted.

## Resource Necessity Matrix

| Resource | Possible purpose | Create only when |
|---|---|---|
| Presentation | Organize input, modeling, instructions, interaction | Visual sequencing or projection materially improves the lesson |
| Audio | Listening input, model language, pronunciation, interaction | Listening or auditory modeling serves the objective |
| Video | Context, demonstration, authentic interaction | Movement, context, demonstration, or audiovisual input adds value |
| Worksheet | Controlled/guided practice, recording, evidence | Written support or evidence is pedagogically justified |
| Quiz | Recognition/checking understanding | Quick assessment evidence is needed |
| Flashcards | Retrieval, visual recognition, rapid interaction | Visual/retrieval practice is useful |
| Infographic | Organization of complex or visual information | A visual relationship is substantially clearer than prose |
| Study guide | Consolidation and independent review | Learners need structured review or reference material |
| Role-play cards | Reduce cognitive load while supporting interaction | Scaffolding is needed for communicative production |

## Level Control Integration

Resource decisions must respect the target level.

A0 may justify stronger visual and auditory support because learners have limited linguistic resources and cannot depend on untaught language.

A1 may use structured visual and language support for basic functional communication.

A2 may use multimedia to support routine independent communication and connected language.

B1 should prioritize resources that support sustained communication, explanation, narration, opinions, and interaction.

B2 should prioritize resources that support nuance, argumentation, evaluation, inference, register, and flexible communication when relevant.

A higher level does not automatically justify more resources.

## Avoiding Resource Overproduction

The engine must actively detect:

- duplicate resources;
- decorative multimedia;
- excessive slide production;
- redundant quizzes;
- worksheets that repeat the presentation without adding practice;
- videos that do not contribute to the objective;
- unnecessary tool switching;
- resources that increase teacher workload without increasing learning value.

## Decision Output

For each lesson, unit, assessment, or project, the engine should be capable of producing a concise resource decision report:

**Learning need:**

**Required evidence:**

**Resources justified:**

**Resources omitted:**

**Resources reused:**

**Resources adapted:**

**Recommended tool for each justified resource:**

**Reason for each tool choice:**

**Constraints to preserve:**

**QC gates required:**

## Integration With Other Engines

The decision engine depends on:

- Master System for authority;
- Level Control for learner-level requirements;
- ESL Lesson Engine for lesson structure and instructional intent;
- Assessment Engine for evidence requirements;
- Project Design Engine for larger learning architecture;
- Resource Management System for reuse, adaptation, status, and governance;
- AI Tool Coordination for specialized tool roles;
- Quality Control for final validation.

## Final Decision Rule

The system should prefer the **smallest set of resources and tools that fully supports the intended learning outcome**.

More resources do not equal a better lesson.

More AI does not equal better pedagogy.

The goal is not maximum production.

The goal is **maximum pedagogical value with justified production**.
