# External Benchmarks (Research Iteration 2)

This directory holds **third-party standard benchmark suites** that strengthen
the experimental validity of the study by testing the findings on realistic,
widely-used circuit families instead of only toy and synthetic circuits.

```
benchmarks/external/
├── iscas85/     # ISCAS-85 combinational suite (c17, c432, c499, …)
└── epfl/        # EPFL combinational benchmark suite (adder, bar, max, …)
```

These suites are **not redistributed in this repository** (licensing /
provenance reasons) and are **never downloaded automatically**. You place the
files here manually, then the existing pipeline discovers them automatically.

## How source families are assigned

The benchmark id is derived from the path by `scripts/benchmark_id.py`, and
`infer_source_family()` maps it to a *source family*:

| Path                                   | benchmark id                | source family |
|----------------------------------------|-----------------------------|---------------|
| `benchmarks/external/iscas85/c17.blif` | `external_iscas85_c17`      | `iscas85`     |
| `benchmarks/external/epfl/adder.blif`  | `external_epfl_adder`       | `epfl`        |
| `benchmarks/generated/adder_4.blif`    | `generated_adder_4`         | `generated`   |
| `benchmarks/real/hand_written/...`     | `real_hand_written_...`     | `custom`      |
| `benchmarks/majority3.blif`            | `majority3`                 | `toy`         |

So **just dropping a `.blif` file in the right folder is enough** — no code
changes are needed for it to flow through analysis, SAT validation and the
family-separated plots.

## Getting the benchmark files

### ISCAS-85
- Place `.blif` files directly in `benchmarks/external/iscas85/`.
- Sources: search for *"ISCAS-85 benchmark circuits BLIF"*, e.g.
  <https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/iscas/>.
- If you only have original BENCH (`.bench`), AIGER (`.aig`, `.aag`, `.aiger`)
  or Verilog/SystemVerilog (`.v`, `.sv`), convert them — see
  `scripts/import_external_benchmarks.py` (uses ABC / Yosys, documented there).

### EPFL combinational benchmarks
- Place `.blif` (or `.aig`/`.aiger`) files in `benchmarks/external/epfl/`.
- Source: <https://github.com/lsils/benchmarks> (the EPFL "Arithmetic" and
  "Random/Control" combinational suites).
- The upstream files are usually `.aig`/`.v`; convert them to `.blif` with
  `scripts/import_external_benchmarks.py`.

## Running the pipeline once files are present

```bash
# 1. (optional) import / convert files into the external folders
python3 scripts/import_external_benchmarks.py --help

# 2. record what is present
python3 scripts/build_benchmark_manifest.py     # → results/benchmark_manifest.csv

# 3. run the normal pipeline (discovers benchmarks/external/**/*.blif)
make generate-variants analyze sat-pipeline research-plots
```

The importer scans `--input-dir` recursively, so it can point at a downloaded
suite root with nested category folders. Hidden/cache directories are ignored.

If both external folders are empty the pipeline still runs on the existing
toy / generated / custom benchmarks and prints a clear warning that no external
benchmarks were found.
