#!/usr/bin/env python3
"""Check circuit availability for canonical boundary-recovery COIs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_semantics import OPTIMIZATIONS, SEMANTICS_DIR, load_canonical_manifest, original_path, variant_path, write_csv  # noqa: E402

OUT = SEMANTICS_DIR / "circuit_availability.csv"


def main() -> int:
    rows = []
    for coi in load_canonical_manifest():
        for opt in ["identity", *OPTIMIZATIONS]:
            spec = original_path(coi.benchmark)
            impl = variant_path(coi.benchmark, opt)
            spec_ok = spec.exists()
            impl_ok = impl.exists()
            rows.append(
                {
                    "case_id": f"{coi.benchmark}|{coi.coi_name}|{opt}",
                    "spec_path": rel(spec),
                    "impl_path": rel(impl),
                    "spec_available": spec_ok,
                    "impl_available": impl_ok,
                    "generation_target": "boundary-recovery-micro-benchmarks" if "micro_" in coi.benchmark else "generate-variants",
                    "generation_attempted": False,
                    "generation_success": spec_ok and impl_ok,
                    "eligibility_status": "available" if spec_ok and impl_ok else "infrastructure_skip",
                    "skip_reason": "valid" if spec_ok and impl_ok else "missing_spec_or_impl",
                }
            )
    write_csv(OUT, rows)
    print(f"Wrote circuit availability rows: {len(rows)}")
    return 0


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
