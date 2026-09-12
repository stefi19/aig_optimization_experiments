"""Compatibility adapter for :mod:`scripts.materialization.select_materialization_targets`.

The research codebase now keeps implementation modules in logical script
subpackages.  This root-level file is intentionally tiny: it preserves the
long-standing `python scripts/select_materialization_targets.py` command used in old notes, Makefile
targets, CI logs, and external reproductions while delegating all real work to
`python -m scripts.materialization.select_materialization_targets`.
"""

from __future__ import annotations

import importlib as _importlib
import runpy as _runpy
import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

_TARGET_MODULE = "scripts.materialization.select_materialization_targets"

if __name__ == "__main__":
    _runpy.run_module(_TARGET_MODULE, run_name="__main__")
else:
    _module = _importlib.import_module(_TARGET_MODULE)
    globals().update({name: value for name, value in vars(_module).items() if not name.startswith("__")})
    __all__ = [name for name in globals() if not name.startswith("_")]
