# MVP Runtime Test 02 - Local LM Studio

## Purpose

Execute the first real end-to-end lesson-generation flow using the local LM Studio server and Gemma 3n E4B.

## Preconditions

- LM Studio installed and running.
- Gemma model loaded: `google/gemma-3n-e4b`.
- LM Studio server status: `Running`.
- API endpoint available at the local OpenAI-compatible endpoint.
- Repository checked out locally.
- Python environment available for the project.

LM Studio documents `/v1/chat/completions` as an OpenAI-compatible endpoint and uses `http://localhost:1234/v1` as the default base URL for clients. citeturn0view0turn1view0

## Golden case

Use `tests/regression/golden_case_a2_present_perfect.json`:

- Level: A2
- Audience: adults
- Duration: 90 minutes
- Topic: Present Perfect
- Prior knowledge: Past Simple
- Objective: discuss past experiences and ask follow-up questions
- Constraint: question formation

## Local model

- Model ID: `google/gemma-3n-e4b`
- Default connector endpoint: `http://127.0.0.1:1234/v1/chat/completions`

## Execution

From the repository root:

```text
python tools/connectors/run_local_runtime_test.py
```

The runner also accepts:

```text
python tools/connectors/run_local_runtime_test.py --model google/gemma-3n-e4b --base-url http://127.0.0.1:1234/v1/chat/completions
```

## Expected behavior

The flow should execute:

`Request -> Context -> Level Control -> Pedagogical Decision -> Tool Selection -> Local Generator -> Generation QC`

A successful execution returns `READY` and includes the generated lesson and QC result.

A non-READY result is a test failure and should be investigated from the reported status/errors. Do not claim this test passed until it has actually been executed on the teacher's machine.

## Important note

This test validates the real local provider connection. It does not replace the provider-agnostic architecture, and it does not make LM Studio the only possible tool. The local connector remains one runtime implementation behind the existing tool registry and orchestration layers.
