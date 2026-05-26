#!/bin/bash

# run_abc_variants.sh
#
# For every BLIF benchmark (original + generated), generate several optimized
# variants using ABC and write them to variants/ and logs/.
#
# Core variants:
#   original, balance, rewrite, refactor, resub, resyn2_like
#
# Extended variants (run with error handling — failure does not abort the run):
#   rewrite_z, refactor_z, resyn, resyn2, dc2, compress2rs
#
# Usage:
#   ./run_abc_variants.sh
#   ABC=/path/to/abc ./run_abc_variants.sh

set -e

# nullglob prevents globs from expanding to literal strings when no files match.
# Without this, BENCH_FILES=(benchmarks/*.blif) would contain the literal
# string "benchmarks/*.blif" when the directory has no .blif files.
shopt -s nullglob

ABC=${ABC:-abc}

mkdir -p variants logs results

# ── Benchmark discovery ───────────────────────────────────────────────────────

BENCH_FILES=(benchmarks/*.blif)

if compgen -G "benchmarks/generated/*.blif" > /dev/null 2>&1; then
    BENCH_FILES+=( benchmarks/generated/*.blif )
else
    echo ""
    echo "Note: benchmarks/generated/ is empty or missing."
    echo "      Run 'make generate-benchmarks' to create synthetic benchmarks."
    echo ""
fi

# Real benchmarks (hand-written + any converted Verilog / ISCAS-85)
while IFS= read -r -d '' bf; do
    BENCH_FILES+=( "$bf" )
done < <(find benchmarks/real -name "*.blif" -print0 2>/dev/null)

if [ ${#BENCH_FILES[@]} -eq 0 ]; then
    echo "ERROR: No .blif files found in benchmarks/. Aborting."
    exit 1
fi

# ── Core variants ─────────────────────────────────────────────────────────────
# These use explicit ABC command sequences rather than named scripts (e.g. resyn2)
# because some ABC builds do not load abc.rc consistently across platforms.

run_core_variant() {
    local bench="$1" base="$2" opt="$3"
    local cmd out log

    case "$opt" in
        original)
            # strash converts to AIG and collapses trivial redundancy.
            # Running it even for "original" ensures parse_blif sees a consistent
            # node representation across all variants.
            cmd="strash"
            ;;
        balance)
            cmd="strash; balance"
            ;;
        rewrite)
            cmd="strash; rewrite"
            ;;
        refactor)
            cmd="strash; refactor"
            ;;
        resub)
            cmd="strash; resub"
            ;;
        resyn2_like)
            # Explicit expansion of resyn2 so behaviour is identical regardless
            # of whether abc.rc is loaded on the target machine.
            cmd="strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance"
            ;;
        *)
            echo "  Unknown core variant: $opt (skipping)"; return ;;
    esac

    out="variants/${base}_${opt}.blif"
    log="logs/${base}_${opt}.log"
    echo "  $opt"
    # print_stats goes to the log for comparison with our Python metrics later.
    $ABC -c "read_blif $bench; $cmd; print_stats; write_blif $out" > "$log" 2>&1
}

# ── Extended variants ─────────────────────────────────────────────────────────
# Wrapped in a subshell with || so one ABC failure does not stop the whole run.

run_extended_variant() {
    local bench="$1" base="$2" opt="$3"
    local cmd out log

    case "$opt" in
        rewrite_z)   cmd="strash; rewrite -z" ;;
        refactor_z)  cmd="strash; refactor -z" ;;
        resyn)       cmd="strash; balance; rewrite; rewrite -z; balance; rewrite; balance" ;;
        resyn2)      cmd="strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance" ;;
        dc2)         cmd="strash; dc2" ;;
        compress2rs) cmd="strash; balance; rewrite; refactor; resub; balance; rewrite -z; refactor -z; resub; balance" ;;
        *)           echo "  Unknown extended variant: $opt (skipping)"; return ;;
    esac

    out="variants/${base}_${opt}.blif"
    log="logs/${base}_${opt}.log"
    echo "  $opt (extended)"
    ($ABC -c "read_blif $bench; $cmd; print_stats; write_blif $out" > "$log" 2>&1) || {
        echo "    Warning: ABC failed for ${base}_${opt} — see $log"
    }
}

# ── Main loop ─────────────────────────────────────────────────────────────────

for bench in "${BENCH_FILES[@]}"; do
    # Compute a safe, collision-free ID from the relative path.
    # e.g. benchmarks/real/hand_written/full_adder.blif → real_hand_written_full_adder
    # e.g. benchmarks/majority3.blif → majority3
    base=$(python3 scripts/benchmark_id.py "$bench")
    echo "============================================================"
    echo "Benchmark: $base  ($bench)"
    echo "============================================================"

    for opt in original balance rewrite refactor resub resyn2_like; do
        run_core_variant "$bench" "$base" "$opt"
    done

    for opt in rewrite_z refactor_z resyn resyn2 dc2 compress2rs; do
        run_extended_variant "$bench" "$base" "$opt"
    done

    echo ""
done

echo "Done. Generated optimized BLIF files in variants/ and logs in logs/."
echo "Next step: python3 analyze_blif_matches.py"
