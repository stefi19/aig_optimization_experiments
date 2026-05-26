"""
tests/test_region_correspondence.py
=====================================
Unit tests for region_correspondence.py.

All tests use in-memory _Network / _AnalyzedNet objects built from tiny
hand-crafted circuits — no BLIF files on disk are required.

Circuit used in most fixtures:
  Primary inputs: a, b, c
  g1 = AND(a, b)          level 1
  g2 = OR(g1, c)          level 2   (output)
  g3 = AND(a, c)          level 1   (internal, not output)

  Original: nodes g1, g3 are internal (g2 is output).
  Optimised: same topology but renamed n1, n3 (n2 is output).
"""

import os
import sys
import math

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from region_correspondence import (
    _Node,
    _Network,
    _AnalyzedNet,
    _parse_blif,
    _simulate_network,
    _fanin_cone,
    _bit_sim,
    _jaccard,
    _size_sim,
    region_score,
    _score_pairs,
    _compute_summary,
    build_markdown,
    CONE_DEPTHS,
    TOP_K_REGION,
    W_SIM,
    W_SUPPORT,
    W_SIZE,
)


# ---------------------------------------------------------------------------
# Helpers to build minimal _Network / _AnalyzedNet in-memory
# ---------------------------------------------------------------------------

def _make_net(inputs, outputs, node_specs):
    """
    node_specs: list of (output, [inputs], [cover_rows])
    cover_rows use the standard SOP notation, e.g. ["11 1"] for AND.
    """
    nodes = [_Node(o, i, c) for o, i, c in node_specs]
    net = _Network(inputs=inputs, outputs=outputs, nodes=nodes)
    for node in nodes:
        net.node_map[node.output] = node
    return net


def _analyzed_from_net(net: _Network) -> _AnalyzedNet:
    """Build _AnalyzedNet from an in-memory _Network (no file I/O)."""
    from region_correspondence import _simulate_network, _fanin_cone, CONE_DEPTHS
    values, mask, total = _simulate_network(net)
    output_set = set(net.outputs)
    internal = [n.output for n in net.nodes if n.output not in output_set]
    cones = {}
    for name in internal:
        for depth in CONE_DEPTHS:
            cones[(name, depth)] = _fanin_cone(name, net, depth)
    return _AnalyzedNet(
        path="<memory>",
        net=net,
        values=values,
        mask=mask,
        total_patterns=total,
        internal_nodes=internal,
        cones=cones,
    )


# Tiny AND-OR circuit (see module docstring)
def _orig_net():
    return _make_net(
        inputs=["a", "b", "c"],
        outputs=["g2"],
        node_specs=[
            ("g1", ["a", "b"], ["11 1"]),     # g1 = a AND b
            ("g2", ["g1", "c"], ["11 1", "01 1", "10 1"]),   # g2 = g1 OR c
            ("g3", ["a", "c"], ["11 1"]),     # g3 = a AND c
        ],
    )


def _opt_net():
    """Same logic, renamed nodes."""
    return _make_net(
        inputs=["a", "b", "c"],
        outputs=["n2"],
        node_specs=[
            ("n1", ["a", "b"], ["11 1"]),
            ("n2", ["n1", "c"], ["11 1", "01 1", "10 1"]),
            ("n3", ["a", "c"], ["11 1"]),
        ],
    )


# ---------------------------------------------------------------------------
# _fanin_cone
# ---------------------------------------------------------------------------

class TestFaninCone:

    def test_depth1_root_in_cone(self):
        net = _orig_net()
        cone_nodes, cone_pis = _fanin_cone("g1", net, depth=1)
        assert "g1" in cone_nodes

    def test_depth1_fanins_are_pis(self):
        net = _orig_net()
        cone_nodes, cone_pis = _fanin_cone("g1", net, depth=1)
        # g1 fanins are primary inputs a and b
        assert "a" in cone_pis
        assert "b" in cone_pis

    def test_depth1_no_deeper_nodes(self):
        net = _orig_net()
        cone_nodes, cone_pis = _fanin_cone("g2", net, depth=1)
        # At depth=1 from g2: g2 is the root (in cone); g1 is one level below g2
        # and is included; g1's own fanins (a, b) become boundary PIs.
        # g3 (unrelated node) must NOT appear in the cone.
        assert "g3" not in cone_nodes
        # g1's fanins a and b should be cut to the boundary
        assert "a" in cone_pis or "b" in cone_pis

    def test_depth2_includes_transitive_fanin(self):
        net = _orig_net()
        cone_nodes, _ = _fanin_cone("g2", net, depth=2)
        # At depth 2 from g2: g2 → g1 → {a, b};  so g1 should be in cone
        assert "g2" in cone_nodes
        assert "g1" in cone_nodes

    def test_primary_input_root_is_pi(self):
        net = _orig_net()
        cone_nodes, cone_pis = _fanin_cone("a", net, depth=2)
        assert "a" in cone_pis
        assert len(cone_nodes) == 0

    def test_depth3_pis_are_true_inputs(self):
        net = _orig_net()
        _, cone_pis = _fanin_cone("g2", net, depth=3)
        # Full cone of g2 at depth 3 should reach all true PIs
        assert cone_pis <= {"a", "b", "c"}

    def test_cone_nodes_disjoint_from_pis(self):
        net = _orig_net()
        cone_nodes, cone_pis = _fanin_cone("g2", net, depth=3)
        assert cone_nodes.isdisjoint(cone_pis)


