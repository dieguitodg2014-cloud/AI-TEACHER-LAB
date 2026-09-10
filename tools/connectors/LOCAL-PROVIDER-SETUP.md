# Local Provider Setup

AI-TEACHER-LAB now includes a provider callable for OpenAI-compatible local servers.

## LM Studio

LM Studio exposes an OpenAI-compatible Chat Completions endpoint. Start the server from LM Studio's Developer tab.

Default endpoint used by the connector:

`http://127.0.0.1:1234/v1/chat/completions`

Set the model identifier used by the local server before executing the workflow:

Windows PowerShell:

```powershell
$env:AI_TEACHER_LAB_PROVIDER_MODEL="YOUR-LM-STUDIO-MODEL-ID"
```

Optional endpoint override:

```powershell
$env:AI_TEACHER_LAB_PROVIDER_URL="http://127.0.0.1:1234/v1/chat/completions"
```

An API token can be supplied with `AI_TEACHER_LAB_PROVIDER_API_KEY` if authentication is enabled in the local server. No token is required by default in a standard local setup.

## Architecture boundary

The connector implements the existing `LessonGenerator` callable contract. It does not make pedagogical decisions, select tools, bypass QC, or change the approved learning plan.

The workflow remains responsible for:

1. Context
2. Level decision
3. Pedagogical decision
4. Tool selection
5. Generation
6. QC and bounded revision

The connector only performs provider execution and converts the provider response into a Python dictionary for the existing validation/QC boundary.

## Runtime note

Repository tests mock the HTTP call and verify the connector contract. A real end-to-end run still requires LM Studio to be running locally with a loaded model and must be executed on the teacher's machine.
