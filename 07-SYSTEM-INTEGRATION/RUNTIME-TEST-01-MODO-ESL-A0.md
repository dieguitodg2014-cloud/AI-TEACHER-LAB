# AI TEACHER LAB - RUNTIME TEST 01

## Modo ESL A0

### Purpose

Validate that Modo ESL correctly activates the special A0 rules for a true beginner and produces a usable communicative lesson without assuming prior English knowledge or introducing unnecessary language.

## Test Input

`Modo ESL: Present Simple A0`

## Expected Behavior

1. Activate Modo ESL A0.
2. Treat learners as true beginners.
3. Provide bilingual explanation in English and Spanish.
4. Explain meaning, use, affirmative, negative, and question forms clearly and minimally.
5. Use high scaffolding and controlled language load.
6. Avoid tasks that require students to produce language before it has been taught or modeled.
7. Balance grammar with oral production.
8. Include two meaningful conversations.
9. Include a worksheet using only taught or necessary language.
10. Follow the default 90-minute Modo ESL lesson architecture.

## Runtime Result

**PASS**

The system activated the A0-specific behavior and designed the lesson for true beginners. The lesson prioritized comprehensible input, modeling, repetition with purpose, controlled practice, and supported oral interaction before freer production.

The explanation was bilingual, and the language load was deliberately restricted. Activities did not depend on students already knowing English. The lesson included affirmative, negative, and question practice, two supported conversations, oral production, and a worksheet.

## A0 Compliance Checks

### Check 1 - Level Identification

**PASS** - A0 was treated as a true-beginner condition rather than as a simplified A1 lesson.

### Check 2 - Bilingual Explanation

**PASS** - English content was supported with Spanish explanation where needed for comprehension.

### Check 3 - Language Load

**PASS** - The lesson avoided unnecessary vocabulary and grammar expansion.

### Check 4 - Scaffolding

**PASS** - Modeling, controlled practice, sentence support, and guided interaction preceded freer production.

### Check 5 - Oral Production

**PASS** - Students had repeated opportunities to say meaningful target-language sentences with support.

### Check 6 - No Premature Production

**PASS** - Tasks did not require learners to generate unknown language before instruction and modeling.

### Check 7 - Communicative Purpose

**PASS** - Present Simple practice was connected to basic real-life communication rather than isolated form manipulation.

### Check 8 - Two Conversations

**PASS** - Two supported conversations were included as required by Modo ESL.

### Check 9 - Worksheet

**PASS** - The worksheet reinforced the target language and remained within the lesson's taught scope.

### Check 10 - Timing

**PASS** - The default 90-minute Modo ESL duration was respected.

## Quality Gates

- G1 - Level: **PASS**
- G2 - Alignment: **PASS**
- G3 - Language: **PASS**
- G4 - Communication: **PASS**
- G5 - Feasibility: **PASS**

## Validation Decision

**TEST 01 - PASS**

The runtime test confirms that Modo ESL can activate the A0-specific pedagogical rules and maintain true-beginner accessibility while still providing meaningful communication and oral production.

## Architectural Implication

A0 behavior is not produced merely by shortening sentences or simplifying vocabulary. The system changes scaffolding, language load, task dependency, production demands, explanation support, and interaction design to match true-beginner learning conditions.
