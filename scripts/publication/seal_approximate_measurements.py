import csv
import json
from pathlib import Path

from scripts.analysis.audit_approximate_distance import ROOT,sha

OUT=ROOT/"results/formal_approximate_correspondence"


def seal():
    names=["cases.csv","candidates.csv","sampling.csv","ranking_queries.csv","ranking_summary.csv","coverage_abstention.csv","critical_path_diagnostics.csv","reconstruction.csv","provenance.json"]
    paths=[OUT/name for name in names]
    paths.extend(p for p in (OUT/"audit").rglob("*") if p.is_file())
    for name in ("artifacts","reconstruction"):
        paths.extend((OUT/name).glob("*.blif"))
    code=[ROOT/name for name in ["analyze_blif_matches.py","blif_z3.py","contextual_error_metrics.py","source_blind_counterpart_placement.py","necessity_first_rewrites.py","formal_locality_barriers.py","configs/formal_approximate_correspondence.json","scripts/abc/cec.py","scripts/analysis/approximate_correspondence.py","scripts/analysis/audit_approximate_distance.py","scripts/analysis/run_formal_approximate_correspondence.py","scripts/analysis/run_approximation_guided_reconstruction.py","scripts/validation/approximate_oracle.py","scripts/validation/check_formal_approximate_correspondence.py","scripts/publication/seal_approximate_measurements.py"]]
    data=dict(schema="approximate_measurement_manifest_v1",files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths+code))})
    (OUT/"measurement_manifest.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print(f"Sealed {len(data['files'])} measurement and implementation files")


if __name__=="__main__":
    seal()
