import math
import random

from analyze_blif_matches import BlifNetwork, eval_cover, combined_candidate_score
from contextual_error_metrics import evaluate_network, output_metrics, substitute_candidate


SCHEMA = "formal_approximate_correspondence_v1"


def interval(hits, count, alpha=0.05):
    if count <= 0 or hits < 0 or hits > count or not 0 < alpha < 1:
        raise ValueError("invalid binomial observations")
    epsilon = math.sqrt(math.log(2 / alpha) / (2 * count))
    mean = hits / count
    return max(0.0, mean - epsilon), min(1.0, mean + epsilon)


def aligned(source, optimized):
    if len(set(source.inputs)) != len(source.inputs) or len(set(optimized.inputs)) != len(optimized.inputs) or set(source.inputs) != set(optimized.inputs):
        raise ValueError("primary inputs must be unique and aligned by name")
    if source.outputs != optimized.outputs:
        raise ValueError("primary outputs must be explicitly aligned")
    return BlifNetwork(list(optimized.inputs), list(source.outputs), list(source.nodes))


def measured_pair(source, optimized, target, candidate, patterns, invert=False):
    source = aligned(source, optimized)
    if target in optimized.outputs or target in optimized.inputs:
        raise ValueError("substitution target must be internal")
    substitution = substitute_candidate(optimized, source, target, candidate, invert=invert)
    if substitution.status != "ok":
        raise ValueError(substitution.reason)
    baseline = evaluate_network(optimized, patterns)
    old = evaluate_network(source, patterns)
    new = evaluate_network(substitution.network, patterns)
    toggled = dict(patterns.values)
    for node in optimized.nodes:
        if node.output == target:
            toggled[target] = baseline[target] ^ patterns.mask
        else:
            toggled[node.output] = eval_cover(node, toggled, patterns.mask)
    observation_bits = 0
    error_bits = 0
    for y in optimized.outputs:
        observation_bits |= baseline[y] ^ toggled[y]
        error_bits |= baseline[y] ^ new[y]
    diff = baseline[target] ^ old[candidate] ^ (patterns.mask if invert else 0)
    if error_bits != (diff & observation_bits):
        raise AssertionError("invalid substitution/observability identity")
    metrics = output_metrics([baseline[y] for y in optimized.outputs], [new[y] for y in optimized.outputs], patterns.pattern_count)
    n = patterns.pattern_count
    d = diff.bit_count() / n
    lo, hi = (d, d) if patterns.mode == "exact" else interval(diff.bit_count(), n)
    return dict(distance=d, complement_distance=min(d, 1-d), contextual_error=error_bits.bit_count()/n,
                observability=observation_bits.bit_count()/n,
                conditional_observability=error_bits.bit_count()/diff.bit_count() if diff else 0.0,
                output_hamming=metrics.mean_output_hamming_distance,
                mae=metrics.mean_absolute_output_error, wce=metrics.worst_case_absolute_output_error,
                worst_hamming=metrics.worst_case_output_hamming_distance,
                distance_lower=lo, distance_upper=hi, mode=patterns.mode, patterns=n), substitution.network


def sampled_order(proposals, target_vector, seed, samples):
    if samples <= 0 or not target_vector:
        raise ValueError("nonempty sampling domain required")
    rng = random.Random(seed)
    indices = [rng.randrange(len(target_vector)) for _ in range(samples)]
    return sorted(proposals, key=lambda item: (sum(item["vector"][i] != target_vector[i] for i in indices), item["ordinal"]))


def rank_candidates(rows, method):
    def key(row):
        d = row["distance"]
        dc = row["complement_distance"]
        structural = row["structural_score"]
        locality = 1 - row["support_overlap"]
        contextual = row["best_contextual_error"]
        if method == "structural":
            return (-structural,)
        if method == "fingerprint":
            return (-combined_candidate_score(1-d, row["support_overlap"], row["depth_score"]),)
        if method == "sat_only":
            return (row["global_status"] != "unsat", -structural)
        if method == "global":
            return (d, -structural)
        if method == "complement":
            return (dc, -structural)
        if method == "contextual":
            return (contextual, dc, -structural)
        if method in {"hybrid", "no_global", "no_context", "no_complement", "no_observability", "no_structure", "no_locality", "no_formal"}:
            score = (row["contextual_error"] if method == "no_complement" else contextual) if method != "no_context" else 0
            score += 0.35*(d if method == "no_complement" else dc) if method != "no_global" else 0
            score += 0.10*(row["conditional_observability"] if method == "no_complement" else row["best_conditional_observability"]) if method != "no_observability" else 0
            score += 0.10*locality if method != "no_locality" else 0
            score -= 0.05*structural if method != "no_structure" else 0
            return (score,)
        raise ValueError(method)
    return sorted(rows, key=lambda row: (*key(row), row["candidate"]))
