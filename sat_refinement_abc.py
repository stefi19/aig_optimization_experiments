"""
sat_refinement_abc.py

Uses Berkeley ABC as a formal equivalence-checking backend to verify the
high-confidence node-level candidates produced by select_sat_candidates.py.

This is still a prototype. It does NOT implement a SAT solver from scratch —
it shells out to the `abc` binary and parses its output. Some candidates will be
marked inconclusive if the circuit cannot be prepared for ABC's CEC command.

Fingerprint-based fallback recovery
------------------------------------
ABC renames internal nodes during optimization, so a node name present in
results/top_candidates.csv may not exist in the BLIF file that ABC wrote.
When a node name is not found, sat_refinement_abc.py now attempts a conservative
fallback:

  1. Look up the candidate's fingerprint in results/node_fingerprints.csv.
  2. Scan the target BLIF for nodes whose fingerprints match.
  3. If exactly ONE match exists, use that node name instead.
  4. If zero or ≥ 2 matches exist, leave the candidate inconclusive.

This is intentionally conservative: a single unambiguous fingerprint match is
the only case where automatic recovery is safe.

Each result row carries a ``recovery_method`` column:
  direct        — the original node name was found without any fallback
  fingerprint   — the node was recovered via a unique fingerprint match
  inconclusive  — could not be completed (missing file, ambiguous/no fingerprint, timeout…)

Pipeline position:
  analyze_blif_matches.py
      → results/top_candidates.csv
      → results/node_fingerprints.csv
  sat_refinement_placeholder.py  (now: select_sat_candidates.py)
      → results/sat_refinement_candidates.csv
  sat_refinement_abc.py  (this script)
      → results/sat_verified_candidates.csv

Usage:
  python3 sat_refinement_abc.py

If `abc` is not on PATH, set the ABC environment variable:
  ABC=/path/to/abc python3 sat_refinement_abc.py
"""

import os
import sys
import csv
import shutil
import tempfile
import subprocess
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_CSV          = os.path.join("results", "sat_refinement_candidates.csv")
OUTPUT_CSV         = os.path.join("results", "sat_verified_candidates.csv")
FINGERPRINT_CSV    = os.path.join("results", "node_fingerprints.csv")

# Columns written to the output CSV
OUT_COLS = [
    "benchmark", "optimization",
    "optimized_node", "original_candidate",
    "combined_score",
    "is_exact_signature_match",  # 1 if already an exact Boolean match, 0 otherwise
    "match_category",            # "exact_anchor" | "non_exact_candidate"
    "sat_status",        # verified | rejected | inconclusive
    "abc_result",        # raw summary line from ABC
    "recovery_method",   # direct | fingerprint | inconclusive
    "notes",
]

# Timeout per ABC call (seconds).
ABC_TIMEOUT = 30


# ── ABC binary discovery ───────────────────────────────────────────────────────

def find_abc() -> str:
    """
    Return the path to the ABC binary.

    Search order:
      1. $ABC environment variable
      2. 'abc' on PATH (via shutil.which)

    Raises RuntimeError if not found.
    """
    from_env = os.environ.get("ABC", "").strip()
    if from_env and os.path.isfile(from_env) and os.access(from_env, os.X_OK):
        return from_env

    on_path = shutil.which("abc")
    if on_path:
        return on_path

    raise RuntimeError(
        "ABC binary not found.\n"
        "Either put `abc` on your PATH, or set the ABC environment variable:\n"
        "  ABC=/path/to/abc python3 sat_refinement_abc.py\n"
        "You can build ABC from: https://github.com/berkeley-abc/abc"
    )


# ── Fingerprint index ─────────────────────────────────────────────────────────

def load_fingerprint_index(csv_path: str) -> dict[tuple[str, str], dict[str, list[str]]]:
    """
    Load ``results/node_fingerprints.csv`` and build a two-level lookup:

        index[(benchmark, optimization)][fingerprint] = [node_name, ...]

    The inner list contains every node in that (benchmark, optimization) variant
    that carries the given fingerprint.  For a conservative fallback we only act
    when the list has exactly one entry.

    Returns an empty dict if the file does not exist or cannot be parsed, so the
    caller can continue without fingerprint recovery rather than crashing.
    """
    index: dict[tuple[str, str], dict[str, list[str]]] = {}

    if not os.path.exists(csv_path):
        return index

    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = (row["benchmark"], row["optimization"])
                fp  = row["fingerprint"]
                node = row["node"]
                if not fp or not node:
                    continue
                inner = index.setdefault(key, {})
                inner.setdefault(fp, []).append(node)
    except Exception:
        # Corrupt or partial file — degrade gracefully, don't crash.
        pass

    return index


