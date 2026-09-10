# PILOT 05 - INTELLIGENT TOOL SELECTION

**Version:** 1.0  
**Status:** Test specification

## Purpose

PILOT 05 tests whether AI TEACHER LAB can independently determine which instructional resources should be created, reused, adapted, or omitted, and which tool should produce each justified resource.

The teacher does not prescribe the production tool.

The system must reason from pedagogical purpose first.

## Core Test Question

> Can AI TEACHER LAB select the smallest set of resources and tools that fully supports the intended learning outcome?

## Test Principle

The pilot must not reward maximum production.

A decision to omit a resource or use no specialized tool can be a successful result when pedagogically justified.

## Test Cases

### TEST 05-A - A0 Classroom Objects

**Need:** true beginners need to identify and say basic classroom objects and respond to simple teacher prompts.

**Expected reasoning:** strong visual and auditory support may be justified; unnecessary written complexity should be avoided.

### TEST 05-B - A1 Daily Routines

**Need:** learners describe basic daily routines using familiar language and short connected utterances.

**Expected reasoning:** visual sequencing and structured speaking support may be useful; multimedia should remain simple and level-appropriate.

### TEST 05-C - A2 Making Arrangements

**Need:** learners make suggestions, respond to suggestions, and reach an agreement about a plan.

**Expected reasoning:** a presentation may support sequencing and language input; role-play or speaking support may be more valuable than a separate quiz; audio/video should be justified by function.

### TEST 05-D - B1 Present Perfect / Experiences

**Need:** learners sustain interaction about experiences, ask follow-up questions, and explain or elaborate on personal experiences.

**Expected reasoning:** resources should support sustained speaking, meaningful input, and interaction rather than isolated grammar recognition.

### TEST 05-E - B2 Debate / Social Media and Society

**Need:** learners evaluate ideas, express and support positions, respond to opposing views, and use appropriate register and nuance.

**Expected reasoning:** authentic or source-based input, discussion/debate frameworks, evidence prompts, and assessment criteria may be more valuable than basic vocabulary materials or recognition quizzes.

## Required Decision Output

For every test case, the system must report:

**Learning need:**  
**Required evidence:**  
**Resources justified:**  
**Resources omitted:**  
**Resources reused:**  
**Resources adapted:**  
**Recommended tool for each justified resource:**  
**Reason for each tool choice:**  
**Why simpler production is insufficient, if applicable:**  
**Constraints to preserve:**  
**QC gates required:**  

## Decision Categories

Every proposed resource must receive one of:

- CREATE
- REUSE
- ADAPT
- OMIT

Tool selection must also allow:

- NotebookLM
- Canva
- Gemini or another appropriate multimodal tool
- Local Bionic/local model
- No specialized tool

## Evaluation Criteria

### G13 - Pedagogical Necessity

The selected resource responds to a genuine learning need.

### G14 - Minimal Effective Production

The system avoids unnecessary resources and selects the smallest effective resource set.

### G15 - Tool-Function Fit

The selected tool is appropriate for the actual production function.

### G16 - Level Fit

Resource and tool decisions respect A0-A1-A2-B1-B2 requirements.

### G17 - Teacher Usability

The decision does not create unnecessary teacher workload.

### G18 - Production Coherence

Resources produced from the same lesson remain aligned with the approved pedagogical source.

## Pass Conditions

PILOT 05 passes only if the system demonstrates all of the following:

1. It does not automatically generate every possible resource.
2. It can justify omission.
3. It can select no specialized tool when appropriate.
4. It distinguishes resource necessity from tool availability.
5. It changes resource decisions appropriately across proficiency levels and pedagogical purposes.
6. It selects tools according to function rather than popularity or novelty.
7. It preserves the approved learning objective and evidence.
8. It identifies unnecessary production or redundant resources.
9. It produces decisions that are realistic for classroom use.
10. All selected outputs remain subject to QC.

## Important Validation Rule

A visually impressive or technologically complex solution must not receive a higher evaluation merely because it uses more AI.

The best decision may be a simple worksheet, an existing resource, a teacher-led procedure, or no additional resource at all.

## Pilot Outcome

**Status:** Pending runtime validation.

The pilot should be executed after the decision engine is integrated into the runtime workflow. Results should be recorded separately for each test case, followed by an overall PASS / NEEDS REVISION decision.
