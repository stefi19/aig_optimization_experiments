# benchmarks/real/README.md
#
# Real Benchmark Suite
# ====================
#
# This directory contains real combinational-logic benchmarks in BLIF format
# (and their Verilog sources where available).
#
# Directory layout
# ----------------
#
#   benchmarks/real/
#   ├── hand_written/        # Small, hand-crafted BLIF files (verified by inspection)
#   │   ├── full_adder.blif       – 1-bit full adder   (3 in, 2 out, 6 nodes)
#   │   ├── priority_enc_4.blif  – 4→2 priority encoder (4 in, 3 out, 5 nodes)
#   │   ├── mux_4to1.blif        – 4-to-1 multiplexer  (6 in, 1 out, 10 nodes)
#   │   ├── comparator_4.blif    – 4-bit equality cmp  (8 in, 1 out, 9 nodes)
#   │   └── parity_8.blif        – 8-bit XOR parity    (8 in, 1 out, 7 nodes)
#   ├── verilog_examples/    # Verilog sources; convert with Yosys (see below)
#   │   ├── adder_8.v            – 8-bit ripple-carry adder
#   │   └── popcount_8.v         – 8-bit population count
#   └── README.md            # This file
#
# Converting Verilog → BLIF
# -------------------------
# If you have Yosys installed:
#
#   yosys -p "read_verilog <file>.v; synth -top <module>; write_blif <file>.blif"
#
# Or use the helper script (handles all files in verilog_examples/ at once):
#
#   python3 scripts/import_real_benchmarks.py --verilog benchmarks/real/verilog_examples/
#
# The converted BLIFs will be placed in benchmarks/real/converted_blif/.
#
# Adding ISCAS-85 benchmarks
# --------------------------
# The ISCAS-85 suite (c17, c432, c499, …) is widely used in logic synthesis
# research but cannot be redistributed here due to licensing.
#
# Download instructions:
#   1. Visit https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/iscas/
#      or search for "ISCAS 85 benchmark circuits".
#   2. Place the .blif files in  benchmarks/real/iscas85/
#   3. Run the pipeline normally; run_abc_variants.sh discovers all
#      benchmarks/**/*.blif recursively.
#
# Adding your own benchmarks
# --------------------------
# Drop any .blif file anywhere under  benchmarks/real/  and it will be picked
# up automatically by run_abc_variants.sh (uses `find benchmarks -name "*.blif"`).