def resolve_node_via_fingerprint(
    index: dict[tuple[str, str], dict[str, list[str]]],
    benchmark: str,
    optimization: str,
    candidate_fingerprint: str,
) -> str | None:
    """
    Return the unique node name that matches ``candidate_fingerprint`` for
    (benchmark, optimization), or ``None`` if no unambiguous match exists.

    'Unambiguous' means the fingerprint maps to exactly one node name in that
    variant.  Zero matches → None (fingerprint not present).
    Two-or-more matches → None (too ambiguous to recover safely).
    """
    if not candidate_fingerprint:
        return None

    inner = index.get((benchmark, optimization), {})
    names = inner.get(candidate_fingerprint, [])
    return names[0] if len(names) == 1 else None


# ── BLIF node exposure ────────────────────────────────────────────────────────

def expose_node_as_output(src_blif: str, node_name: str, dst_path: str) -> None:
    """
    Write a copy of src_blif where the .outputs line is replaced by a single
    entry: `node_name`.

    This lets ABC load the circuit and treat `node_name` as the sole primary
    output, so CEC checks only that node's function.

    The .inputs and all .names lines are kept unchanged so ABC can compute the
    transitive fanin correctly. Unused nodes are harmless — ABC ignores them.

    Raises ValueError if `node_name` is not defined by any .names statement
    in the source BLIF (catches typos early).
    """
    with open(src_blif) as fh:
        lines = fh.readlines()

    # Verify the node actually exists in this BLIF.
    defined_names = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".names"):
            parts = stripped.split()
            if len(parts) >= 2:
                defined_names.add(parts[-1])  # last token is the output name

    # Also count primary inputs as defined (they don't have .names lines).
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".inputs"):
            defined_names.update(stripped.split()[1:])

    if node_name not in defined_names:
        raise ValueError(
            f"Node '{node_name}' not found in {src_blif}. "
            f"Defined names: {sorted(defined_names)}"
        )

    out_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".outputs"):
            # Replace whatever was here with just our target node.
            out_lines.append(f".outputs {node_name}\n")
        else:
            out_lines.append(line)

    with open(dst_path, "w") as fh:
        fh.writelines(out_lines)


# ── ABC CEC runner ─────────────────────────────────────────────────────────────

def run_abc_cec(abc_bin: str, file_a: str, file_b: str) -> tuple[str, str]:
    """
    Run ABC's combinational equivalence check between file_a (loaded with
    read_blif) and file_b (checked with cec).

    Returns (status, raw_output) where status is one of:
      'verified'     — ABC says networks are equivalent
      'rejected'     — ABC says networks are NOT equivalent
      'inconclusive' — ABC errored, timed out, or gave unexpected output

    raw_output is the trimmed stdout from ABC (useful for debugging).
    """
    abc_script = f"read_blif {file_a}\ncec {file_b}\n"

    try:
        result = subprocess.run(
            [abc_bin],
            input=abc_script,
            capture_output=True,
            text=True,
            timeout=ABC_TIMEOUT,
        )
        combined = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "inconclusive", f"ABC timed out after {ABC_TIMEOUT}s"
    except Exception as exc:
        return "inconclusive", f"subprocess error: {exc}"

    return parse_cec_output(combined), combined.strip()


def parse_cec_output(output: str) -> str:
    """
    Parse ABC's stdout to extract a CEC verdict.

    ABC prints one of:
      "Networks are equivalent ..."
      "Networks are NOT EQUIVALENT."
    """
    lower = output.lower()
    if "networks are equivalent" in lower and "not equivalent" not in lower:
        return "verified"
    if "not equivalent" in lower:
        return "rejected"
    return "inconclusive"


# ── Per-candidate check ───────────────────────────────────────────────────────

