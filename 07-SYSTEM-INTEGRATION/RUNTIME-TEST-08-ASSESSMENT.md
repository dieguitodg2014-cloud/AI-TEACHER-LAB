# RUNTIME TEST 08 - ASSESSMENT

## Purpose

Validate that AI TEACHER LAB designs assessment from learning objectives and evidence rather than generating disconnected questions or activities.

## Test Input

`Diseña una evaluación oral B1 sobre experiencias y viajes. Quiero que dure 10 minutos y que permita saber si los estudiantes pueden hablar de experiencias, hacer preguntas de seguimiento y explicar por qué una experiencia fue importante.`

## Expected System Behavior

The system should activate the Assessment Engine and establish:

**Learning Objective → Evidence → Task → Criteria → Feedback → Decision**

The assessment should:

- measure the stated communicative outcomes;
- be appropriate for B1;
- require sustained but manageable oral communication;
- include follow-up interaction;
- avoid reducing performance to isolated grammar questions;
- define observable criteria;
- provide useful feedback and a decision rule.

## Controlled Runtime Result

The assessment was designed as a 10-minute paired performance.

### Task

Student A describes a meaningful travel or life experience and explains why it was important. Student B listens and asks natural follow-up questions. Students then exchange roles. The teacher may use one additional prompt if the interaction needs support.

### Evidence

The task provides direct evidence of whether learners can:

1. narrate an experience with connected language;
2. explain significance or consequences;
3. ask and answer follow-up questions;
4. maintain interaction;
5. use appropriate B1 language with sufficient control for communication.

### Criteria

The rubric uses observable performance criteria:

- **Task achievement:** communicates the required experience and significance.
- **Coherence:** ideas are connected and understandable.
- **Fluency:** maintains communication with manageable hesitation.
- **Range and control:** uses appropriate B1 language with generally effective grammatical control.
- **Interaction:** responds to questions and contributes follow-up questions appropriately.

Grammar is evaluated as part of communicative performance rather than as an isolated score detached from the task.

### Feedback

Feedback begins with demonstrated strengths, followed by one or two high-value priorities for improvement. The teacher records evidence during performance without unnecessarily interrupting the learner.

### Decision

Performance evidence is used to determine whether the learner has demonstrated the target communicative outcomes or needs targeted additional practice and reassessment.

## B1 Level Validation

**PASS**

The assessment requires connected speech, explanation, personal narration, follow-up interaction, and functional independence. It is qualitatively more demanding than a simple A2 information exchange while remaining realistic for B1.

## Quality Gates

### G1 - Level

**PASS**

The task and criteria reflect B1 communicative expectations.

### G2 - Alignment

**PASS**

The assessment directly measures the objectives stated in the request.

### G3 - Language

**PASS**

Language criteria are appropriate and do not turn the assessment into a grammar-only test.

### G4 - Communication

**PASS**

Learners must communicate meaningfully and respond to another speaker.

### G5 - Feasibility

**PASS**

A 10-minute paired assessment is realistic with clear instructions and concise scoring criteria.

## Final Result

**STATUS: PASS**

The controlled runtime test confirms that the Assessment Engine begins with intended learning and evidence, then constructs the task, criteria, feedback, and decision rather than simply generating questions.

## Validation Note

This is a controlled conversational runtime simulation through the AI TEACHER LAB workflow. It is not an automated software integration test.
