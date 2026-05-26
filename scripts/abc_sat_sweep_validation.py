"""
scripts/abc_sat_sweep_validation.py

ABC-native SAT sweeping / FRAIG validation for a single BLIF pair.

The mentor's suggestion was to reuse ABC's own SAT sweeping / FRAIG
machinery instead of re-implementing simulation externally in Python.
ABC already contains very well-optimised simulation + SAT routines, and
it would be wasteful to ignore them.

This module is the heart of the hybrid flow.  It wraps two ABC commands:

  dump_equiv  — given two BLIF files, computes formal cross-network node
                equivalence classes using simulation + SAT (FRAIG internally).
                This is exactly what we want: a provably-correct mapping
                between original and optimised nodes.

  strash + fraig + print_stats
                — runs FRAIG-based node merging on a single network and
                reports how many nodes ABC can prove redundant within
                that network alone.  Useful as a sanity / quality check.

The module is intentionally defensive: if ABC isn't found, or a command
fails, we return structured error information rather than crashing.  This
makes it easy to integrate into the wider pipeline as an optional step.

Usage as a standalone script:
    python3 scripts/abc_sat_sweep_validation.py \
        --orig   variants/majority3_original.blif \
        --opt    variants/majority3_balance.blif  \
        --abc    .abc_build/abc_repo/abc          \
        --outdir results/abc_sweep/majority3_balance
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

ABC_TIMEOUT = 60  # seconds per ABC call; dump_equiv can take longer on big circuits
ABC_CONFIDENCE_LABEL = "sat_proven"   # all matches from dump_equiv are formally proven


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EquivPair:
    """
    One cross-network equivalence: original_node in file A computes the same
    function as optimised_node in file B (possibly with complementation).

    All pairs produced by dump_equiv are formally proven by ABC's SAT engine,
    so confidence is always 'sat_proven' — no guesswork.
    """
    original_node:   str
    optimised_node:  str
    equiv_class_id:  int
    is_complement:   bool   # True if optimised_node is the Boolean complement of original_node
    confidence:      str = ABC_CONFIDENCE_LABEL


@dataclass
class FraigStats:
    """
    Node / level counts before and after ABC FRAIG on a single network.
    Useful for understanding how much internal redundancy ABC can remove.
    """
    blif_path:     str
    nodes_before:  Optional[int] = None
    levels_before: Optional[int] = None
    nodes_after:   Optional[int] = None
    levels_after:  Optional[int] = None
    raw_log:       str = ""
    error:         str = ""


@dataclass
class DumpEquivResult:
    """
    Full result from a dump_equiv run on a pair of BLIF files.
    """
    orig_blif:          str
    opt_blif:           str
    equiv_pairs:        list = field(default_factory=list)   # list[EquivPair]
    raw_log:            str  = ""
    abc_script_used:    str  = ""
    error:              str  = ""
    # Summary counts
    total_classes:      int  = 0
    cross_network_matches: int = 0


# ---------------------------------------------------------------------------
# ABC binary discovery
# ---------------------------------------------------------------------------

def find_abc(hint: Optional[str] = None) -> str:
    """
    Find the ABC binary.

    Search order:
      1. `hint` argument (e.g. from --abc-path CLI flag)
      2. $ABC environment variable
      3. 'abc' on PATH

    Raises RuntimeError with a clear message if nothing is found.
    We want the error to be obvious so users know exactly what to do.
    """
    candidates = [
        hint or "",
        os.environ.get("ABC", ""),
        shutil.which("abc") or "",
    ]
    for path in candidates:
        path = path.strip()
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    raise RuntimeError(
        "ABC binary not found.\n"
        "Provide the path with --abc-path, set the $ABC environment variable,\n"
        "or put 'abc' on your PATH.\n"
        "Build ABC from: https://github.com/berkeley-abc/abc\n"
        "  git clone https://github.com/berkeley-abc/abc\n"
        "  cd abc && make -j4"
    )


# ---------------------------------------------------------------------------
# BLIF parsing helpers
# ---------------------------------------------------------------------------

def read_internal_nodes(blif_path: str) -> set[str]:
    """
    Return all .names-defined non-input nodes from a BLIF file.

    This includes primary outputs if they are defined by a .names line, because
    dump_equiv may report output equivalences too and we want to capture those.
    Formally: returns (nodes defined by .names) minus (primary inputs).

    We need this to decide which nodes in a dump_equiv equivalence class belong
    to the original vs the optimised network.
    """
    inputs:  set[str] = set()
    outputs: set[str] = set()
    defined: set[str] = set()

    with open(blif_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith(".inputs"):
                inputs.update(line.split()[1:])
            elif line.startswith(".outputs"):
                outputs.update(line.split()[1:])
            elif line.startswith(".names"):
                parts = line.split()
                if len(parts) >= 2:
                    defined.add(parts[-1])

    # Everything that's defined but is not a primary input is an internal node.
    # (Primary outputs are still real internal nodes — they have .names definitions.)
    return defined - inputs


def expose_node_as_output(src_blif: str, node_name: str, dst_path: str) -> None:
    """
    Write a copy of src_blif where the .outputs declaration is replaced by
    a single entry: `node_name`.

    Why do we need this?  ABC's cec command checks whole-circuit equivalence
    based on primary outputs.  By promoting a single internal node to a
    primary output we can ask ABC a targeted yes/no question:
    "Do these two nodes compute the same function?"

    The approach is the same fallback that the existing sat_refinement_abc.py
    uses for per-node CEC, so we keep things consistent.

    Raises ValueError if `node_name` isn't defined in the BLIF — better to
    catch that early than get a confusing ABC error later.
    """
    with open(src_blif, encoding="utf-8") as fh:
        lines = fh.readlines()

    # Collect all defined names (including primary inputs) for validation.
    all_names: set[str] = set()
    for line in lines:
        s = line.strip()
        if s.startswith(".inputs"):
            all_names.update(s.split()[1:])
        elif s.startswith(".names"):
            parts = s.split()
            if len(parts) >= 2:
                all_names.add(parts[-1])

    if node_name not in all_names:
        raise ValueError(
            f"Node '{node_name}' is not defined in {src_blif}. "
            f"Available: {sorted(all_names)}"
        )

    out_lines = []
    for line in lines:
        if line.strip().startswith(".outputs"):
            out_lines.append(f".outputs {node_name}\n")
        else:
            out_lines.append(line)

    with open(dst_path, "w", encoding="utf-8") as fh:
        fh.writelines(out_lines)


# ---------------------------------------------------------------------------
# dump_equiv output parser
# ---------------------------------------------------------------------------

def parse_dump_equiv_file(
    equiv_file: str,
    orig_nodes: set[str],
    opt_nodes:  set[str],
) -> list[EquivPair]:
    """
    Parse the text file written by ABC's `dump_equiv` command and return a
    list of cross-network EquivPairs.

    The file format is:
        # header comment line
        <blank line>
        <class_id>:<model>:<node>
        <class_id>:<model>:<node>      ← same class, possibly from other network
        <class_id>:<model>:NOT:<node>  ← complement relationship
        <blank line>
        <class_id>:<model>:<node>
        ...

    Cross-network match detection:
    --------------------------------
    Because both BLIF files usually share the same .model name (ABC uses the
    .model directive), we can't tell which network a line came from by model
    name alone.  Instead we cross-reference with the node sets from each file:

      - If a node only exists in orig_nodes  → it's from the original network
      - If a node only exists in opt_nodes   → it's from the optimised network
      - If it exists in both                 → we use position (first occurrence
                                               = original, second = optimised)
        This position-based heuristic is safe for balanced/mild optimisations
        where names are preserved; for aggressive optimisations that rename all
        nodes the two sets don't overlap, so the unambiguous path applies.

    Only pairs where one node comes from each network are reported as matches.
    """
    # Parse all entries grouped by class_id.
    # Structure: class_entries[class_id] = list of (node_name, is_complement)
    class_entries: dict[int, list[tuple[str, bool]]] = {}

    with open(equiv_file, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            # Expected: class_id : model : [NOT :] node
            # Minimum 3 parts; "NOT" is an extra token before the node name
            if len(parts) < 3:
                continue
            try:
                class_id = int(parts[0])
            except ValueError:
                continue

            # Handle both "cls:model:node" and "cls:model:NOT:node"
            if len(parts) == 4 and parts[2] == "NOT":
                node_name    = parts[3]
                is_complement = True
            else:
                node_name     = parts[2]
                is_complement = False

            class_entries.setdefault(class_id, []).append((node_name, is_complement))

    # Now resolve which entries come from which network and build EquivPairs.
    pairs: list[EquivPair] = []

    for class_id, entries in class_entries.items():
        # Track which nodes we've already attributed to the original network
        # so a second occurrence of the same name goes to the optimised side.
        seen_in_orig: set[str] = set()
        orig_members: list[tuple[str, bool]] = []   # (node, is_complement)
        opt_members:  list[tuple[str, bool]] = []

        for node, is_comp in entries:
            only_orig = (node in orig_nodes) and (node not in opt_nodes)
            only_opt  = (node in opt_nodes)  and (node not in orig_nodes)

            if only_orig:
                orig_members.append((node, is_comp))
            elif only_opt:
                opt_members.append((node, is_comp))
            elif (node in orig_nodes) and (node in opt_nodes):
                # Same node name exists in both networks (e.g. a preserved output).
                # First occurrence goes to original, second to optimised.
                if node not in seen_in_orig:
                    orig_members.append((node, is_comp))
                    seen_in_orig.add(node)
                else:
                    opt_members.append((node, is_comp))
            else:
                # Node appears in neither BLIF — it is a synthetic/internal name
                # introduced by ABC's FRAIG merge (e.g. "const0", temp nodes).
                # We cannot safely attribute it to either network, so skip it.
                continue

        # Pair up every original member with every optimised member in this class.
        # In practice most classes have exactly one node from each network.
        for o_node, o_comp in orig_members:
            for p_node, p_comp in opt_members:
                # Complementation: the pair is complemented if exactly one of
                # the two entries has the NOT flag.
                pair_complement = o_comp ^ p_comp
                pairs.append(EquivPair(
                    original_node  = o_node,
                    optimised_node = p_node,
                    equiv_class_id = class_id,
                    is_complement  = pair_complement,
                ))

    return pairs


# ---------------------------------------------------------------------------
# ABC runner: dump_equiv
# ---------------------------------------------------------------------------

def run_dump_equiv(
    abc_bin:  str,
    orig_blif: str,
    opt_blif:  str,
    outdir:   str,
) -> DumpEquivResult:
    """
    Run ABC's `dump_equiv` command on an (original, optimised) BLIF pair.

    ABC's dump_equiv internally builds the combined miter AIG, runs
    FRAIG-style simulation + SAT to prove or disprove node equivalences,
    and writes the result to a text file.  This is the same engine that
    FRAIG uses internally — we're just asking ABC to expose the results
    at the node level instead of silently merging them.

    The ABC script is passed via stdin (not -c) so that long paths with
    spaces are handled safely by the shell.  The script is also saved as
    dump_equiv.abc in outdir for reproducibility.
    """
    os.makedirs(outdir, exist_ok=True)

    equiv_file  = os.path.join(outdir, "dump_equiv.txt")
    script_file = os.path.join(outdir, "dump_equiv.abc")
    log_file    = os.path.join(outdir, "dump_equiv.log")

    # Absolute paths avoid any cwd issues when ABC is invoked.
    orig_abs = str(Path(orig_blif).resolve())
    opt_abs  = str(Path(opt_blif).resolve())
    out_abs  = str(Path(equiv_file).resolve())

    # The ABC script: one command is enough.  We use -v for verbose output
    # so the log contains SAT stats (useful for debugging large circuits).
    abc_script = f"dump_equiv -v {orig_abs} {opt_abs} {out_abs}\n"

    # Save the script for reproducibility — the mentor asked for this.
    with open(script_file, "w") as fh:
        fh.write(abc_script)

    result = DumpEquivResult(
        orig_blif       = orig_blif,
        opt_blif        = opt_blif,
        abc_script_used = abc_script,
    )

    try:
        proc = subprocess.run(
            [abc_bin],
            input=abc_script,
            capture_output=True,
            text=True,
            timeout=ABC_TIMEOUT,
        )
        raw_log = proc.stdout + proc.stderr
        result.raw_log = raw_log.strip()

        with open(log_file, "w") as fh:
            fh.write(raw_log)

        # Check for obvious ABC-level failures.
        if "Error:" in raw_log and not os.path.exists(equiv_file):
            result.error = f"ABC reported an error; see {log_file}"
            return result

    except subprocess.TimeoutExpired:
        result.error = f"ABC timed out after {ABC_TIMEOUT}s"
        return result
    except Exception as exc:
        result.error = f"subprocess error: {exc}"
        return result

    # Parse the equivalence file.
    if not os.path.exists(equiv_file):
        result.error = f"dump_equiv file not created; see {log_file}"
        return result

    orig_nodes = read_internal_nodes(orig_blif)
    opt_nodes  = read_internal_nodes(opt_blif)

    result.equiv_pairs = parse_dump_equiv_file(equiv_file, orig_nodes, opt_nodes)
    result.total_classes       = _count_classes(equiv_file)
    result.cross_network_matches = len(result.equiv_pairs)

    return result


def _count_classes(equiv_file: str) -> int:
    """Count unique class IDs in a dump_equiv output file."""
    ids: set[int] = set()
    with open(equiv_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            try:
                ids.add(int(parts[0]))
            except (ValueError, IndexError):
                pass
    return len(ids)


# ---------------------------------------------------------------------------
# ABC runner: FRAIG stats on a single network
# ---------------------------------------------------------------------------

def run_fraig_stats(
    abc_bin:   str,
    blif_path: str,
    outdir:    str,
) -> FraigStats:
    """
    Run strash → fraig → print_stats on a single BLIF and parse the node/level
    counts before and after.

    This tells us how much internal redundancy ABC can eliminate from one
    network in isolation.  If fraig reduces a network's node count significantly,
    it means the original synthesis left redundant logic inside.

    The ABC command `print_stats` prints a line like:
        model_name  : i/o =  3/ 1  lat = 0  and = 5  lev = 3
    We parse 'and' (node count) and 'lev' (level count) from that.
    """
    os.makedirs(outdir, exist_ok=True)

    log_file    = os.path.join(outdir, "fraig_stats.log")
    script_file = os.path.join(outdir, "fraig_stats.abc")

    blif_abs = str(Path(blif_path).resolve())
    abc_script = (
        f"read_blif {blif_abs}\n"
        f"strash\n"
        f"print_stats\n"
        f"fraig\n"
        f"print_stats\n"
    )

    with open(script_file, "w") as fh:
        fh.write(abc_script)

    stats = FraigStats(blif_path=blif_path)

    try:
        proc = subprocess.run(
            [abc_bin],
            input=abc_script,
            capture_output=True,
            text=True,
            timeout=ABC_TIMEOUT,
        )
        raw = proc.stdout + proc.stderr
        stats.raw_log = raw.strip()

        with open(log_file, "w") as fh:
            fh.write(raw)

    except subprocess.TimeoutExpired:
        stats.error = f"ABC timed out after {ABC_TIMEOUT}s"
        return stats
    except Exception as exc:
        stats.error = f"subprocess error: {exc}"
        return stats

    # Parse the two print_stats lines.  ABC prints them in order: before / after.
    parsed = _parse_print_stats_lines(stats.raw_log)
    if len(parsed) >= 1:
        stats.nodes_before, stats.levels_before = parsed[0]
    if len(parsed) >= 2:
        stats.nodes_after, stats.levels_after = parsed[1]

    return stats


_PRINT_STATS_RE = re.compile(r"and\s*=\s*(\d+)\s+lev\s*=\s*(\d+)")

def _parse_print_stats_lines(text: str) -> list[tuple[int, int]]:
    """
    Extract (and_count, level_count) pairs from ABC print_stats output.
    Returns them in the order they appear in the log (before, then after fraig).
    """
    results = []
    for m in _PRINT_STATS_RE.finditer(text):
        results.append((int(m.group(1)), int(m.group(2))))
    return results


# ---------------------------------------------------------------------------
# Structured output writers
# ---------------------------------------------------------------------------

def write_equiv_csv(pairs: list[EquivPair], csv_path: str) -> None:
    """Write the list of EquivPair objects to a CSV file."""
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "equiv_class_id", "original_node", "optimised_node",
            "is_complement", "confidence",
        ])
        writer.writeheader()
        for p in pairs:
            writer.writerow(asdict(p))


def write_fraig_stats_json(stats: FraigStats, json_path: str) -> None:
    """Persist FraigStats as a JSON file (easy to load in tests/notebooks)."""
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    d = asdict(stats)
    d.pop("raw_log", None)   # keep the file small; raw log is in fraig_stats.log
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(d, fp=fh, indent=2)


def write_summary_json(result: DumpEquivResult, json_path: str) -> None:
    """Write a compact summary of a DumpEquivResult for programmatic consumption."""
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    summary = {
        "orig_blif":             result.orig_blif,
        "opt_blif":              result.opt_blif,
        "total_equiv_classes":   result.total_classes,
        "cross_network_matches": result.cross_network_matches,
        "error":                 result.error,
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fp=fh, indent=2)


# ---------------------------------------------------------------------------
# High-level entry point for a single BLIF pair
# ---------------------------------------------------------------------------

def validate_blif_pair(
    orig_blif: str,
    opt_blif:  str,
    abc_bin:   str,
    outdir:    str,
    run_fraig: bool = True,
) -> dict:
    """
    Run the full ABC SAT sweep validation on one (original, optimised) BLIF pair.

    Steps:
      1. dump_equiv  — cross-network SAT-proven equivalence classes
      2. fraig stats — single-network redundancy on the original (optional)

    Writes to outdir/:
      dump_equiv.txt      — raw dump_equiv output from ABC
      dump_equiv.abc      — the ABC script used (reproducibility)
      dump_equiv.log      — full ABC stdout + stderr
      abc_equiv_matches.csv — parsed EquivPair table
      dump_equiv_summary.json — compact summary
      fraig_stats.log     — FRAIG ABC output
      fraig_stats.json    — parsed FRAIG stats

    Returns a dict with keys: equiv_pairs, fraig_stats, errors.
    """
    print(f"  [dump_equiv]  {Path(orig_blif).name}  vs  {Path(opt_blif).name}")

    # Step 1: cross-network equivalence via dump_equiv
    de_result = run_dump_equiv(abc_bin, orig_blif, opt_blif, outdir)

    if de_result.error:
        print(f"    WARNING: dump_equiv failed — {de_result.error}")
    else:
        print(f"    Found {de_result.cross_network_matches} cross-network SAT-proven matches "
              f"(out of {de_result.total_classes} equivalence classes)")

    # Write outputs regardless of error status (partial results are useful too).
    write_equiv_csv(de_result.equiv_pairs, os.path.join(outdir, "abc_equiv_matches.csv"))
    write_summary_json(de_result, os.path.join(outdir, "dump_equiv_summary.json"))

    # Step 2: FRAIG stats on the original network
    fraig_result = None
    if run_fraig:
        print(f"  [fraig_stats] {Path(orig_blif).name}")
        fraig_result = run_fraig_stats(abc_bin, orig_blif, outdir)
        if fraig_result.error:
            print(f"    WARNING: fraig_stats failed — {fraig_result.error}")
        elif fraig_result.nodes_before is not None:
            reduction = ""
            if fraig_result.nodes_after is not None:
                saved = fraig_result.nodes_before - fraig_result.nodes_after
                reduction = f" (fraig eliminated {saved} redundant nodes)"
            print(f"    {fraig_result.nodes_before} nodes before fraig{reduction}")
        write_fraig_stats_json(
            fraig_result, os.path.join(outdir, "fraig_stats.json")
        )

    return {
        "equiv_pairs":  de_result.equiv_pairs,
        "fraig_stats":  fraig_result,
        "dump_result":  de_result,
        "errors": [e for e in [de_result.error,
                                fraig_result.error if fraig_result else None] if e],
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="ABC-native SAT sweep / dump_equiv validation for a BLIF pair.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--orig",   required=True,  help="Original BLIF file")
    p.add_argument("--opt",    required=True,  help="Optimised BLIF file")
    p.add_argument("--abc",    default=None,   help="Path to ABC binary (default: $ABC or 'abc' on PATH)")
    p.add_argument("--outdir", default=None,   help="Output directory (default: derived from BLIF names)")
    p.add_argument("--no-fraig", action="store_true", help="Skip FRAIG stats (faster)")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)

    try:
        abc_bin = find_abc(args.abc)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.orig):
        print(f"ERROR: original BLIF not found: {args.orig}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.opt):
        print(f"ERROR: optimised BLIF not found: {args.opt}", file=sys.stderr)
        sys.exit(1)

    outdir = args.outdir
    if outdir is None:
        orig_stem = Path(args.orig).stem
        opt_stem  = Path(args.opt).stem
        outdir = os.path.join("results", "abc_sweep", f"{orig_stem}_vs_{opt_stem}")

    print(f"\nABC SAT sweep validation")
    print(f"  Original : {args.orig}")
    print(f"  Optimised: {args.opt}")
    print(f"  ABC      : {abc_bin}")
    print(f"  Output   : {outdir}\n")

    result = validate_blif_pair(
        orig_blif  = args.orig,
        opt_blif   = args.opt,
        abc_bin    = abc_bin,
        outdir     = outdir,
        run_fraig  = not args.no_fraig,
    )

    n = len(result["equiv_pairs"])
    if result["errors"]:
        print(f"\n  Finished with {len(result['errors'])} warning(s).")
    print(f"\n  Summary: {n} formally-proven cross-network node correspondences.")
    print(f"  See {outdir}/abc_equiv_matches.csv\n")


if __name__ == "__main__":
    main()
