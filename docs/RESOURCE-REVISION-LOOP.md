# Resource Revision Loop

The resource pipeline uses a bounded correction loop after provider production.

```text
Approved TaskPacket
        |
        v
Provider Production
        |
        v
Resource QC
        |
        v
Resource Acceptance Gate
   |            |
 ACCEPT     REVISION_REQUIRED
   |            |
 Delivery   Revision Engine
                 |
                 v
              QC again
                 |
                 v
             Acceptance
```

## Rules

1. The `TaskPacket` is immutable authority for the resource task.
2. Every produced version is validated against that same task.
3. A provider cannot bypass QC by returning `READY`.
4. Correctable failures trigger a bounded revision attempt.
5. After the revision boundary is exhausted, the system returns `HUMAN_HANDOFF` rather than looping indefinitely.
6. Invalid reviser output also produces `HUMAN_HANDOFF`.
7. Acceptance is granted only by `ResourceAcceptanceGate`.

The current default revision budget is one revision. This keeps resource production deterministic and prevents uncontrolled provider retry loops.
