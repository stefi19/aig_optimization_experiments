# ISCAS-85 benchmarks

Place ISCAS-85 combinational `.blif` files here, e.g.:

```
c17.blif  c432.blif  c499.blif  c880.blif  c1355.blif
c1908.blif  c2670.blif  c3540.blif  c5315.blif  c6288.blif  c7552.blif
```

These files are **not included** and are **not downloaded automatically**.
If you have original `.bench` files, convert them with:

```bash
make import-external FAMILY=iscas85 INPUT_DIR=/path/to/iscas85_bench_root \
    ARGS=--convert-bench
```

The importer also accepts `.blif` directly, and can convert `.aig`/`.aiger`
with ABC or `.v`/`.sv` with Yosys. It scans input directories recursively, so it
can point at a suite root. Once `.blif` files are here, the pipeline picks them
up automatically (they get source family `iscas85`).
