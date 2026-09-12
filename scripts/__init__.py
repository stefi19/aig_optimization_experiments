"""Research automation package for the AIG optimization experiments.

The package initializer deliberately adds the `scripts/` directory itself to
`sys.path`.  Many historical experiment modules import helper entrypoints with
flat names such as `benchmark_id` or `probe_abc_sat_sweeping`; keeping that
compatibility layer in one place lets the implementations live in subpackages
without invalidating old scripts, notebooks, CI commands, or artifact metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
