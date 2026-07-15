#!/usr/bin/env python3
"""Generate micro BLIFs and canonical COIs for boundary-recovery semantics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from boundary_graph import CircuitGraph  # noqa: E402
from boundary_semantics import MICRO_COIS, MICRO_DIR  # noqa: E402
from coi_model import canonical_dict, normalize_coi  # noqa: E402


MICRO_BLIFS = {
    "micro_linear_chain": (
        """
.model micro_linear_chain
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 n3
1 1
.names n3 y
1 1
.end
""",
        [("linear_middle", ["n2"])],
    ),
    "micro_diamond": (
        """
.model micro_diamond
.inputs a
.outputs y
.names a n1
1 1
.names a n2
1 1
.names n1 n2 n3
1- 1
-1 1
.names n3 y
1 1
.end
""",
        [("diamond_reconvergence", ["n1", "n2", "n3"])],
    ),
    "micro_multi_input": (
        """
.model micro_multi_input
.inputs a b c
.outputs y
.names a b n1
11 1
.names n1 c n2
1- 1
-1 1
.names n2 y
1 1
.end
""",
        [("multi_input_cone", ["n1", "n2"])],
    ),
    "micro_multi_output": (
        """
.model micro_multi_output
.inputs a b
.outputs y1 y2
.names a b n1
11 1
.names n1 n2
1 1
.names n1 n3
1 1
.names n2 y1
1 1
.names n3 y2
1 1
.end
""",
        [("multi_output_region", ["n1", "n2", "n3"])],
    ),
    "micro_shared_fanout": (
        """
.model micro_shared_fanout
.inputs a b
.outputs y z
.names a b n1
11 1
.names n1 n2
1 1
.names n2 y
1 1
.names n1 z
1 1
.end
""",
        [("shared_fanout_region", ["n1", "n2"])],
    ),
    "micro_pi_boundary": (
        """
.model micro_pi_boundary
.inputs a b
.outputs y
.names a b n1
11 1
.names n1 y
1 1
.end
""",
        [("pi_boundary_region", ["n1"])],
    ),
    "micro_po_boundary": (
        """
.model micro_po_boundary
.inputs a
.outputs y
.names a n1
1 1
.names n1 y
1 1
.end
""",
        [("po_boundary_region", ["y"])],
    ),
    "micro_nested": (
        """
.model micro_nested
.inputs a
.outputs y
.names a n1
1 1
.names n1 n2
1 1
.names n2 n3
1 1
.names n3 y
1 1
.end
""",
        [("nested_inner", ["n2"]), ("nested_outer", ["n1", "n2", "n3"])],
    ),
    "micro_whole_design": (
        """
.model micro_whole_design
.inputs a b
.outputs y
.names a b n1
11 1
.names n1 y
1 1
.end
""",
        [("whole_design_region", ["n1", "y"])],
    ),
}


def main() -> int:
    MICRO_DIR.mkdir(parents=True, exist_ok=True)
    cois = []
    for benchmark, (text, specs) in sorted(MICRO_BLIFS.items()):
        path = MICRO_DIR / f"{benchmark}.blif"
        path.write_text(text.strip() + "\n", encoding="utf-8")
        graph = CircuitGraph.from_blif(path)
        for coi_name, region in specs:
            coi = normalize_coi(
                graph,
                benchmark=benchmark,
                optimization="*",
                coi_name=coi_name,
                region_nodes=region,
                source="automatically_derived",
                generation_method="micro_benchmark",
                original_manifest_status="new_micro_case",
                repair_notes="Canonical micro-benchmark COI.",
            )
            cois.append(canonical_dict(coi))
    MICRO_COIS.parent.mkdir(parents=True, exist_ok=True)
    import json

    MICRO_COIS.write_text(json.dumps({"cois": cois}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(MICRO_BLIFS)} micro BLIFs and {len(cois)} COIs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
