"""Bus-hypothesis inference for semantic scalar interfaces.

The inferred mode deliberately uses only scalar interface names and circuit
structure. Ground-truth bus metadata is used only by the evaluation helpers.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass

from boundary_graph import CircuitGraph
from semantic_interface import BusGroundTruth


SEMANTIC_BUS_SCHEMA_VERSION = "semantic_bus_hypothesis_v1"
BUS_DIRECTIONS = ("input", "output")
BUS_ROLES = ("data_operand", "control", "selector", "output", "constant_parameter", "unknown")
BIT_ORDERS = ("lsb_to_msb", "msb_to_lsb", "unknown", "ambiguous")
SIGNEDNESS_VALUES = ("unsigned", "signed", "unknown")
INFERENCE_MODES = ("ground_truth_bus_mode", "inferred_bus_mode")

BRACKET_RE = re.compile(r"^(?P<prefix>.+)\[(?P<index>\d+)\]$")
UNDERSCORE_RE = re.compile(r"^(?P<prefix>.+)_(?P<index>\d+)$")
SUFFIX_RE = re.compile(r"^(?P<prefix>[A-Za-z_][A-Za-z_]*)(?P<index>\d+)$")


@dataclass(frozen=True)
class NameFeatures:
    prefix: str
    index: int | None
    style: str
    name_prefix_score: float
    index_contiguity_score: float
    name_order_confidence: float


@dataclass(frozen=True)
class BusHypothesis:
    bus_hypothesis_id: str
    region_id: str
    inference_mode: str
    used_ground_truth_for_generation: bool
    used_ground_truth_for_evaluation: bool
    direction: str
    role: str
    member_nodes: tuple[str, ...]
    ordered_member_nodes: tuple[str, ...]
    width: int
    bit_order: str
    signedness_hypothesis: str
    grouping_score: float
    ordering_score: float
    role_score: float
    evidence_sources: tuple[str, ...]
    feature_values: dict[str, float | str | int]
    ambiguity_count: int
    ground_truth_bus_name_if_known: str
    ground_truth_match: str
    rank: int
    schema_version: str = SEMANTIC_BUS_SCHEMA_VERSION

    def to_csv_row(self) -> dict[str, str]:
        data = asdict(self)
        row: dict[str, str] = {}
        for field in SEMANTIC_BUS_HYPOTHESIS_FIELDS:
            value = data[field]
            if isinstance(value, (list, tuple)):
                row[field] = json.dumps(list(value), sort_keys=True, separators=(",", ":"))
            elif isinstance(value, dict):
                row[field] = json.dumps(value, sort_keys=True, separators=(",", ":"))
            elif isinstance(value, bool):
                row[field] = str(value).lower()
            elif isinstance(value, float):
                row[field] = f"{value:.6f}"
            else:
                row[field] = str(value)
        return row


SEMANTIC_BUS_HYPOTHESIS_FIELDS = [
    "bus_hypothesis_id",
    "region_id",
    "inference_mode",
    "used_ground_truth_for_generation",
    "used_ground_truth_for_evaluation",
    "direction",
    "role",
    "member_nodes",
    "ordered_member_nodes",
    "width",
    "bit_order",
    "signedness_hypothesis",
    "grouping_score",
    "ordering_score",
    "role_score",
    "evidence_sources",
    "feature_values",
    "ambiguity_count",
    "ground_truth_bus_name_if_known",
    "ground_truth_match",
    "rank",
    "schema_version",
]

SEMANTIC_BUS_EVALUATION_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "inference_mode",
    "feature_mode",
    "direction",
    "ground_truth_bus_count",
    "hypothesis_count",
    "top_1_bus_match",
    "top_3_bus_match",
    "top_5_bus_match",
    "exact_bus_partition_match",
    "exact_ordered_bus_match",
    "bus_membership_precision",
    "bus_membership_recall",
    "bit_order_accuracy",
    "reversed_order_rate",
    "control_input_accuracy",
    "data_operand_accuracy",
    "output_bus_accuracy",
    "mean_ground_truth_rank",
    "mrr",
]

SEMANTIC_INPUT_ROLE_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "node",
    "predicted_role",
    "ground_truth_role",
    "role_score",
    "correct",
    "inference_mode",
]

SEMANTIC_BIT_ORDER_FIELDS = [
    "region_id",
    "case_id",
    "optimization",
    "source_type",
    "direction",
    "bus_hypothesis_id",
    "ground_truth_bus_name",
    "exact_ordered_bus_match",
    "unordered_bus_membership_match",
    "reversed_order_match",
    "partial_match",
    "ordering_method",
    "ordering_score",
    "ordering_ambiguity",
]


def parse_name_features(name: str) -> NameFeatures:
    for style, regex in (("bracket", BRACKET_RE), ("underscore", UNDERSCORE_RE), ("suffix", SUFFIX_RE)):
        match = regex.match(name)
        if match:
            prefix = match.group("prefix")
            return NameFeatures(prefix, int(match.group("index")), style, 1.0, 1.0, 1.0)
    return NameFeatures(name, None, "scalar", 0.7 if len(name) > 1 else 0.2, 1.0, 0.5)


def contiguity_score(indices: list[int]) -> float:
    if not indices:
        return 0.0
    if len(indices) == 1:
        return 1.0
    unique = sorted(set(indices))
    span = max(unique) - min(unique) + 1
    return len(unique) / span if span else 1.0


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / max(1, len(left | right))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def structural_group_score(graph: CircuitGraph | None, nodes: tuple[str, ...], direction: str) -> float:
    if graph is None or len(nodes) <= 1:
        return 1.0
    scores: list[float] = []
    for i, left in enumerate(nodes):
        for right in nodes[i + 1 :]:
            if direction == "input":
                scores.append(jaccard(set(graph.transitive_fanout([left])), set(graph.transitive_fanout([right]))))
            else:
                scores.append(jaccard(set(graph.transitive_fanin([left])), set(graph.transitive_fanin([right]))))
    return mean(scores)


def classify_role(direction: str, nodes: tuple[str, ...], prefix: str) -> tuple[str, float]:
    if direction == "output":
        return "output", 1.0
    lowered = prefix.lower()
    if len(nodes) == 1 and any(token in lowered for token in ("sel", "ctrl", "enable", "en", "cond", "s0", "s1")):
        return "selector", 0.9
    if len(nodes) == 1 and (lowered in {"s", "c"} or lowered.startswith("sel") or lowered.startswith("s")):
        return "control", 0.75
    if len(nodes) == 1 and lowered in {"a", "b", "x", "y", "d", "data", "in"}:
        return "data_operand", 0.6
    if len(nodes) == 1:
        return "control", 0.55
    return "data_operand", 0.8


def order_nodes_by_name(nodes: tuple[str, ...]) -> tuple[tuple[str, ...], str, float, int]:
    features = {node: parse_name_features(node) for node in nodes}
    indexed = [node for node in nodes if features[node].index is not None]
    if len(indexed) == len(nodes):
        ordered = tuple(sorted(nodes, key=lambda node: (features[node].index, node)))
        indices = [features[node].index for node in ordered if features[node].index is not None]
        score = contiguity_score([idx for idx in indices if idx is not None])
        ambiguity = max(0, len(nodes) - len(set(indices)))
        return ordered, "lsb_to_msb", score, ambiguity
    return tuple(sorted(nodes)), "unknown" if len(nodes) > 1 else "lsb_to_msb", 0.5 if len(nodes) == 1 else 0.0, len(nodes) if len(nodes) > 1 else 0


def group_nodes_by_name(nodes: tuple[str, ...]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        feature = parse_name_features(node)
        key = feature.prefix if feature.index is not None else node
        groups[key].append(node)
    return {key: sorted(value, key=lambda n: (parse_name_features(n).index if parse_name_features(n).index is not None else 10**9, n)) for key, value in groups.items()}


def ground_truth_hypotheses(
    *,
    region_id: str,
    direction: str,
    bus_rows: list[BusGroundTruth],
    available_nodes: tuple[str, ...],
    case_id: str,
) -> list[BusHypothesis]:
    available = set(available_nodes)
    rows = [row for row in bus_rows if row.direction == direction]
    hypotheses: list[BusHypothesis] = []
    for rank, row in enumerate(rows, start=1):
        members = tuple(node for node in row.member_signal_names if node in available)
        if not members:
            continue
        ordered = tuple(node for node in row.member_signal_names if node in available)
        hypotheses.append(
            BusHypothesis(
                bus_hypothesis_id=f"{region_id}__gt__{direction}__{row.bus_name}",
                region_id=region_id,
                inference_mode="ground_truth_bus_mode",
                used_ground_truth_for_generation=True,
                used_ground_truth_for_evaluation=True,
                direction=direction,
                role=row.role,
                member_nodes=tuple(sorted(members)),
                ordered_member_nodes=ordered,
                width=len(members),
                bit_order=row.bit_order,
                signedness_hypothesis=row.signedness,
                grouping_score=1.0,
                ordering_score=1.0,
                role_score=1.0,
                evidence_sources=("ground_truth_metadata",),
                feature_values={"ground_truth_bus": row.bus_name},
                ambiguity_count=0,
                ground_truth_bus_name_if_known=row.bus_name,
                ground_truth_match="exact",
                rank=rank,
            )
        )
    return hypotheses


def infer_bus_hypotheses(
    *,
    region_id: str,
    direction: str,
    nodes: tuple[str, ...],
    graph: CircuitGraph | None,
    feature_mode: str = "full_combined",
    max_bus_hypotheses: int = 12,
) -> list[BusHypothesis]:
    groups = group_nodes_by_name(nodes)
    hypotheses: list[BusHypothesis] = []
    for key, members_list in groups.items():
        members = tuple(sorted(members_list))
        ordered, bit_order, ordering_score, ambiguity = order_nodes_by_name(members)
        indices = [parse_name_features(node).index for node in members if parse_name_features(node).index is not None]
        name_score = mean([parse_name_features(node).name_prefix_score for node in members])
        index_score = contiguity_score([idx for idx in indices if idx is not None]) if indices else (1.0 if len(members) == 1 else 0.0)
        structure_score = structural_group_score(graph, ordered, direction)
        role, role_score = classify_role(direction, ordered, key)
        if feature_mode == "names_only":
            grouping_score = 0.75 * name_score + 0.25 * index_score
            evidence = ("name_prefix", "index_contiguity")
        elif feature_mode == "structure_only":
            grouping_score = structure_score
            evidence = ("structural_similarity",)
        elif feature_mode in {"names_plus_structure", "full_combined"}:
            grouping_score = 0.45 * name_score + 0.25 * index_score + 0.30 * structure_score
            evidence = ("name_prefix", "index_contiguity", "structural_similarity")
        else:
            grouping_score = 0.55 * name_score + 0.20 * index_score + 0.25 * structure_score
            evidence = ("name_prefix", "index_contiguity", "structural_similarity")
        hypotheses.append(
            BusHypothesis(
                bus_hypothesis_id=f"{region_id}__inf__{direction}__{key}",
                region_id=region_id,
                inference_mode="inferred_bus_mode",
                used_ground_truth_for_generation=False,
                used_ground_truth_for_evaluation=True,
                direction=direction,
                role=role,
                member_nodes=members,
                ordered_member_nodes=ordered,
                width=len(members),
                bit_order=bit_order,
                signedness_hypothesis="unknown",
                grouping_score=max(0.0, min(1.0, grouping_score)),
                ordering_score=max(0.0, min(1.0, ordering_score)),
                role_score=role_score,
                evidence_sources=evidence,
                feature_values={
                    "name_prefix": key,
                    "name_prefix_score": round(name_score, 6),
                    "index_contiguity_score": round(index_score, 6),
                    "structural_similarity_score": round(structure_score, 6),
                },
                ambiguity_count=ambiguity,
                ground_truth_bus_name_if_known="",
                ground_truth_match="not_evaluated",
                rank=0,
            )
        )

    hypotheses.sort(
        key=lambda h: (
            -h.grouping_score,
            -h.ordering_score,
            -h.width,
            h.direction,
            h.ordered_member_nodes,
            h.bus_hypothesis_id,
        )
    )
    ranked = []
    for rank, hyp in enumerate(hypotheses[:max_bus_hypotheses], start=1):
        ranked.append(BusHypothesis(**{**asdict(hyp), "rank": rank}))
    return ranked


def evaluate_hypotheses(
    *,
    region_row: dict[str, str],
    direction: str,
    hypotheses: list[BusHypothesis],
    bus_rows: list[BusGroundTruth],
    scalar_nodes: tuple[str, ...],
    feature_mode: str,
) -> dict[str, str]:
    truth = [row for row in bus_rows if row.direction == direction]
    truth_sets = [set(row.member_signal_names) & set(scalar_nodes) for row in truth]
    truth_sets = [s for s in truth_sets if s]
    truth_orders = [tuple(node for node in row.member_signal_names if node in set(scalar_nodes)) for row in truth]
    hyp_sets = [set(h.member_nodes) for h in hypotheses]
    hyp_orders = [h.ordered_member_nodes for h in hypotheses]

    def exact_partition(limit: int | None = None) -> bool:
        selected = hyp_sets if limit is None else hyp_sets[:limit]
        return sorted([sorted(s) for s in selected]) == sorted([sorted(s) for s in truth_sets])

    top_matches: list[int] = []
    reciprocal: list[float] = []
    for truth_set in truth_sets:
        rank = 0
        for idx, hyp_set in enumerate(hyp_sets, start=1):
            if hyp_set == truth_set:
                rank = idx
                break
        if rank:
            top_matches.append(rank)
            reciprocal.append(1.0 / rank)

    paired_matches = 0
    reversed_matches = 0
    partial_matches = 0
    for truth_order in truth_orders:
        truth_set = set(truth_order)
        for hyp_order in hyp_orders:
            if set(hyp_order) == truth_set:
                if tuple(hyp_order) == tuple(truth_order):
                    paired_matches += 1
                elif tuple(hyp_order) == tuple(reversed(truth_order)):
                    reversed_matches += 1
                break
        if any(set(hyp_order) & truth_set for hyp_order in hyp_orders):
            partial_matches += 1

    actual_pairs = sum(len(h.member_nodes) for h in hypotheses)
    matching_pairs = 0
    for hyp in hypotheses:
        matching_pairs += max((len(set(hyp.member_nodes) & truth_set) for truth_set in truth_sets), default=0)
    expected_bits = sum(len(s) for s in truth_sets)
    membership_precision = matching_pairs / max(1, actual_pairs)
    membership_recall = matching_pairs / max(1, expected_bits)

    truth_role_by_node = {
        node: row.role
        for row in truth
        for node in row.member_signal_names
        if node in scalar_nodes
    }
    pred_role_by_node = {
        node: hyp.role
        for hyp in hypotheses
        for node in hyp.member_nodes
    }
    control_nodes = [n for n, role in truth_role_by_node.items() if role in {"control", "selector"}]
    data_nodes = [n for n, role in truth_role_by_node.items() if role == "data_operand"]
    output_nodes = [n for n, role in truth_role_by_node.items() if role == "output"]
    control_acc = sum(1 for n in control_nodes if pred_role_by_node.get(n) in {"control", "selector"}) / max(1, len(control_nodes))
    data_acc = sum(1 for n in data_nodes if pred_role_by_node.get(n) == "data_operand") / max(1, len(data_nodes))
    output_acc = sum(1 for n in output_nodes if pred_role_by_node.get(n) == "output") / max(1, len(output_nodes))

    return {
        "region_id": region_row["region_id"],
        "case_id": region_row["case_id"],
        "optimization": region_row["optimization"],
        "source_type": region_row["source_type"],
        "inference_mode": hypotheses[0].inference_mode if hypotheses else "inferred_bus_mode",
        "feature_mode": feature_mode,
        "direction": direction,
        "ground_truth_bus_count": str(len(truth_sets)),
        "hypothesis_count": str(len(hypotheses)),
        "top_1_bus_match": str(any(rank <= 1 for rank in top_matches)).lower(),
        "top_3_bus_match": str(any(rank <= 3 for rank in top_matches)).lower(),
        "top_5_bus_match": str(any(rank <= 5 for rank in top_matches)).lower(),
        "exact_bus_partition_match": str(exact_partition()).lower(),
        "exact_ordered_bus_match": str(paired_matches == len(truth_orders) and len(hyp_orders) == len(truth_orders)).lower(),
        "bus_membership_precision": f"{membership_precision:.6f}",
        "bus_membership_recall": f"{membership_recall:.6f}",
        "bit_order_accuracy": f"{paired_matches / max(1, len(truth_orders)):.6f}",
        "reversed_order_rate": f"{reversed_matches / max(1, len(truth_orders)):.6f}",
        "control_input_accuracy": f"{control_acc:.6f}",
        "data_operand_accuracy": f"{data_acc:.6f}",
        "output_bus_accuracy": f"{output_acc:.6f}",
        "mean_ground_truth_rank": f"{(sum(top_matches) / max(1, len(top_matches))):.6f}" if top_matches else "0.000000",
        "mrr": f"{(sum(reciprocal) / max(1, len(truth_sets))):.6f}",
    }


def bit_order_rows(
    *,
    region_row: dict[str, str],
    direction: str,
    hypotheses: list[BusHypothesis],
    bus_rows: list[BusGroundTruth],
    scalar_nodes: tuple[str, ...],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for truth in [row for row in bus_rows if row.direction == direction]:
        truth_order = tuple(node for node in truth.member_signal_names if node in set(scalar_nodes))
        if not truth_order:
            continue
        best = max(hypotheses, key=lambda h: (len(set(h.member_nodes) & set(truth_order)), h.grouping_score), default=None)
        if not best:
            continue
        unordered = set(best.member_nodes) == set(truth_order)
        exact = best.ordered_member_nodes == truth_order
        reversed_order = best.ordered_member_nodes == tuple(reversed(truth_order))
        partial = bool(set(best.member_nodes) & set(truth_order))
        rows.append(
            {
                "region_id": region_row["region_id"],
                "case_id": region_row["case_id"],
                "optimization": region_row["optimization"],
                "source_type": region_row["source_type"],
                "direction": direction,
                "bus_hypothesis_id": best.bus_hypothesis_id,
                "ground_truth_bus_name": truth.bus_name,
                "exact_ordered_bus_match": str(exact).lower(),
                "unordered_bus_membership_match": str(unordered).lower(),
                "reversed_order_match": str(reversed_order).lower(),
                "partial_match": str(partial).lower(),
                "ordering_method": "name_index" if best.bit_order != "unknown" else "canonical_fallback",
                "ordering_score": f"{best.ordering_score:.6f}",
                "ordering_ambiguity": str(best.ambiguity_count),
            }
        )
    return rows


def annotate_ground_truth_matches(hypotheses: list[BusHypothesis], bus_rows: list[BusGroundTruth]) -> list[BusHypothesis]:
    by_direction = defaultdict(list)
    for row in bus_rows:
        by_direction[row.direction].append(row)
    annotated: list[BusHypothesis] = []
    for hyp in hypotheses:
        hyp_set = set(hyp.member_nodes)
        gt_name = ""
        match = "none"
        for row in by_direction[hyp.direction]:
            truth_set = set(row.member_signal_names)
            if hyp_set == truth_set:
                gt_name = row.bus_name
                match = "exact"
                break
            if hyp_set & truth_set and not gt_name:
                gt_name = row.bus_name
                match = "partial"
        annotated.append(
            BusHypothesis(
                **{
                    **asdict(hyp),
                    "ground_truth_bus_name_if_known": gt_name,
                    "ground_truth_match": match,
                }
            )
        )
    return annotated


def aggregate_metrics(rows: list[dict[str, str]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(float(row[field]) for row in rows) / len(rows)