# ---------------------------------------------------------------------------
# _bit_sim
# ---------------------------------------------------------------------------

class TestBitSim:

    def test_identical_is_1(self):
        assert _bit_sim(0b1010, 0b1010, 4) == pytest.approx(1.0)

    def test_complementary_is_0(self):
        assert _bit_sim(0b1010, 0b0101, 4) == pytest.approx(0.0)

    def test_half_overlap(self):
        assert _bit_sim(0b1100, 0b1010, 4) == pytest.approx(0.5)

    def test_zero_patterns_returns_0(self):
        assert _bit_sim(0, 0, 0) == 0.0


# ---------------------------------------------------------------------------
# _jaccard
# ---------------------------------------------------------------------------

class TestJaccard:

    def test_identical_sets(self):
        assert _jaccard({"a", "b"}, {"a", "b"}) == pytest.approx(1.0)

    def test_disjoint_sets(self):
        assert _jaccard({"a"}, {"b"}) == pytest.approx(0.0)

    def test_partial_overlap(self):
        # |{a,b} ∩ {b,c}| / |{a,b,c}| = 1/3
        assert _jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)

    def test_both_empty(self):
        assert _jaccard(set(), set()) == pytest.approx(1.0)

    def test_one_empty(self):
        assert _jaccard({"a"}, set()) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _size_sim
# ---------------------------------------------------------------------------

class TestSizeSim:

    def test_equal_sizes(self):
        assert _size_sim(3, 3) == pytest.approx(1.0)

    def test_diff_of_1(self):
        assert _size_sim(2, 3) == pytest.approx(0.5)

    def test_diff_of_4(self):
        assert _size_sim(0, 4) == pytest.approx(1 / 5)

    def test_symmetric(self):
        assert _size_sim(1, 5) == pytest.approx(_size_sim(5, 1))


# ---------------------------------------------------------------------------
# region_score
# ---------------------------------------------------------------------------

