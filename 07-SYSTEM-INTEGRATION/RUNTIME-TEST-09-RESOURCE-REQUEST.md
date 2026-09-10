# RUNTIME TEST 09 - RESOURCE REQUEST

## Purpose

Validate that AI TEACHER LAB treats classroom resources as pedagogical support and applies Resource Management, Level Control, lesson alignment, and Quality Control before delivering a classroom-ready resource.

## Test Input

`Modo ESL A0: necesito una worksheet de 30 minutos para practicar daily routines. Quiero que los estudiantes practiquen I wake up, I get up, I have breakfast, I go to work, I go home, I go to bed, y las preguntas What time do you...? / I ... at ... . No introduzcas gramática nueva.`

## Expected System Behavior

The system should:

- activate A0 Level Control and the Modo ESL A0 rules;
- preserve the exact target language supplied by the teacher;
- avoid introducing untaught grammar or unnecessary vocabulary;
- design the worksheet around a clear communicative learning purpose;
- provide controlled-to-guided practice appropriate to true beginners;
- ensure instructions are understandable for the intended learners;
- check feasibility for a 30-minute classroom use;
- apply resource quality control before declaring the resource classroom-ready.

## Controlled Runtime Result

The resource was designed as a 30-minute A0 worksheet with four stages:

1. **Recognize:** learners identify the target daily-routine expressions.
2. **Match:** learners connect routine expressions with their meanings/representations.
3. **Build:** learners complete short supported sentences using the supplied target language.
4. **Ask and answer:** learners practice the supplied question pattern `What time do you...?` and answer with `I ... at ... .` using the taught routines.

The resource avoids introducing additional tense forms, third-person forms, new question structures, or unrelated vocabulary.

## Resource Alignment

**Learning purpose:** practice recognition, production, and basic oral use of the specified daily-routine language.

**Target level:** A0.

**Target language:** only the expressions and question/answer patterns specified in the request.

**Communicative value:** the final stage moves beyond mechanical completion and requires learners to use the target language with a partner.

**Dependencies:** the resource assumes the target expressions and question pattern have already been taught or modeled, but does not require knowledge outside the stated scope.

## A0 Level Validation

**PASS**

The resource respects the A0 rule that learners should not be expected to produce language they have not been taught. It uses high scaffolding, short language, repetition, clear progression, and a small controlled language load.

## Resource Quality Gates

### G1 - Pedagogical Purpose

**PASS**

Every exercise contributes to the stated practice goal.

### G2 - Level Appropriacy

**PASS**

The worksheet is suitable for true beginners and does not silently increase linguistic or cognitive demands.

### G3 - Language Scope

**PASS**

No new grammar is introduced. The target language remains within the teacher-specified scope.

### G4 - Communication

**PASS**

The worksheet culminates in a short partner interaction rather than ending with written completion alone.

### G5 - Feasibility and Usability

**PASS**

The sequence is realistic for approximately 30 minutes and can be used with ordinary classroom materials.

## Final Result

**STATUS: PASS**

The controlled runtime test confirms that Resource Management governs the creation and validation of a classroom resource. The system does not treat the worksheet as an independent artifact; it preserves level, target language, communicative purpose, prerequisites, and feasibility.

## Validation Note

This is a controlled conversational runtime simulation through the AI TEACHER LAB workflow. It is not an automated software integration test.
