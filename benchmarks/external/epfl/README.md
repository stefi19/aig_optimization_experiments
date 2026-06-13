# EPFL combinational benchmarks

Place EPFL combinational `.blif` files here (convert from `.aig`/`.aiger`/`.v`
or `.sv` if needed),
e.g. from the arithmetic and random/control suites:

```
adder.blif  bar.blif  div.blif  hyp.blif  log2.blif  max.blif
multiplier.blif  sin.blif  sqrt.blif  square.blif  ...
```

These files are **not included** and are **not downloaded automatically**.
Upstream: <https://github.com/lsils/benchmarks>. See `../README.md` and
`scripts/import_external_benchmarks.py` for recursive import/conversion
instructions. Once `.blif` files are here, the pipeline picks them up
automatically (they get source family `epfl`).

> Note: several EPFL circuits (e.g. `hyp`, `log2`, `div`) are very large and
> have wide input cones — exact truth-table mode is infeasible for them, so the
> pipeline falls back to random simulation. The benchmark manifest records
> whether exact mode is possible for each file.
