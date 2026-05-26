#!/usr/bin/env bash
# start.sh — One-command bootstrap for the AIG optimization experiments.
#
# What this script does:
#   1. Checks that Python 3 and the required packages are available.
#   2. Locates the ABC binary (or builds it if missing).
#   3. Creates output directories.
#   4. Runs the full pipeline in order:
#        run_abc_variants.sh          → variants/ and logs/
#        analyze_blif_matches.py      → results/summary_metrics.csv, top_candidates.csv
#        visualize_results.py         → results/plots/
#        select_sat_candidates.py     → results/sat_refinement_candidates.csv
#        sat_refinement_abc.py        → results/sat_verified_candidates.csv
#        summarize_sat_results.py     → results/sat_summary.csv, sat_summary.md
#        evaluate_topk_recovery.py    → results/topk_recovery.*
#        ablation_study.py            → results/ablation_summary.*
#        region_correspondence.py     → results/region_*
#        counterexample_guided_refinement.py → results/cegar_*
#        research_plots.py            → results/plots/
#        pytest tests/                → test report
#   5. Prints a summary of all output files.
#
# Usage:
#   bash ./start.sh
#
# If `abc` is not on PATH, point the script at it:
#   ABC=/path/to/abc bash ./start.sh
#
# All intermediate and final outputs are written under results/, variants/, and logs/.

set -euo pipefail

# ── Colours (disabled automatically when not a terminal) ──────────────────────
if [ -t 1 ]; then
    GREEN="\033[0;32m"
    YELLOW="\033[1;33m"
    RED="\033[0;31m"
    BOLD="\033[1m"
    RESET="\033[0m"
else
    GREEN="" YELLOW="" RED="" BOLD="" RESET=""
fi

step()  { echo -e "${BOLD}==> $*${RESET}"; }
ok()    { echo -e "${GREEN}    ✓ $*${RESET}"; }
warn()  { echo -e "${YELLOW}    ⚠  $*${RESET}"; }
fail()  { echo -e "${RED}    ✗ $*${RESET}"; exit 1; }

# ── Locate script directory so we can run relative paths reliably ─────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. Python check ───────────────────────────────────────────────────────────
step "Checking Python 3"

if ! command -v python3 &>/dev/null; then
    fail "python3 not found. Install Python 3.9+ and re-run."
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "python3 $PY_VERSION"

# Check required packages.
MISSING_PKGS=()
for pkg in pandas matplotlib pytest; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    warn "Missing packages: ${MISSING_PKGS[*]}"
    step "Installing missing packages with pip"
    python3 -m pip install --quiet "${MISSING_PKGS[@]}"
    ok "Packages installed"
else
    ok "All required packages present (pandas, matplotlib, pytest)"
fi

# ── 2. Locate ABC ─────────────────────────────────────────────────────────────
step "Locating ABC binary"

ABC_BIN=""

# Priority 1: explicit environment variable
if [ -n "${ABC:-}" ] && [ -x "$ABC" ]; then
    ABC_BIN="$ABC"
    ok "Using ABC from \$ABC env var: $ABC_BIN"
fi

# Priority 2: abc on PATH
if [ -z "$ABC_BIN" ] && command -v abc &>/dev/null; then
    ABC_BIN="$(command -v abc)"
    ok "Found abc on PATH: $ABC_BIN"
fi

# Priority 3: local build under .abc_build/
LOCAL_ABC=".abc_build/abc_repo/abc"
if [ -z "$ABC_BIN" ] && [ -x "$LOCAL_ABC" ]; then
    ABC_BIN="$(pwd)/$LOCAL_ABC"
    ok "Found local ABC build: $ABC_BIN"
fi

# Priority 4: build ABC now
if [ -z "$ABC_BIN" ]; then
    warn "ABC binary not found. Building from source (this takes a few minutes)..."
    ABC_REPO=".abc_build/abc_repo"
    mkdir -p .abc_build
    if [ ! -d "$ABC_REPO" ]; then
        git clone --depth=1 https://github.com/berkeley-abc/abc.git "$ABC_REPO"
    fi
    make -C "$ABC_REPO" -j2
    ABC_BIN="$(pwd)/$ABC_REPO/abc"
    ok "ABC built: $ABC_BIN"
