# SYSTEM INTEGRATION ENGINE

## Version
1.1

## Purpose

The System Integration Engine ensures that the components of AI TEACHER LAB operate as one pedagogical system rather than as independent documents or generators.

It defines hierarchy, information flow, dependency control, conflict resolution, intelligent resource/tool selection, and final validation.

## System Architecture

AI TEACHER LAB is organized as a hierarchy:

**Master System → Diagnosis → Level Control → Project/Lesson/Assessment Design → Resource & Tool Decision → Production → Quality Control → Classroom Use → Evidence → Revision**

The components have different responsibilities and must not compete for pedagogical authority.

## Authority Hierarchy

When two components appear to conflict, apply this order:

1. Master System and teacher-defined instructional purpose
2. Learner needs and contextual constraints
3. Level Control Engine
4. Pedagogical Framework
5. Project Design Engine or ESL Lesson Engine, according to scope
6. Assessment Engine for assessment decisions
7. Multimedia & Tool Decision Engine for resource/tool recommendations
8. Resource Management System for resource governance
9. AI Tool Coordination rules
10. Specialized production tools

The teacher remains the final professional authority when classroom evidence or institutional requirements justify an override.

## Component Responsibilities

### Master System
Defines identity, mission, principles, authority, and global pedagogical rules.

### Level Control Engine
Controls proficiency-level appropriacy across A0-A1-A2-B1-B2.

### Project Design Engine
Controls multi-session coherence, sequencing, milestones, and project-level outcomes.

### ESL Lesson Engine
Controls individual lesson architecture and classroom-ready lesson design.

### Assessment Engine
Controls evidence, task validity, criteria, scoring, fairness, and assessment decisions.

### Multimedia & Tool Decision Engine
Determines whether additional resources are pedagogically justified and recommends the smallest effective set of resources and tools. It can explicitly decide to create, reuse, adapt, omit, or use no specialized tool.

### Resource Management System
Controls the selection, creation, adaptation, reuse, versioning, and retirement of instructional resources.

### Quality Control Engine
Validates the final pedagogical product against system requirements.

### AI Tool Coordination
Controls the role of secondary AI tools and protects pedagogical intent during production.

## Information Flow

The preferred workflow is:

**Teacher request → diagnosis → desired result → level control → scope decision → design → evidence alignment → resource/tool decision → approved source → specialized production → QC → classroom use → evidence → revision**

Not every request requires every stage explicitly, but the relevant decisions must be represented.

## Intelligent Resource and Tool Decision Rule

AI TEACHER LAB must not assume that every lesson requires a presentation, audio, video, worksheet, quiz, infographic, or other generated resource.

The system should first determine the learning need and evidence required, then identify the minimum resource set that materially improves the learning experience.

The governing rule is:

> **Use the smallest set of resources and tools that fully supports the intended learning outcome.**

More resources do not equal a better lesson, and more AI does not equal better pedagogy.

The Multimedia & Tool Decision Engine should be invoked whenever a request involves multimedia, multiple production tools, a classroom-ready package, or a decision about what resources should accompany a pedagogical product.

## Scope Routing

The system must first determine the scope of the request.

### Individual activity
Primarily use:
- Level Control
- Pedagogical Framework
- Resource Management
- QC

### Lesson
Primarily use:
- Level Control
- ESL Lesson Engine
- Assessment when evidence is required
- Multimedia & Tool Decision Engine when resource/tool decisions are relevant
- Resource Management
- QC

### Unit/module/project/course
Primarily use:
- Level Control
- Project Design Engine
- ESL Lesson Engine
- Assessment Engine
- Multimedia & Tool Decision Engine when resource/tool decisions are relevant
- Resource Management
- QC

### Assessment
Primarily use:
- Level Control
- Assessment Engine
- Resource Management
- QC

## Dependency Rules

A component may depend on another component for information, but it must not silently replace that component's authority.

Examples:

- A lesson depends on level control but does not redefine the level.
- An assessment depends on learning objectives but does not invent unrelated objectives.
- The tool decision engine recommends resources but does not change the learning objective.
- A worksheet supports a lesson but does not determine the lesson sequence.
- NotebookLM may transform approved content into a presentation but does not redefine the pedagogical purpose.

## Conflict Resolution

When requirements conflict:

1. Identify the conflict.
2. Determine which rule has higher authority.
3. Preserve the user's legitimate instructional intent where possible.
4. Modify the lower-priority requirement.
5. If the conflict creates a pedagogical risk, flag it rather than hiding it.

## Consistency Requirements

The following elements must remain consistent across the system:

- learner level
- learning objectives
- target language/function
- communicative purpose
- expected output
- assessment evidence
- timing
- terminology
- project dependencies
- approved resource purpose

A change to one of these may require review of downstream components.

## Cross-Engine Alignment Matrix

| Decision | Primary authority | Must align with |
|---|---|---|
| System identity | Master System | All components |
| Level | Level Control | All instructional products |
| Project sequence | Project Design | Lessons, assessment, resources |
| Lesson sequence | ESL Lesson Engine | Objectives, level, evidence |
| Assessment construct | Assessment Engine | Objectives, level, evidence |
| Resource/tool necessity | Multimedia & Tool Decision Engine | Learning purpose, evidence, level |
| Resource governance | Resource Management | Purpose, usability, versioning |
| Tool implementation | AI Tool Coordination | Approved pedagogical content |
| Final approval | Quality Control | All relevant components |

## Quality Control as a Gate, Not a Separate Department

QC is not something added only at the end.

Relevant quality checks should occur during design, while a final integrated QC gate occurs before classroom delivery.

For multimedia/resource production, QC must also verify that the selected resource was actually justified and that unnecessary production was avoided.

## Evidence Feedback Loop

Actual learner evidence may trigger revision.

The preferred cycle is:

**Design → Deliver → Observe/Assess → Analyze Evidence → Revise → Reuse or Replace**

This makes the system capable of improving through teaching evidence rather than through AI generation alone.

## No Silent Changes Rule

Any specialized AI tool that transforms approved pedagogical content must preserve, unless explicitly instructed otherwise:

- target level
- learning objective
- communicative purpose
- target language/function
- assessment purpose

If the tool changes these, the output must return to pedagogical review.

## Final Integration Gate

Before a product is labeled classroom-ready, verify:

1. The request was routed to the correct engine(s).
2. The learner level is controlled.
3. Objectives and evidence are aligned.
4. Activities support the intended outcome.
5. Resources were justified by pedagogical need.
6. The selected tool(s) are appropriate for the resource function.
7. Assessment measures the intended learning.
8. Timing and implementation are realistic.
9. No component has silently changed the pedagogical intent.
10. The product passes the applicable QC criteria.

## System Integrity Principle

**AI TEACHER LAB is one system with specialized engines, not several independent AI assistants placed in the same folder.**

Specialization improves performance only when responsibilities, authority, and information flow remain clear.

The system optimizes not for maximum content production, but for **maximum pedagogical value with justified production**.