def check_candidate(abc_bin: str, row: dict, fp_index: dict | None = None) -> dict:
    """
    Run a full equivalence check for one candidate row.

    Parameters
    ----------
    abc_bin
        Path to the ABC binary.
    row
        One row from sat_refinement_candidates.csv as a plain dict.  Expected
        keys: benchmark, optimization, optimized_node, original_candidate,
        combined_score, orig_blif, opt_blif, and optionally
        original_fingerprint / optimized_fingerprint.
    fp_index
        Pre-built fingerprint index from load_fingerprint_index().  Pass None
        (or omit) to skip fingerprint-based recovery entirely.

    Returns a result dict with the columns defined in OUT_COLS.
    Catches all exceptions so a single bad candidate never stops the loop.

    recovery_method values
    ----------------------
    direct        — the original node name was present in the BLIF; no fallback needed
    fingerprint   — the original name was missing; recovered via unique fingerprint
    inconclusive  — node could not be resolved (missing/ambiguous fingerprint,
                    missing file, ABC timeout, etc.)
    """
    base = {
        "benchmark":                row["benchmark"],
        "optimization":             row["optimization"],
        "optimized_node":           row["optimized_node"],
        "original_candidate":       row["original_candidate"],
        "combined_score":           row["combined_score"],
        # pass through exact-match metadata from select_sat_candidates.py
        "is_exact_signature_match": int(row.get("is_exact_signature_match", 0)),
        "match_category":           row.get("match_category", "non_exact_candidate"),
        "sat_status":               "inconclusive",
        "abc_result":               "",
        "recovery_method":          "inconclusive",
        "notes":                    "",
    }

    orig_blif = row["orig_blif"]
    opt_blif  = row["opt_blif"]
    orig_node = row["original_candidate"]
    opt_node  = row["optimized_node"]

    # Both BLIF files must exist.
    for path in (orig_blif, opt_blif):
        if not os.path.exists(path):
            base["notes"] = f"BLIF file not found: {path}"
            return base

    # Create temporary BLIF files with the target node exposed as output.
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_orig = os.path.join(tmpdir, "orig_exposed.blif")
            tmp_opt  = os.path.join(tmpdir, "opt_exposed.blif")

            # ── original node ────────────────────────────────────────────────
            orig_recovery = "direct"
            try:
                expose_node_as_output(orig_blif, orig_node, tmp_orig)
            except ValueError:
                # Direct name not found — try fingerprint fallback.
                recovered = None
                if fp_index is not None:
                    orig_fp = row.get("original_fingerprint", "")
                    bench   = row["benchmark"]
                    # The original variant lives under optimization "original".
                    recovered = resolve_node_via_fingerprint(
                        fp_index, bench, "original", orig_fp
                    )

                if recovered is None:
                    base["notes"] = (
                        f"original node '{orig_node}' not in BLIF and "
                        "fingerprint recovery found no unique match"
                    )
                    return base

                try:
                    expose_node_as_output(orig_blif, recovered, tmp_orig)
                    orig_recovery = "fingerprint"
                    base["notes"] = (
                        f"original: '{orig_node}' → '{recovered}' via fingerprint"
                    )
                except ValueError as exc2:
                    base["notes"] = (
                        f"fingerprint-recovered original '{recovered}' "
                        f"also not in BLIF: {exc2}"
                    )
                    return base

            # ── optimized node ───────────────────────────────────────────────
            opt_recovery = "direct"
            try:
                expose_node_as_output(opt_blif, opt_node, tmp_opt)
            except ValueError:
                # Direct name not found — try fingerprint fallback.
                recovered_opt = None
                if fp_index is not None:
                    opt_fp  = row.get("optimized_fingerprint", "")
                    bench   = row["benchmark"]
                    opt_key = row["optimization"]
                    recovered_opt = resolve_node_via_fingerprint(
                        fp_index, bench, opt_key, opt_fp
                    )

                if recovered_opt is None:
                    base["notes"] = (
                        f"optimized node '{opt_node}' not in BLIF and "
                        "fingerprint recovery found no unique match"
                    )
                    return base

                try:
                    expose_node_as_output(opt_blif, recovered_opt, tmp_opt)
                    opt_recovery = "fingerprint"
                    prev = base["notes"]
                    base["notes"] = (
                        (prev + "; " if prev else "")
                        + f"optimized: '{opt_node}' → '{recovered_opt}' via fingerprint"
                    )
                except ValueError as exc2:
                    base["notes"] = (
                        f"fingerprint-recovered optimized '{recovered_opt}' "
                        f"also not in BLIF: {exc2}"
                    )
                    return base

            # ── run ABC CEC ──────────────────────────────────────────────────
            status, raw = run_abc_cec(abc_bin, tmp_orig, tmp_opt)

        summary_line = _extract_summary_line(raw)
        base["sat_status"] = status
        base["abc_result"] = summary_line

        # recovery_method: "fingerprint" if either side needed it, else "direct"
        if orig_recovery == "fingerprint" or opt_recovery == "fingerprint":
            base["recovery_method"] = "fingerprint"
        else:
            base["recovery_method"] = "direct"

        if status == "inconclusive":
            useful = _find_useful_error_line(raw)
            # Preserve any note from fingerprint recovery; append ABC error.
            abc_note = useful if useful else raw.strip()[:150]
            if base["notes"]:
                base["notes"] = base["notes"] + f"; abc: {abc_note}"
            else:
                base["notes"] = abc_note

    except Exception as exc:
        base["notes"] = f"unexpected error: {exc}"

    return base


