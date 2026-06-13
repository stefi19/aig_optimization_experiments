# ISCAS-85 benchmarks

Place ISCAS-85 combinational `.blif` files here, e.g.:

```
c17.blif  c432.blif  c499.blif  c880.blif  c1355.blif
c1908.blif  c2670.blif  c3540.blif  c5315.blif  c6288.blif  c7552.blif
```

These files are **not included** and are **not downloaded automatically**.
See `../README.md` and `scripts/import_external_benchmarks.py` for how to add
and convert them. The importer scans input directories recursively, so it can
point at a suite root. Once `.blif` files are here, the pipeline picks them up
automatically (they get source family `iscas85`).
