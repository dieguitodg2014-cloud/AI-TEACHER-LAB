# MVP Runtime Test 03 - Content Alignment

## Purpose

Verify that the real lesson-generation flow does not accept a technically valid lesson that violates explicit content constraints.

## What changed

The generation request now carries the requested topic and prior knowledge into the provider boundary. Generation QC now checks:

- target topic presence in generated lesson content;
- explicit forbidden terms declared through `FORBIDDEN_TERMS:` constraints.

A content violation is a blocking QC error and enters the existing bounded revision loop.

## Golden case

Use:

`tests/regression/golden_case_a2_present_perfect.json`

The case requests Present Perfect and explicitly forbids `used to`.

## Preconditions

- LM Studio is running.
- `google/gemma-3n-e4b` is loaded.
- The local server is running on port 1234.
- The local repository has the latest `main` branch.
- Python is available.

## Update local repository

From the repository root:

```bash
git pull
```

## Run

From the repository root:

```bash
PYTHONPATH="$PWD" "/c/Users/Deejh/AppData/Local/Python/bin/python.exe" tools/connectors/run_local_runtime_test.py
```

## Expected behavior

The flow remains:

Request -> Context -> Level Control -> Pedagogical Decision -> Tool Selection -> Local Generator -> Generation QC -> Revision if required

The final result should be `READY` only if the generated lesson satisfies the explicit content constraint. If Gemma initially generates `used to`, QC should reject that attempt and provide `CONTENT_FORBIDDEN_TERM` to the revision loop.

## Important

Do not treat a `READY` result alone as proof that content alignment was exercised. Inspect the generated lesson and the `attempts` value. A revised result should show more than one attempt when the first generation violates the constraint.

This test must be executed on the teacher's local machine before it is considered passed. GitHub repository updates do not execute the local runtime test.
