#!/bin/bash

set -e

# Small runner for the first optimization study.
# The idea is simple: for every BLIF benchmark, I generate several versions:
# original AIG form, balanced, rewritten, refactored, resubstituted, and a small resynthesis flow.
# Then the Python script compares the internal nodes between the original and optimized versions.

# If abc is not in PATH, run for example:
# ABC=/Users/stefi/tools/abc/abc ./run_abc_variants.sh
ABC=${ABC:-abc}

mkdir -p variants logs results

for bench in benchmarks/*.blif; do
    base=$(basename "$bench" .blif)

    echo "============================================================"
    echo "Benchmark: $base"
    echo "============================================================"

    # I avoid using only aliases like resyn2 here, because some ABC builds do not load abc.rc
    # in exactly the same way. These are explicit enough to be reproducible.

    for opt in original balance rewrite refactor resub resyn2_like; do
        case "$opt" in
            original)
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
                cmd="strash; balance; rewrite; refactor; balance; rewrite -z; refactor -z; balance"
                ;;
            *)
                cmd="strash"
                ;;
        esac

        out="variants/${base}_${opt}.blif"
        log="logs/${base}_${opt}.log"

        echo "Running $opt"

        # print_stats is saved in logs, because later I may want to compare ABC's own stats
        # with the metrics computed by the Python script.
        $ABC -c "read_blif $bench; $cmd; print_stats; write_blif $out" > "$log"
    done

done

echo

echo "Done. Generated optimized BLIF files in variants/ and logs in logs/."
echo "Next step: python3 analyze_blif_matches.py"
