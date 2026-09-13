from core.pedagogy.pattern_registry import PatternFilter, PatternRegistry


def test_default_registry_has_18_unique_patterns():
    registry = PatternRegistry()
    assert len(registry.all()) == 18
    assert len(set(registry.ids())) == 18


def test_a0_filter_excludes_higher_load_patterns():
    registry = PatternRegistry()
    patterns = registry.filter(PatternFilter(level="A0"))
    ids = {p.pattern_id for p in patterns}
    assert "MODEL_AND_REPEAT" in ids
    assert "CONTROLLED_PRACTICE" in ids
    assert "INFORMATION_GAP" not in ids
    assert "JIGSAW" not in ids
    assert "PROBLEM_SOLVING" not in ids


def test_a1_pair_speaking_filter_returns_appropriate_patterns():
    registry = PatternRegistry()
    patterns = registry.filter(PatternFilter(level="A1", interaction="PAIR", skill="SPEAKING"))
    ids = {p.pattern_id for p in patterns}
    assert "CONTROLLED_PRACTICE" in ids
    assert "GUIDED_PRODUCTION" in ids
    assert "INTERVIEW" in ids
    assert "INFORMATION_GAP" in ids


def test_student_output_filter():
    registry = PatternRegistry()
    patterns = registry.filter(PatternFilter(requires_student_output=True))
    assert patterns
    assert all(p.requires_student_output for p in patterns)


def test_sequence_role_filter():
    registry = PatternRegistry()
    patterns = registry.filter(PatternFilter(sequence_role="ASSESSMENT"))
    ids = {p.pattern_id for p in patterns}
    assert "EXIT_TICKET" in ids
    assert "QUICK_CHECK" in ids


def test_get_returns_requested_pattern():
    registry = PatternRegistry()
    assert registry.get("INTERVIEW").name == "Interview"


def test_unknown_pattern_raises_key_error():
    registry = PatternRegistry()
    try:
        registry.get("NOT_A_PATTERN")
    except KeyError:
        pass
    else:
        raise AssertionError("Unknown pattern must raise KeyError")
