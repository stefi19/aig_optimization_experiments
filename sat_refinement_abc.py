"""
sat_refinement_abc.py

Uses Berkeley ABC as a formal equivalence-checking backend to verify the
high-confidence node-level candidates produced by sat_refinement_placeholder.py.

This is still a prototype. It does NOT implement a SAT solver from scratch —
it shells out to the `abc` binary and parses its output. Some candidates will be
marked inconclusive if the circuit cannot be prepared for ABC's CEC command.

Pipeline position:
  analyze_blif_matches.py
      → results/top_candidates.csv
  sat_refinement_placeholder.py
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
import shutil
import tempfile
import subprocess
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_CSV  = os.path.join("results", "sat_refinement_candidates.csv")
OUTPUT_CSV = os.path.join("results", "sat_verified_candidates.csv")

# Columns written to the output CSV
OUT_COLS = [
    "benchmark", "optimization",
    "optimized_node", "original_candidate",
    "combined_score",
    "sat_status",   # verified | rejected | inconclusive
    "abc_result",   # raw summary line from ABC
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

def check_candidate(abc_bin: str, row: dict) -> dict:
    """
    Run a full equivalence check for one candidate row.

    Returns a result dict with the columns defined in OUT_COLS.
    Catches all exceptions so a single bad candidate never stops the loop.
    """
    base = {
        "benchmark":          row["benchmark"],
        "optimization":       row["optimization"],
        "optimized_node":     row["optimized_node"],
        "original_candidate": row["original_candidate"],
        "combined_score":     row["combined_score"],
        "sat_status":         "inconclusive",
        "abc_result":         "",
        "notes":              "",
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

            try:
                expose_node_as_output(orig_blif, orig_node, tmp_orig)
            except ValueError as exc:
                base["notes"] = f"expose original failed: {exc}"
                return base

            try:
                expose_node_as_output(opt_blif, opt_node, tmp_opt)
            except ValueError as exc:
                base["notes"] = f"expose optimized failed: {exc}"
                return base

            status, raw = run_abc_cec(abc_bin, tmp_orig, tmp_opt)

        # Extract a short summary line from ABC's raw output.
        summary_line = _extract_summary_line(raw)

        base["sat_status"] = status
        base["abc_result"] = summary_line
        # For inconclusive: store a clean explanation, not the full ABC header spam.
        if status == "inconclusive":
            # Look for the most useful line in the raw output.
            useful = _find_useful_error_line(raw)
            base["notes"] = useful if useful else raw.strip()[:150]

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
            "Run sat_refinement_placeholder.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} candidates from {INPUT_CSV}")

    # Run equivalence check for each candidate.
    results = []
    for i, row in df.iterrows():
        label = (
            f"  [{i+1}/{len(df)}] "
            f"{row['benchmark']}/{row['optimization']} "
            f"{row['optimized_node']} ↔ {row['original_candidate']}"
        )
        print(label, end=" ... ", flush=True)

        result = check_candidate(abc_bin, row.to_dict())
        results.append(result)

        status = result["sat_status"]
        note   = f"  ({result['notes'][:60]})" if result["notes"] else ""
        print(f"{status}{note}")

    # Write output CSV.
    out_df = pd.DataFrame(results, columns=OUT_COLS)
    os.makedirs("results", exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nWrote {len(out_df)} rows to {OUTPUT_CSV}")

    # Print a short summary.
    counts = out_df["sat_status"].value_counts()
    print("\nSummary:")
    for status in ("verified", "rejected", "inconclusive"):
        n = counts.get(status, 0)
        print(f"  {status:15s}: {n}")

    print(
        "\nNOTE: 'verified' means ABC found the two exposed nodes to be "
        "combinationally equivalent.\n"
        "'rejected' means ABC found a counterexample — the nodes are NOT equivalent.\n"
        "'inconclusive' means the check could not be completed (missing file, "
        "node not found, timeout, etc.).\n"
        "This is still a prototype — node names between original and optimized BLIFs "
        "may differ, which can cause some checks to be inconclusive."
    )


if __name__ == "__main__":
    main()
