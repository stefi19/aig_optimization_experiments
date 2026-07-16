from semantic_ast import SemanticExpr, input_expr
from semantic_formal_validation import FormalValidationConfig, validate_candidate_exhaustive
from semantic_patterns import generate_semantic_patterns
from semantic_simulation import simulate_candidate
from semantic_types import unsigned_bitvector


def write_and_blif(path):
    path.write_text(
        ".model and2\n"
        ".inputs a_0 b_0\n"
        ".outputs y\n"
        ".names a_0 b_0 y\n"
        "11 1\n"
        ".end\n",
        encoding="utf-8",
    )


def io():
    return [{"name": "a", "width": 1, "role": "data_operand", "ordered_member_nodes": ("a_0",)}, {"name": "b", "width": 1, "role": "data_operand", "ordered_member_nodes": ("b_0",)}], {"name": "y", "width": 1, "ordered_member_nodes": ("y",)}


def test_simulation_match_and_mismatch(tmp_path):
    blif = tmp_path / "and.blif"
    write_and_blif(blif)
    inputs, output = io()
    patterns = generate_semantic_patterns(inputs, random_count=0)
    good = SemanticExpr("and", (input_expr("a", 1), input_expr("b", 1)), unsigned_bitvector(1))
    bad = SemanticExpr("or", (input_expr("a", 1), input_expr("b", 1)), unsigned_bitvector(1))
    assert simulate_candidate(blif_path=blif, input_buses=inputs, output_bus=output, expr=good, patterns=patterns)["simulation_status"] == "simulation_match"
    bad_result = simulate_candidate(blif_path=blif, input_buses=inputs, output_bus=output, expr=bad, patterns=patterns)
    assert bad_result["simulation_status"] == "simulation_mismatch"
    assert bad_result["simulation_evidence_level"] == "sampled_estimate"


def test_formal_region_verification_accepts_only_exact_candidate(tmp_path):
    blif = tmp_path / "and.blif"
    write_and_blif(blif)
    inputs, output = io()
    good = SemanticExpr("and", (input_expr("a", 1), input_expr("b", 1)), unsigned_bitvector(1))
    bad = SemanticExpr("or", (input_expr("a", 1), input_expr("b", 1)), unsigned_bitvector(1))
    assert validate_candidate_exhaustive(blif_path=blif, input_buses=inputs, output_bus=output, expr=good)["formal_status"] == "formally_verified_region"
    rejected = validate_candidate_exhaustive(blif_path=blif, input_buses=inputs, output_bus=output, expr=bad)
    assert rejected["formal_status"] == "disproven"
    assert rejected["proof_scope"] == "region"
    assert rejected["formal_evidence_level"] == "formal_exhaustive"


def test_formal_rejects_large_support_without_overclaim(tmp_path):
    blif = tmp_path / "and.blif"
    write_and_blif(blif)
    inputs, output = io()
    expr = SemanticExpr("and", (input_expr("a", 1), input_expr("b", 1)), unsigned_bitvector(1))
    result = validate_candidate_exhaustive(blif_path=blif, input_buses=inputs, output_bus=output, expr=expr, config=FormalValidationConfig(max_scalar_bits=1))
    assert result["formal_status"] == "unsupported"
    assert result["formal_evidence_level"] == "unresolved"
