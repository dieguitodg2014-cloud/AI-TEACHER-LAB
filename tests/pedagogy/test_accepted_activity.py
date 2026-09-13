from core.pedagogy.accepted_activity import materialize_accepted_activity
from core.pedagogy.activity_acceptance import AcceptanceResult


def test_only_accepted_activity_crosses_downstream_boundary():
    class Result:
        activity = {"name": "valid"}
        attempts = (1,)
        acceptance = AcceptanceResult("ACCEPT", (), False)

    contract = object()
    accepted = materialize_accepted_activity(contract, Result())
    assert accepted is not None
    assert accepted.activity["name"] == "valid"


def test_rejected_activity_never_crosses_downstream_boundary():
    class Result:
        activity = {"name": "invalid"}
        attempts = (1,)
        acceptance = AcceptanceResult("HUMAN_HANDOFF", ("still invalid",))

    accepted = materialize_accepted_activity(object(), Result())
    assert accepted is None
