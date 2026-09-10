# MVP Runtime Test 04 - Resource Decision

## Purpose

Verify that the executable lesson workflow makes an explicit resource decision before specialized resource production and can legitimately decide that no specialized resource is required.

## What changed

The vertical slice now runs a resource decision immediately after level control and the pedagogical learning plan.

The decision is exposed as `resource_decision` and its action is copied into `learning_plan.resource_need`.

Supported actions are:

- `CREATE`
- `REUSE`
- `ADAPT`
- `OMIT`
- `NO_RESOURCE_REQUIRED`

The MVP includes only transparent rules needed for this test. It defaults to `NO_RESOURCE_REQUIRED`, while an objective that explicitly requires listening or audiovisual input can justify a resource. An explicit `RESOURCE_REQUIRED:` request constraint is also preserved.

## Expected flow

Request -> Context -> Level Control -> Pedagogical Decision -> Resource Decision -> Tool Selection -> Generation -> QC

## Local validation

Update the repository:

```bash
git pull
```

Run the unit and integration tests locally from the repository root:

```bash
PYTHONPATH="$PWD" "/c/Users/Deejh/AppData/Local/Python/bin/python.exe" -m unittest tests.unit.test_resource_decision tests.integration.test_resource_decision_vertical_slice
```

## Test cases

### Case 1 - No specialized resource

Objective:

`Discuss past experiences and ask follow-up questions.`

Expected:

`NO_RESOURCE_REQUIRED`

### Case 2 - Listening objective

Objective:

`Understand and respond to a short listening text.`

Expected:

`CREATE` with resource type `audio`.

## Important

A repository update does not mean the runtime test has passed. The test must be executed locally. The goal is to verify the decision itself, not merely that the field exists.