fi

export ABC="$ABC_BIN"

# ── 3. Verify benchmarks exist ────────────────────────────────────────────────
step "Checking benchmarks"

if [ ! -d benchmarks ] || [ -z "$(find benchmarks -name '*.blif' 2>/dev/null | head -1)" ]; then
    fail "No .blif files found under benchmarks/. Ensure the benchmarks directory is populated."
fi

BENCH_COUNT=$(find benchmarks -name "*.blif" | wc -l | tr -d ' ')
ok "$BENCH_COUNT benchmark(s) found under benchmarks/"

# ── 4. Create output directories ──────────────────────────────────────────────
mkdir -p variants logs results results/plots

# ── 5. Generate optimized BLIF variants ───────────────────────────────────────
step "Generating BLIF variants  (run_abc_variants.sh)"
bash ./run_abc_variants.sh
ok "Variants written to variants/"

# ── 6. Analyse correspondences ────────────────────────────────────────────────
step "Analysing node correspondences  (analyze_blif_matches.py)"
python3 analyze_blif_matches.py
ok "Results written to results/summary_metrics.csv and results/top_candidates.csv"

# ── 7. Visualise ──────────────────────────────────────────────────────────────
step "Generating plots  (visualize_results.py)"
python3 visualize_results.py
ok "Plots saved to results/plots/"

# ── 8. SAT pipeline ───────────────────────────────────────────────────────────
step "Filtering SAT candidates  (select_sat_candidates.py)"
python3 select_sat_candidates.py
ok "High-confidence candidates → results/sat_refinement_candidates.csv"

step "Running ABC equivalence checks  (sat_refinement_abc.py)"
python3 sat_refinement_abc.py
ok "Verification results → results/sat_verified_candidates.csv"

step "Summarising SAT results  (summarize_sat_results.py)"
python3 summarize_sat_results.py
ok "Summary → results/sat_summary.csv and results/sat_summary.md"

# ── 9. Top-K / ablation / region / CEGAR ──────────────────────────────────────
step "Evaluating top-K recovery  (evaluate_topk_recovery.py)"
python3 evaluate_topk_recovery.py
ok "Results → results/topk_recovery.*"

step "Running ablation study  (ablation_study.py)"
python3 ablation_study.py
ok "Results → results/ablation_summary.*"

step "Running region correspondence baseline  (region_correspondence.py)"
python3 region_correspondence.py
ok "Results → results/region_*"

step "Running CEGAR refinement  (counterexample_guided_refinement.py)"
python3 counterexample_guided_refinement.py
ok "Results → results/cegar_*"

step "Generating research plots  (research_plots.py)"
python3 research_plots.py
ok "Plots → results/plots/"

# ── 10. Tests ─────────────────────────────────────────────────────────────────
step "Running tests  (pytest)"
python3 -m pytest tests/ -v
ok "All tests passed"

# ── 11. Summary of outputs ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Pipeline complete. Output files:${RESET}"

for f in \
    results/summary_metrics.csv \
    results/top_candidates.csv \
    results/sat_refinement_candidates.csv \
    results/sat_verified_candidates.csv \
    results/sat_summary.csv \
    results/sat_summary.md \
    results/topk_recovery.csv \
    results/topk_recovery.md \
    results/ablation_summary.csv \
    results/ablation_summary.md \
    results/region_correspondence.csv \
    results/region_summary.md \
    results/cegar_refinement.csv \
    results/cegar_summary.md \
    results/plots; do
    if [ -e "$f" ]; then
        echo -e "  ${GREEN}✓${RESET}  $f"
    else
        echo -e "  ${YELLOW}?${RESET}  $f  (not found — check earlier output)"
    fi
done

echo ""
