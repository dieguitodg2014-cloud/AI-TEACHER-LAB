from core.pedagogy.accepted_activity import materialize_accepted_activity
from core.pedagogy.activity_revision import ActivityRevisionEngine

from tests.pedagogy.test_activity_revision import make_contract, valid_activity


def test_revision_result_crosses_only_after_acceptance():
    contract = make_contract()

    def generator(contract):
        activity = valid_activity(contract)
        activity["oral_output_by_student"] = {"Student A": "asks and answers"}
        return activity

    def reviser(revision_contract):
        return valid_activity(revision_contract.source_contract)

    result = ActivityRevisionEngine(max_attempts=3).run(contract, generator, reviser)

    accepted = materialize_accepted_activity(contract, result)

    assert result.acceptance is not None
    assert result.acceptance.decision == "ACCEPT"
    assert accepted is not None
    assert accepted.acceptance.decision == "ACCEPT"


def test_rejected_revision_result_cannot_cross_downstream_boundary():
    contract = make_contract()

    def generator(contract):
        activity = valid_activity(contract)
        activity["oral_output_by_student"] = {"Student A": "asks and answers"}
        return activity

    def reviser(revision_contract):
        return valid_activity(revision_contract.source_contract) | {
            "oral_output_by_student": {"Student A": "asks and answers"}
        }

    result = ActivityRevisionEngine(max_attempts=2).run(contract, generator, reviser)

    accepted = materialize_accepted_activity(contract, result)

    assert result.acceptance is not None
    assert result.acceptance.decision == "HUMAN_HANDOFF"
    assert accepted is None
