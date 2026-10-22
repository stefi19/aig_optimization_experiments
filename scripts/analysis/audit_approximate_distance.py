import csv
import hashlib
import json
import subprocess
from pathlib import Path

from analyze_blif_matches import BlifNode, eval_cover, parse_blif
from scripts.analysis.approximate_node_distance import exact_pattern_values, sampled_pattern_values, structural_supports
from sat_refinement_abc import expose_node_as_output
from scripts.validation.approximate_oracle import scalar_values

ROOT = Path(__file__).resolve().parents[2]
FLOWS = dict(original="strash", balance="strash; balance", rewrite="strash; rewrite", refactor="strash; refactor",
             resub="strash; resub", rewrite_z="strash; rewrite -z", refactor_z="strash; refactor -z",
             resyn="strash; balance; rewrite; rewrite -z; balance; rewrite; balance",
             resyn2="strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
             resyn2_like="strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance",
             dc2="strash; dc2", compress2rs="strash; balance; rewrite; refactor; resub; balance; rewrite -z; refactor -z; resub; balance")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["status"])
        writer.writeheader()
        writer.writerows(rows)


def abc_call(abc, commands, log, timeout=30):
    try:
        proc = subprocess.run([str(abc), "-q", commands], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        output = proc.stdout + proc.stderr
        status = "equivalent" if proc.returncode == 0 and "Networks are equivalent" in output and "not equivalent" not in output.lower() else "disproved" if "not equivalent" in output.lower() else "unknown"
    except subprocess.TimeoutExpired:
        output, status = "timeout", "timeout"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output)
    return status


def evaluate(net, patterns, mask, legacy=False):
    values = dict(patterns)
    for node in net.nodes:
        if legacy and node.inputs:
            node = BlifNode(node.output, node.inputs, [r for r in node.cover if len(r.split()) == 1 or r.split()[1] == "1"])
        values[node.output] = eval_cover(node, values, mask)
    return values


def audit(out, abc, per_stratum=8):
    out.mkdir(parents=True, exist_ok=True)
    historical = []
    for mode in ("exact", "sampled"):
        historical.extend(csv.DictReader((ROOT / f"results/approximate_distance_{mode}.csv").open()))
    selected = []
    for mode in ("exact", "sampled"):
        for status in ("verified", "rejected"):
            subset = [r for r in historical if r["distance_mode"] == mode and r["sat_status"] == status]
            selected.extend(subset[:per_stratum])
    nets = {}
    rows = []
    for i, old in enumerate(selected):
        benchmark, flow = old["benchmark"], old["optimization"]
        paths = []
        for variant in ("original", flow):
            key = (benchmark, variant)
            if key not in nets:
                path = out / f"{benchmark}_{variant}.blif"
                source = f"benchmarks/external/iscas85/{benchmark.removeprefix('external_iscas85_')}.blif"
                abc_call(abc, f"read_blif {source}; {FLOWS[variant]}; write_blif {path.relative_to(ROOT)}", out / f"{benchmark}_{variant}.log")
                if not path.exists():
                    raise RuntimeError("ABC failed to regenerate audit netlist")
                nets[key] = (path, parse_blif(path))
            paths.append(nets[key])
        (a, source), (b, optimized) = paths
        u = set(structural_supports(a)[old["original_candidate"]]) | set(structural_supports(b)[old["optimized_node"]])
        seed_key = f"{benchmark}|{flow}|{old['original_candidate']}|{old['optimized_node']}"
        inputs = sorted(source.inputs)
        p, mask, n = exact_pattern_values(inputs, u) if old["distance_mode"] == "exact" else sampled_pattern_values(inputs, u, int(old["pattern_count"]), seed_key)
        targets = (old["original_candidate"], old["optimized_node"])
        distances = []
        for legacy in (True, False):
            av, bv = evaluate(source, p, mask, legacy), evaluate(optimized, p, mask, legacy)
            distances.append((av[targets[0]] ^ bv[targets[1]]).bit_count() / n)
        hits = 0
        for j in range(n):
            assignment = {k: (v >> j) & 1 for k, v in p.items()}
            hits += scalar_values(source, assignment, [targets[0]])[targets[0]] != scalar_values(optimized, assignment, [targets[1]])[targets[1]]
        exposed = []
        for label, path, target in zip(("source", "optimized"), (a,b), targets):
            exposed_path = out / f"row_{i}_{label}.blif"
            expose_node_as_output(str(path), target, str(exposed_path))
            exposed.append(str(exposed_path.relative_to(ROOT)))
        cec = abc_call(abc, f"cec {' '.join(exposed)}", out / f"row_{i}_cec.log")
        rows.append(dict(benchmark=benchmark, optimization=flow, original_candidate=targets[0], optimized_node=targets[1],
                         historical_status=old["sat_status"], mode=old["distance_mode"], historical_distance=float(old["distance"]),
                         legacy_replay_distance=distances[0], corrected_distance=distances[1], independent_oracle_distance=hits/n,
                         pattern_count=n, fresh_cec=cec, pi_alignment=source.inputs == optimized.inputs,
                         source_path=str(a.relative_to(ROOT)), optimized_path=str(b.relative_to(ROOT)), source_sha256=sha(a), optimized_sha256=sha(b),
                         caveat="regenerated_pair_historical_variant_hash_unavailable"))
    write_csv(out / "replay.csv", rows)
    inputs = [ROOT / f"results/approximate_distance_{m}.csv" for m in ("exact", "sampled")]
    (out / "historical_inputs.json").write_text(json.dumps({str(p.relative_to(ROOT)): sha(p) for p in inputs}, indent=2)+"\n")
    return rows
