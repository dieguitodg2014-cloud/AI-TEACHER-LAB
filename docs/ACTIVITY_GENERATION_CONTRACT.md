# Activity Generation Contract

## Purpose

The Activity Generation Contract is the boundary between Bionic's pedagogical planning and an activity content generator.

Pedagogical decisions are made before generation. The generator instantiates content within those decisions. The validator independently checks the generated activity.

## Pipeline

```text
Lesson / Pedagogical Plan
        |
        v
Sequence Planner
        |
        v
Activity Generation Contract
        |
        v
Activity Generator
        |
        v
Activity Validator
        |
        +---- PASS
        +---- PASS_WITH_WARNINGS
        +---- REVISE
        +---- REJECT
```

## Contract principles

1. The contract is provider-agnostic.
2. A generator must not silently change level, interaction, skill, cognitive demand, target language, or duration.
3. `must_include` protects essential pedagogical requirements.
4. `must_not_include` protects explicit constraints.
5. Student output must be observable when the objective requires production.
6. Pair and group activities must define meaningful participation for the learners involved.
7. A0 activities require observable scaffolding when the contract calls for it.
8. Validation is independent of generation.
9. Aesthetic quality never compensates for a critical pedagogical failure.
10. A failed generation can enter a specific revision cycle; it must not be silently accepted.

## Required fields

- `activity_id`
- `pattern_id`
- `level`
- `objective_ids`
- `skill`
- `language_target`
- `vocabulary`
- `interaction`
- `cognitive_demand`
- `scaffolding`
- `duration_minutes`

Optional control fields:

- `constraints`
- `must_include`
- `must_not_include`
- `evidence_expected`

## Validation boundary

Contract validation checks whether the specification itself is coherent. Activity validation checks whether the generated artifact actually follows that specification.

This separation prevents the generator from becoming the authority that defines its own success.