class TestRegionScore:

    def test_all_ones_gives_1(self):
        assert region_score(1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_all_zeros_gives_0(self):
        assert region_score(0.0, 0.0, 0.0) == pytest.approx(0.0)

    def test_weights_sum_to_1(self):
        assert W_SIM + W_SUPPORT + W_SIZE == pytest.approx(1.0)

    def test_sim_dominates(self):
        # sim weight (0.50) > support (0.40) > size (0.10)
        score_sim_high  = region_score(1.0, 0.0, 0.0)
        score_sup_high  = region_score(0.0, 1.0, 0.0)
        score_size_high = region_score(0.0, 0.0, 1.0)
        assert score_sim_high > score_sup_high > score_size_high

    def test_known_value(self):
        expected = W_SIM * 0.8 + W_SUPPORT * 0.6 + W_SIZE * 1.0
        assert region_score(0.8, 0.6, 1.0) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# _score_pairs
# ---------------------------------------------------------------------------

class TestScorePairs:

    def _orig(self):
        return _analyzed_from_net(_orig_net())

    def _opt(self):
        return _analyzed_from_net(_opt_net())

    def test_returns_list(self):
        result = _score_pairs(self._orig(), self._opt(), "toy", "balance")
        assert isinstance(result, list) and len(result) > 0

    def test_required_columns_present(self):
        result = _score_pairs(self._orig(), self._opt(), "toy", "balance")
        for col in ("benchmark", "optimization", "depth", "optimized_node",
                    "rank", "original_candidate", "region_score",
                    "root_sim_score", "cone_support_jaccard", "cone_size_sim",
                    "opt_cone_size", "orig_cone_size"):
            assert col in result[0], f"missing column: {col}"

    def test_rank_1_has_highest_score_per_group(self):
        result = _score_pairs(self._orig(), self._opt(), "toy", "balance")
        from collections import defaultdict
        groups = defaultdict(list)
        for row in result:
            groups[(row["optimized_node"], row["depth"])].append(row)
        for rows in groups.values():
            rows.sort(key=lambda r: r["rank"])
            assert rows[0]["region_score"] == max(r["region_score"] for r in rows)

    def test_at_most_top_k_per_group(self):
        result = _score_pairs(self._orig(), self._opt(), "toy", "balance")
        from collections import defaultdict
        groups = defaultdict(list)
        for row in result:
            groups[(row["optimized_node"], row["depth"])].append(row)
        for rows in groups.values():
            assert len(rows) <= TOP_K_REGION

    def test_all_depths_present(self):
        result = _score_pairs(self._orig(), self._opt(), "toy", "balance")
        depths_found = {row["depth"] for row in result}
        assert depths_found == set(CONE_DEPTHS)

    def test_identical_nets_give_score_1(self):
        # When original == optimised (same topology, same names), rank-1 should be 1.0
        net = _orig_net()
        an = _analyzed_from_net(net)
        result = _score_pairs(an, an, "toy", "original")
        rank1 = [r for r in result if r["rank"] == 1 and r["depth"] == 1]
        for row in rank1:
            # The node should match itself perfectly
            if row["optimized_node"] == row["original_candidate"]:
                assert row["region_score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:

    def _candidate_rows(self):
        orig = _analyzed_from_net(_orig_net())
        opt  = _analyzed_from_net(_opt_net())
        return _score_pairs(orig, opt, "toy", "balance")

    def test_returns_list(self):
        result = _compute_summary(self._candidate_rows())
        assert isinstance(result, list)

    def test_one_row_per_benchmark_opt_depth(self):
        rows = self._candidate_rows()
        result = _compute_summary(rows)
        keys = {(r["benchmark"], r["optimization"], r["depth"]) for r in result}
        assert len(result) == len(keys)

    def test_depth_values_are_cone_depths(self):
        result = _compute_summary(self._candidate_rows())
        for row in result:
            assert row["depth"] in CONE_DEPTHS

    def test_required_columns_present(self):
        result = _compute_summary(self._candidate_rows())
        for col in ("benchmark", "optimization", "depth", "total_opt_nodes",
                    "avg_rank1_region_score", "avg_rank1_cone_sim",
                    "avg_rank1_cone_support", "avg_rank1_cone_size_sim",
                    "pct_rank1_above_0_8"):
            assert col in result[0], f"missing column: {col}"

    def test_avg_scores_in_unit_interval(self):
        for row in _compute_summary(self._candidate_rows()):
            assert 0.0 <= row["avg_rank1_region_score"] <= 1.0
            assert 0.0 <= row["pct_rank1_above_0_8"] <= 1.0

    def test_empty_candidates_returns_empty(self):
        assert _compute_summary([]) == []


# ---------------------------------------------------------------------------
# build_markdown
# ---------------------------------------------------------------------------

class TestBuildMarkdown:

    def _rows(self):
        orig = _analyzed_from_net(_orig_net())
        opt  = _analyzed_from_net(_opt_net())
        cands = _score_pairs(orig, opt, "toy", "balance")
        summary = _compute_summary(cands)
        return cands, summary

    def test_returns_string(self):
        cands, summary = self._rows()
        md = build_markdown(cands, summary, True)
        assert isinstance(md, str) and len(md) > 0

    def test_contains_depth_sections(self):
        cands, summary = self._rows()
        md = build_markdown(cands, summary, True)
        for d in CONE_DEPTHS:
            assert f"Depth {d}" in md

    def test_contains_cross_depth_section(self):
        cands, summary = self._rows()
        md = build_markdown(cands, summary, True)
        assert "Cross-depth" in md

    def test_contains_interpretation(self):
        cands, summary = self._rows()
        md = build_markdown(cands, summary, True)
        assert "Interpretation" in md

    def test_missing_variants_note(self):
        md = build_markdown([], [], False)
        assert "run_abc_variants" in md or "missing" in md.lower() or "run" in md

    def test_missing_variants_returns_early(self):
        md = build_markdown([], [], False)
        # Should not contain depth tables when no data
        assert "Depth 1" not in md

    def test_empty_data_with_variants_does_not_crash(self):
        md = build_markdown([], [], True)
        assert isinstance(md, str)
