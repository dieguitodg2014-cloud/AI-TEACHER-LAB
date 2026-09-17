from core.workflow.vertical_slice import result_to_dict, run_lesson_planning


def test_result_to_dict_exposes_lists_at_external_boundary():
    result = run_lesson_planning({"level": "A1", "objective": "Talk about daily routines"})

    payload = result_to_dict(result)

    assert isinstance(result.missing, tuple)
    assert isinstance(result.errors, tuple)
    assert isinstance(payload["missing"], list)
    assert isinstance(payload["errors"], list)
