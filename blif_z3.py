"""Exact Z3 encoding for the repository BLIF subset."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - exercised by check-z3 when installed
    import z3
except Exception:  # pragma: no cover
    z3 = None  # type: ignore[assignment]

from analyze_blif_matches import BlifNetwork, parse_blif


BLIF_Z3_SCHEMA_VERSION = "blif_z3_v1"


@dataclass(frozen=True)
class BlifZ3Encoding:
    net: BlifNetwork
    values: dict[str, object]
    inputs: dict[str, object]
    runtime: float
    fingerprint: str


def z3_available() -> bool:
    return z3 is not None


def z3_version() -> str:
    return "" if z3 is None else str(z3.get_version_string())


def circuit_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_symbol(name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)
    return f"b_{safe}_{digest}"


def encode_cover(inputs: list[object], cover: list[str]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    if not inputs:
        return z3.BoolVal(any(row.strip() == "1" for row in cover))
    cubes = []
    for raw in cover:
        parts = raw.split()
        if not parts:
            continue
        pattern = parts[0]
        out = parts[1] if len(parts) > 1 else "1"
        if out != "1":
            continue
        terms = []
        for char, value in zip(pattern, inputs):
            if char == "1":
                terms.append(value)
            elif char == "0":
                terms.append(z3.Not(value))
            elif char == "-":
                continue
            else:
                raise ValueError(f"unsupported BLIF cover character: {char}")
        cubes.append(z3.And(*terms) if terms else z3.BoolVal(True))
    return z3.Or(*cubes) if cubes else z3.BoolVal(False)


def encode_blif(path: Path) -> BlifZ3Encoding:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    start = time.perf_counter()
    net = parse_blif(path)
    values: dict[str, object] = {}
    inputs: dict[str, object] = {}
    for name in net.inputs:
        sym = z3.Bool(stable_symbol(name))
        values[name] = sym
        inputs[name] = sym
    seen_outputs = set(net.inputs)
    for node in net.nodes:
        missing = [fanin for fanin in node.inputs if fanin not in values]
        if missing:
            raise ValueError(f"node {node.output} has missing fanins: {missing}")
        if node.output in seen_outputs:
            raise ValueError(f"duplicate BLIF output assignment: {node.output}")
        values[node.output] = encode_cover([values[fanin] for fanin in node.inputs], node.cover)
        seen_outputs.add(node.output)
    runtime = time.perf_counter() - start
    return BlifZ3Encoding(net=net, values=values, inputs=inputs, runtime=runtime, fingerprint=circuit_fingerprint(path))


def bool_to_bv1(value: object) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    return z3.If(value, z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))


def pack_bus(values: dict[str, object], ordered_member_nodes: tuple[str, ...]) -> object:
    if z3 is None:
        raise RuntimeError("z3 is not installed")
    missing = [node for node in ordered_member_nodes if node not in values]
    if missing:
        raise KeyError(f"missing bus members: {missing}")
    bits = [bool_to_bv1(values[node]) for node in ordered_member_nodes]
    if not bits:
        raise ValueError("cannot pack empty bus")
    result = bits[0]
    for bit in bits[1:]:
        result = z3.Concat(bit, result)
    return result


def model_bus_assignment(model: object, input_buses: list[dict[str, object]], encoded: BlifZ3Encoding) -> dict[str, int]:
    assignment: dict[str, int] = {}
    for bus in input_buses:
        value = 0
        for idx, node in enumerate(bus.get("ordered_member_nodes", [])):
            sym = encoded.inputs.get(str(node))
            if sym is None:
                continue
            bit = bool(model.eval(sym, model_completion=True))
            if bit:
                value |= 1 << idx
        assignment[str(bus["name"])] = value
    return assignment


def provenance_row() -> dict[str, str]:
    return {
        "formal_backend": "z3",
        "z3_available": str(z3_available()).lower(),
        "z3_version": z3_version(),
        "schema_version": BLIF_Z3_SCHEMA_VERSION,
    }