def _extract_summary_line(raw: str) -> str:
    """Pull the most informative single line from ABC's output."""
    for line in raw.splitlines():
        low = line.lower()
        if "equivalent" in low or "not equivalent" in low:
            return line.strip()
    # Fall back to last non-empty line that isn't the ABC banner.
    for line in reversed(raw.splitlines()):
        stripped = line.strip()
        if stripped and "UC Berkeley" not in stripped and "====" not in stripped:
            return stripped
    return raw.strip()[:120]


def _find_useful_error_line(raw: str) -> str:
    """Return the most descriptive error line from ABC output, skipping banner lines."""
    skip_prefixes = ("UC Berkeley", "=====", "source -s", "***EOF***", "read_blif", "cec ")
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in skip_prefixes):
            continue
        return stripped
    return ""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Locate ABC.
    try:
        abc_bin = find_abc()
        print(f"Using ABC: {abc_bin}")
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Load the candidate list.
    if not os.path.exists(INPUT_CSV):
        print(
            f"ERROR: {INPUT_CSV} not found.\n"
            "Run select_sat_candidates.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} candidates from {INPUT_CSV}")

    # Load the fingerprint index for conservative fallback recovery.
    fp_index = load_fingerprint_index(FINGERPRINT_CSV)
    if fp_index:
        total_fps = sum(len(inner) for inner in fp_index.values())
        print(f"Loaded fingerprint index: {total_fps} fingerprint entries")
    else:
        print(
            f"Note: {FINGERPRINT_CSV} not found or empty — "
            "fingerprint-based node recovery disabled.\n"
            "  Run analyze_blif_matches.py to generate it."
        )

    # Run equivalence check for each candidate.
    results = []
    for i, row in df.iterrows():
        label = (
            f"  [{i+1}/{len(df)}] "
            f"{row['benchmark']}/{row['optimization']} "
            f"{row['optimized_node']} ↔ {row['original_candidate']}"
        )
        print(label, end=" ... ", flush=True)

        result = check_candidate(abc_bin, row.to_dict(), fp_index=fp_index)
        results.append(result)

        status = result["sat_status"]
        method = result["recovery_method"]
        method_tag = f" [{method}]" if method != "direct" else ""
        note = f"  ({result['notes'][:60]})" if result["notes"] else ""
        print(f"{status}{method_tag}{note}")

    # Write output CSV.
    out_df = pd.DataFrame(results, columns=OUT_COLS)
    os.makedirs("results", exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(out_df)} rows to {OUTPUT_CSV}")

    # Print a short summary broken down by recovery_method.
    counts        = out_df["sat_status"].value_counts()
    method_counts = out_df["recovery_method"].value_counts()

    print("\nSummary by sat_status:")
    for status in ("verified", "rejected", "inconclusive"):
        n = counts.get(status, 0)
        print(f"  {status:15s}: {n}")

    print("\nSummary by recovery_method:")
    direct_n      = int(method_counts.get("direct",      0))
    fp_n          = int(method_counts.get("fingerprint", 0))
    inconc_n      = int(method_counts.get("inconclusive", 0))
    print(f"  {'direct':15s}: {direct_n}")
    print(f"  {'fingerprint':15s}: {fp_n}")
    print(f"  {'inconclusive':15s}: {inconc_n}")

    print(
        "\nNOTE: 'verified' means ABC found the two exposed nodes to be "
        "combinationally equivalent.\n"
        "'rejected' means ABC found a counterexample — the nodes are NOT equivalent.\n"
        "'inconclusive' means the check could not be completed (missing file, "
        "node not found, timeout, etc.).\n"
        "recovery_method='fingerprint' means the node name was missing from the BLIF\n"
        "but was recovered via a unique SHA-256 fingerprint match.\n"
        "This is still a prototype — fingerprint recovery only triggers when exactly\n"
        "one node in the variant matches the candidate's fingerprint."
    )


if __name__ == "__main__":
    main()
