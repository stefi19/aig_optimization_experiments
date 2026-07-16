from semantic_patterns import exhaustive_bus_assignments, generate_semantic_patterns


def test_semantic_patterns_are_deterministic():
    buses = [{"name": "a", "width": 3, "role": "data_operand"}, {"name": "s", "width": 1, "role": "selector"}]
    first = generate_semantic_patterns(buses, seed=1)
    second = generate_semantic_patterns(buses, seed=1)
    assert first == second
    assert any(pattern.pattern_family == "control_selector" for pattern in first)


def test_exhaustive_assignments_respect_scalar_limit():
    buses = [{"name": "a", "width": 2}, {"name": "b", "width": 1}]
    rows, evidence = exhaustive_bus_assignments(buses, max_scalar_bits=3)
    assert evidence == "formal_exhaustive"
    assert len(rows) == 8
    rows, evidence = exhaustive_bus_assignments(buses, max_scalar_bits=2)
    assert rows == []
    assert evidence == "support_too_large_for_exhaustive_formal"
