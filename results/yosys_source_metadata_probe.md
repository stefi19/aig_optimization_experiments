# Yosys Source Metadata Probe

This probe checks whether a tiny Verilog example can be lowered by Yosys
while preserving signal names or source-location attributes.

- Yosys available: `false`
- Version: `not available`
- Example: `benchmarks/source_examples/simple_pipeline.v`
- JSON generated: `false`
- BLIF generated: `false`
- Netnames with `src`: `0`
- Cells with `src`: `0`
- Visible RTL signals: `none recorded`

Notes: Yosys not found on PATH; install Yosys to run the metadata-preservation probe.

Interpretation: this is an availability and metadata-survival probe only.
If Yosys is unavailable, the source-map prototype writes a documented skip row.
