#!/usr/bin/env python3
"""Generate a deterministic semantic-recovery benchmark suite.

This suite is a ground-truth source-level benchmark layer for future semantic
recovery experiments.  It writes RTL sources for all cases and exact truth-table
BLIFs for bounded-input cases.  ABC variants are generated only when a source
BLIF exists and an ABC binary is available.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "benchmarks" / "semantic_recovery"
RTL_DIR = BENCH_DIR / "rtl"
SOURCE_BLIF_DIR = BENCH_DIR / "blif" / "source"
VARIANT_BLIF_DIR = BENCH_DIR / "blif" / "variants"
RESULT_DIR = ROOT / "results" / "semantic_recovery"

SCHEMA_VERSION = "semantic_recovery_benchmark_v1"
GENERATION_SEED = 20260716
EXACT_BLIF_INPUT_LIMIT = 8
ABC_VARIANT_INPUT_LIMIT = 4

FLOWS: dict[str, str] = {
    "identity": "",
    "balance": "strash; balance",
    "rewrite": "strash; rewrite",
    "refactor": "strash; refactor",
    "resub": "strash; resub",
    "resyn": "strash; balance; rewrite; rewrite -z; balance; rewrite; balance",
    "resyn2": (
        "strash; balance; rewrite; refactor; balance; rewrite -z; "
        "refactor -z; balance"
    ),
    "dc2": "strash; dc2",
    "compress2rs": "strash; balance; rewrite; refactor; resub; balance; rewrite -z; refactor -z; resub; balance",
}

MANIFEST_FIELDS = [
    "case_id",
    "family",
    "operator",
    "expression",
    "input_buses",
    "output_buses",
    "input_widths",
    "output_widths",
    "signedness",
    "truncation",
    "extension_mode",
    "constants",
    "control_inputs",
    "source_rtl",
    "source_blif",
    "exact_blif_available",
    "expected_rtl_cost",
    "ground_truth_region",
    "ground_truth_boundary",
    "generation_seed",
    "schema_version",
]

VARIANT_FIELDS = [
    "case_id",
    "flow",
    "source_blif",
    "variant_blif",
    "status",
    "abc_command",
    "runtime_seconds",
    "message",
]


@dataclass(frozen=True)
class Bus:
    name: str
    width: int
    signed: bool = False
    role: str = "data"


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    family: str
    operator: str
    expression: str
    inputs: tuple[Bus, ...]
    output: Bus
    signedness: str = "unsigned"
    truncation: str = "none"
    extension_mode: str = "none"
    constants: dict[str, int | str] | None = None
    control_inputs: tuple[str, ...] = ()
    expected_rtl_cost: int = 1

    @property
    def total_input_bits(self) -> int:
        return sum(bus.width for bus in self.inputs)

    @property
    def flat_inputs(self) -> list[str]:
        names: list[str] = []
        for bus in self.inputs:
            if bus.width == 1:
                names.append(bus.name)
            else:
                names.extend(f"{bus.name}_{idx}" for idx in range(bus.width))
        return names

    @property
    def flat_outputs(self) -> list[str]:
        if self.output.width == 1:
            return [self.output.name]
        return [f"{self.output.name}_{idx}" for idx in range(self.output.width)]


def mask(width: int) -> int:
    return (1 << width) - 1


def to_signed(value: int, width: int) -> int:
    sign_bit = 1 << (width - 1)
    value &= mask(width)
    return value - (1 << width) if value & sign_bit else value


def from_signed(value: int, width: int) -> int:
    return value & mask(width)


def json_compact(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def bus_decl(direction: str, bus: Bus) -> str:
    signed = " signed" if bus.signed else ""
    width = "" if bus.width == 1 else f" [{bus.width - 1}:0]"
    return f"    {direction}{signed}{width} {bus.name}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def spec_to_verilog(spec: CaseSpec) -> str:
    ports = [bus.name for bus in spec.inputs] + [spec.output.name]
    decls = [bus_decl("input", bus) for bus in spec.inputs]
    decls.append(bus_decl("output", spec.output))
    return (
        f"// Generated semantic-recovery benchmark: {spec.case_id}\n"
        f"// Ground-truth expression: {spec.expression}\n"
        f"module {spec.case_id}({', '.join(ports)});\n"
        + ";\n".join(decls)
        + ";\n\n"
        f"    assign {spec.output.name} = {spec.expression};\n"
        "endmodule\n"
    )


def specs() -> list[CaseSpec]:
    cases: list[CaseSpec] = []

    def add(
        family: str,
        operator: str,
        width: int,
        expression: str,
        inputs: tuple[Bus, ...],
        output_width: int | None = None,
        signedness: str = "unsigned",
        truncation: str = "none",
        extension_mode: str = "none",
        constants: dict[str, int | str] | None = None,
        controls: tuple[str, ...] = (),
        cost: int = 1,
        suffix: str | None = None,
    ) -> None:
        out_width = output_width if output_width is not None else width
        case_suffix = suffix or f"w{width}"
        case_id = f"{family}_{operator}_{case_suffix}"
        cases.append(
            CaseSpec(
                case_id=case_id,
                family=family,
                operator=operator,
                expression=expression,
                inputs=inputs,
                output=Bus("y", out_width, signed=(signedness == "signed")),
                signedness=signedness,
                truncation=truncation,
                extension_mode=extension_mode,
                constants=constants or {},
                control_inputs=controls,
                expected_rtl_cost=cost,
            )
        )

    widths = (2, 3, 4, 6, 8, 12, 16)
    for w in widths:
        a = Bus("a", w)
        b = Bus("b", w)
        c = Bus("c", w)
        add("arithmetic", "unsigned_add", w, "a + b", (a, b), output_width=w + 1, cost=w)
        add(
            "arithmetic",
            "signed_add",
            w,
            "$signed(a) + $signed(b)",
            (Bus("a", w, True), Bus("b", w, True)),
            output_width=w + 1,
            signedness="signed",
            cost=w,
        )
        add("arithmetic", "sub", w, "a - b", (a, b), output_width=w + 1, cost=w)
        add("arithmetic", "reversed_sub", w, "b - a", (a, b), output_width=w + 1, cost=w)
        add("arithmetic", "add_add", w, "a + b + c", (a, b, c), output_width=w + 2, cost=2 * w)
        add(
            "arithmetic",
            "shifted_add",
            w,
            "a + (b << 1)",
            (a, b),
            output_width=w + 2,
            constants={"shift": 1},
            cost=w + 1,
        )
        add(
            "arithmetic",
            "constant_multiply",
            w,
            "a * 3",
            (a,),
            output_width=w + 2,
            constants={"multiplier": 3},
            cost=2 * w,
        )
        add(
            "arithmetic",
            "affine",
            w,
            "(a * 3) + 5",
            (a,),
            output_width=w + 3,
            constants={"scale": 3, "offset": 5},
            cost=2 * w + 1,
        )
        if w <= 8:
            add(
                "arithmetic",
                "truncated_multiply",
                w,
                "a * b",
                (a, b),
                output_width=w,
                truncation="low_bits",
                cost=w * w,
            )
        if w <= 4:
            add(
                "arithmetic",
                "full_multiply",
                w,
                "a * b",
                (a, b),
                output_width=2 * w,
                cost=w * w,
            )
            add(
                "arithmetic",
                "multiply_accumulate",
                w,
                "(a * b) + c",
                (a, b, Bus("c", 2 * w)),
                output_width=2 * w + 1,
                cost=w * w + 2 * w,
            )
            add(
                "arithmetic",
                "bilinear",
                w,
                "(a * b) + (c * d)",
                (a, b, Bus("c", w), Bus("d", w)),
                output_width=2 * w + 1,
                cost=2 * w * w,
            )
        if w in (3, 4, 8):
            add(
                "arithmetic",
                "mixed_width_add",
                w,
                "a + b",
                (Bus("a", w), Bus("b", max(1, w - 1))),
                output_width=w + 1,
                extension_mode="zero_extend_b",
                cost=w,
            )

        sel = Bus("sel", 1, role="control")
        add("control", "mux2", w, "sel ? b : a", (a, b, sel), controls=("sel",), cost=w)
        add(
            "control",
            "nested_mux",
            w,
            "sel0 ? (sel1 ? c : b) : a",
            (a, b, c, Bus("sel0", 1, role="control"), Bus("sel1", 1, role="control")),
            controls=("sel0", "sel1"),
            cost=2 * w,
        )
        add(
            "control",
            "arithmetic_select",
            w,
            "sel ? (a + b) : (a ^ b)",
            (a, b, sel),
            output_width=w + 1,
            controls=("sel",),
            cost=2 * w,
        )
        add(
            "control",
            "one_hot_mux",
            w,
            "(s0 ? a : 0) | (s1 ? b : 0)",
            (a, b, Bus("s0", 1, role="control"), Bus("s1", 1, role="control")),
            controls=("s0", "s1"),
            cost=2 * w,
        )
        add(
            "control",
            "priority_mux",
            w,
            "s0 ? a : (s1 ? b : c)",
            (a, b, c, Bus("s0", 1, role="control"), Bus("s1", 1, role="control")),
            controls=("s0", "s1"),
            cost=2 * w,
        )

        for op, expr in (
            ("bitwise_and", "a & b"),
            ("bitwise_or", "a | b"),
            ("bitwise_xor", "a ^ b"),
            ("bitwise_xnor", "~(a ^ b)"),
            ("masked_and", "a & {WIDTH{mask}}".replace("WIDTH", str(w))),
            ("masked_xor", "a ^ {WIDTH{mask}}".replace("WIDTH", str(w))),
        ):
            inputs = (a, b) if "masked" not in op else (a, Bus("mask", 1))
            add("boolean", op, w, expr, inputs, cost=w)
        add("boolean", "parity", w, "^a", (a,), output_width=1, cost=w)
        if w in (3, 4, 8):
            add(
                "boolean",
                "majority",
                w,
                "(a & b) | (a & c) | (b & c)",
                (a, b, c),
                cost=3 * w,
            )

        add("comparison", "eq", w, "a == b", (a, b), output_width=1, cost=w)
        add("comparison", "neq", w, "a != b", (a, b), output_width=1, cost=w)
        add("comparison", "unsigned_lt", w, "a < b", (a, b), output_width=1, cost=w)
        add(
            "comparison",
            "signed_lt",
            w,
            "$signed(a) < $signed(b)",
            (Bus("a", w, True), Bus("b", w, True)),
            output_width=1,
            signedness="signed",
            cost=w,
        )
        add("comparison", "unsigned_le", w, "a <= b", (a, b), output_width=1, cost=w)
        add(
            "comparison",
            "range_check",
            w,
            "(a >= 2) && (a <= 5)",
            (a,),
            output_width=1,
            constants={"lo": 2, "hi": 5},
            cost=w,
        )

        add("bitmanip", "concat", w, "{a, b}", (a, b), output_width=2 * w, cost=0)
        slice_msb = max(0, w // 2 - 1)
        add("bitmanip", "slice_low", w, f"a[{slice_msb}:0]", (a,), output_width=max(1, w // 2), cost=0)
        add(
            "bitmanip",
            "zero_extend",
            w,
            "{{WIDTH{1'b0}}, a}".replace("WIDTH", str(w)),
            (a,),
            output_width=2 * w,
            extension_mode="zero_extend",
            cost=0,
        )
        add(
            "bitmanip",
            "sign_extend",
            w,
            "{{WIDTH{a[MSB]}}, a}".replace("WIDTH", str(w)).replace("MSB", str(w - 1)),
            (Bus("a", w, True),),
            output_width=2 * w,
            signedness="signed",
            extension_mode="sign_extend",
            cost=0,
        )
        add(
            "bitmanip",
            "shift_left",
            w,
            "a << 1",
            (a,),
            output_width=w,
            constants={"shift": 1},
            cost=0,
        )
        add(
            "bitmanip",
            "shift_right",
            w,
            "a >> 1",
            (a,),
            output_width=w,
            constants={"shift": 1},
            cost=0,
        )
        add(
            "bitmanip",
            "mask_low",
            w,
            "a & MASK".replace("MASK", str(mask(max(1, w // 2)))),
            (a,),
            constants={"mask": mask(max(1, w // 2))},
            cost=0,
        )
        add(
            "bitmanip",
            "rotate_left",
            w,
            "{a[WIDTH-2:0], a[WIDTH-1]}".replace("WIDTH", str(w)),
            (a,),
            cost=0,
        )

    return sorted(cases, key=lambda spec: spec.case_id)


def assignment_to_buses(spec: CaseSpec, assignment: int) -> dict[str, int]:
    values: dict[str, int] = {}
    shift = 0
    for bus in spec.inputs:
        values[bus.name] = (assignment >> shift) & mask(bus.width)
        shift += bus.width
    return values


def eval_spec(spec: CaseSpec, values: dict[str, int]) -> int:
    op = spec.operator
    w = spec.inputs[0].width if spec.inputs else spec.output.width
    a = values.get("a", 0)
    b = values.get("b", 0)
    c = values.get("c", 0)
    d = values.get("d", 0)
    if op == "unsigned_add":
        result = a + b
    elif op == "signed_add":
        result = to_signed(a, w) + to_signed(b, w)
    elif op == "sub":
        result = a - b
    elif op == "reversed_sub":
        result = b - a
    elif op == "add_add":
        result = a + b + c
    elif op == "shifted_add":
        result = a + (b << 1)
    elif op == "constant_multiply":
        result = a * 3
    elif op == "affine":
        result = a * 3 + 5
    elif op in {"truncated_multiply", "full_multiply"}:
        result = a * b
    elif op == "multiply_accumulate":
        result = a * b + c
    elif op == "bilinear":
        result = a * b + c * d
    elif op == "mixed_width_add":
        result = a + b
    elif op == "mux2":
        result = b if values["sel"] else a
    elif op == "nested_mux":
        result = c if values["sel0"] and values["sel1"] else b if values["sel0"] else a
    elif op == "arithmetic_select":
        result = (a + b) if values["sel"] else (a ^ b)
    elif op == "one_hot_mux":
        result = (a if values["s0"] else 0) | (b if values["s1"] else 0)
    elif op == "priority_mux":
        result = a if values["s0"] else b if values["s1"] else c
    elif op == "bitwise_and":
        result = a & b
    elif op == "bitwise_or":
        result = a | b
    elif op == "bitwise_xor":
        result = a ^ b
    elif op == "bitwise_xnor":
        result = ~(a ^ b)
    elif op == "masked_and":
        result = a & (mask(w) if values["mask"] else 0)
    elif op == "masked_xor":
        result = a ^ (mask(w) if values["mask"] else 0)
    elif op == "parity":
        result = a.bit_count() & 1
    elif op == "majority":
        result = (a & b) | (a & c) | (b & c)
    elif op == "eq":
        result = int(a == b)
    elif op == "neq":
        result = int(a != b)
    elif op == "unsigned_lt":
        result = int(a < b)
    elif op == "signed_lt":
        result = int(to_signed(a, w) < to_signed(b, w))
    elif op == "unsigned_le":
        result = int(a <= b)
    elif op == "range_check":
        result = int(2 <= a <= 5)
    elif op == "concat":
        result = (a << w) | b
    elif op == "slice_low":
        result = a & mask(spec.output.width)
    elif op == "zero_extend":
        result = a
    elif op == "sign_extend":
        result = from_signed(to_signed(a, w), spec.output.width)
    elif op == "shift_left":
        result = a << 1
    elif op == "shift_right":
        result = a >> 1
    elif op == "mask_low":
        result = a & int(spec.constants["mask"] if spec.constants else mask(max(1, w // 2)))
    elif op == "rotate_left":
        result = ((a << 1) | (a >> (w - 1))) & mask(w)
    else:
        raise ValueError(f"no evaluator for {spec.case_id}")
    return result & mask(spec.output.width)


def pattern_for_assignment(spec: CaseSpec, assignment: int) -> str:
    bits: list[str] = []
    values = assignment_to_buses(spec, assignment)
    for bus in spec.inputs:
        value = values[bus.name]
        bits.extend("1" if (value >> idx) & 1 else "0" for idx in range(bus.width))
    return "".join(bits)


def spec_to_blif(spec: CaseSpec) -> str:
    lines = [
        f".model {spec.case_id}\n",
        f".inputs {' '.join(spec.flat_inputs)}\n",
        f".outputs {' '.join(spec.flat_outputs)}\n",
    ]
    assignments = range(1 << spec.total_input_bits)
    values_by_assignment = {
        assignment: eval_spec(spec, assignment_to_buses(spec, assignment))
        for assignment in assignments
    }
    for bit_idx, output_name in enumerate(spec.flat_outputs):
        on_assignments = [
            assignment
            for assignment, value in values_by_assignment.items()
            if (value >> bit_idx) & 1
        ]
        if not on_assignments:
            lines.append(f".names {output_name}\n")
            continue
        if len(on_assignments) == (1 << spec.total_input_bits):
            lines.append(f".names {output_name}\n1\n")
            continue
        lines.append(f".names {' '.join(spec.flat_inputs)} {output_name}\n")
        for assignment in on_assignments:
            lines.append(f"{pattern_for_assignment(spec, assignment)} 1\n")
    lines.append(".end\n")
    return "".join(lines)


def manifest_row(spec: CaseSpec, source_blif: Path | None) -> dict[str, str]:
    input_buses = [{"name": bus.name, "width": bus.width, "role": bus.role} for bus in spec.inputs]
    output_buses = [{"name": spec.output.name, "width": spec.output.width}]
    boundary = {
        "inputs": [bus.name for bus in spec.inputs],
        "outputs": [spec.output.name],
        "flat_inputs": spec.flat_inputs,
        "flat_outputs": spec.flat_outputs,
    }
    region = {
        "kind": "single_rtl_expression",
        "operator": spec.operator,
        "expression": spec.expression,
    }
    rtl_path = RTL_DIR / f"{spec.case_id}.v"
    return {
        "case_id": spec.case_id,
        "family": spec.family,
        "operator": spec.operator,
        "expression": spec.expression,
        "input_buses": json_compact(input_buses),
        "output_buses": json_compact(output_buses),
        "input_widths": json_compact({bus.name: bus.width for bus in spec.inputs}),
        "output_widths": json_compact({spec.output.name: spec.output.width}),
        "signedness": spec.signedness,
        "truncation": spec.truncation,
        "extension_mode": spec.extension_mode,
        "constants": json_compact(spec.constants or {}),
        "control_inputs": json_compact(list(spec.control_inputs)),
        "source_rtl": str(rtl_path.relative_to(ROOT)),
        "source_blif": str(source_blif.relative_to(ROOT)) if source_blif else "",
        "exact_blif_available": str(source_blif is not None).lower(),
        "expected_rtl_cost": str(spec.expected_rtl_cost),
        "ground_truth_region": json_compact(region),
        "ground_truth_boundary": json_compact(boundary),
        "generation_seed": str(GENERATION_SEED),
        "schema_version": SCHEMA_VERSION,
    }


def find_abc(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    env = os.environ.get("ABC")
    if env:
        path = Path(env)
        return path if path.exists() else None
    default = ROOT / ".abc_build" / "abc_repo" / "abc"
    return default if default.exists() else None


def run_abc_variant(abc: Path, source: Path, dest: Path, flow: str) -> tuple[str, float, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if flow == "identity":
        shutil.copyfile(source, dest)
        return "generated", 0.0, "copied source BLIF"
    source_rel = source.relative_to(ROOT)
    dest_rel = dest.relative_to(ROOT)
    command = f"read_blif {source_rel}; {FLOWS[flow]}; write_blif {dest_rel}"
    start = time.perf_counter()
    proc = subprocess.run(
        [str(abc), "-c", command],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )
    runtime = time.perf_counter() - start
    snippet = " ".join(proc.stdout.split())[:240]
    if proc.returncode != 0 or not dest.exists():
        return "failed", runtime, snippet or f"ABC exited {proc.returncode}"
    return "generated", runtime, snippet


def write_csv(rows: list[dict[str, str]], path: Path, fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    all_specs = specs()
    abc = find_abc(args.abc)
    manifest: list[dict[str, str]] = []
    variants: list[dict[str, str]] = []
    for spec in all_specs:
        rtl_path = RTL_DIR / f"{spec.case_id}.v"
        write_text(rtl_path, spec_to_verilog(spec))
        source_blif: Path | None = None
        if spec.total_input_bits <= args.exact_blif_input_limit:
            source_blif = SOURCE_BLIF_DIR / f"{spec.case_id}.blif"
            write_text(source_blif, spec_to_blif(spec))
        manifest.append(manifest_row(spec, source_blif))

        for flow in FLOWS:
            variant_path = VARIANT_BLIF_DIR / flow / f"{spec.case_id}.blif"
            command = (
                f"read_blif {source_blif.relative_to(ROOT)}; {FLOWS[flow]}; "
                f"write_blif {variant_path.relative_to(ROOT)}"
                if source_blif
                else ""
            )
            if source_blif is None:
                variants.append(
                    {
                        "case_id": spec.case_id,
                        "flow": flow,
                        "source_blif": "",
                        "variant_blif": "",
                        "status": "skipped_rtl_only",
                        "abc_command": command,
                        "runtime_seconds": "0.000000",
                        "message": f"exact BLIF requires {spec.total_input_bits} inputs; limit is {args.exact_blif_input_limit}",
                    }
                )
            elif flow != "identity" and spec.total_input_bits > args.abc_variant_input_limit:
                variants.append(
                    {
                        "case_id": spec.case_id,
                        "flow": flow,
                        "source_blif": str(source_blif.relative_to(ROOT)),
                        "variant_blif": "",
                        "status": "skipped_variant_too_large",
                        "abc_command": command,
                        "runtime_seconds": "0.000000",
                        "message": f"ABC variant generation bounded to {args.abc_variant_input_limit} inputs; case has {spec.total_input_bits}",
                    }
                )
            elif abc is None:
                status = "generated" if flow == "identity" else "skipped_no_abc"
                if flow == "identity":
                    variant_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source_blif, variant_path)
                variants.append(
                    {
                        "case_id": spec.case_id,
                        "flow": flow,
                        "source_blif": str(source_blif.relative_to(ROOT)),
                        "variant_blif": str(variant_path.relative_to(ROOT)) if status == "generated" else "",
                        "status": status,
                        "abc_command": command,
                        "runtime_seconds": "0.000000",
                        "message": "ABC unavailable" if status != "generated" else "copied source BLIF",
                    }
                )
            else:
                status, runtime, message = run_abc_variant(abc, source_blif, variant_path, flow)
                variants.append(
                    {
                        "case_id": spec.case_id,
                        "flow": flow,
                        "source_blif": str(source_blif.relative_to(ROOT)),
                        "variant_blif": str(variant_path.relative_to(ROOT)) if status == "generated" else "",
                        "status": status,
                        "abc_command": command,
                        "runtime_seconds": f"{runtime:.6f}",
                        "message": message,
                    }
                )
    return manifest, variants


def write_summary(manifest: list[dict[str, str]], variants: list[dict[str, str]], path: Path) -> None:
    by_family: dict[str, int] = {}
    by_flow_status: dict[tuple[str, str], int] = {}
    widths: set[int] = set()
    exact_blif = 0
    for row in manifest:
        by_family[row["family"]] = by_family.get(row["family"], 0) + 1
        widths.update(json.loads(row["input_widths"]).values())
        if row["exact_blif_available"] == "true":
            exact_blif += 1
    for row in variants:
        key = (row["flow"], row["status"])
        by_flow_status[key] = by_flow_status.get(key, 0) + 1

    lines = [
        "# Semantic Recovery Benchmark Suite",
        "",
        "This generated suite is a ground-truth source-level benchmark layer for future RTL-expression recovery experiments. RTL is generated for every case. Exact BLIF and ABC flow variants are generated only for cases whose flat input space is small enough for deterministic truth-table emission.",
        "",
        f"- Schema version: `{SCHEMA_VERSION}`",
        f"- Generation seed: `{GENERATION_SEED}`",
        f"- Cases: {len(manifest)}",
        f"- Families: {', '.join(f'{name}={count}' for name, count in sorted(by_family.items()))}",
        f"- Input widths covered: {', '.join(str(width) for width in sorted(widths))}",
        f"- Exact source BLIF cases: {exact_blif}",
        f"- Variant rows: {len(variants)}",
        "",
        "## Flow Status",
        "",
        "| Flow | Generated | Skipped RTL-only | Skipped too large | Skipped no ABC | Failed |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for flow in FLOWS:
        generated = by_flow_status.get((flow, "generated"), 0)
        rtl_only = by_flow_status.get((flow, "skipped_rtl_only"), 0)
        too_large = by_flow_status.get((flow, "skipped_variant_too_large"), 0)
        no_abc = by_flow_status.get((flow, "skipped_no_abc"), 0)
        failed = by_flow_status.get((flow, "failed"), 0)
        lines.append(f"| `{flow}` | {generated} | {rtl_only} | {too_large} | {no_abc} | {failed} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "These benchmarks do not claim recovered RTL yet. They provide known source expressions, bus metadata, and bounded gate-level implementations so later phases can test semantic template recovery, CEGIS validation, and cost-aware RTL selection against ground truth.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abc", default=None, help="ABC binary path; defaults to ABC env var or .abc_build/abc_repo/abc")
    parser.add_argument("--exact-blif-input-limit", type=int, default=EXACT_BLIF_INPUT_LIMIT)
    parser.add_argument("--abc-variant-input-limit", type=int, default=ABC_VARIANT_INPUT_LIMIT)
    parser.add_argument("--manifest", type=Path, default=RESULT_DIR / "semantic_benchmark_manifest.csv")
    parser.add_argument("--variants", type=Path, default=RESULT_DIR / "semantic_benchmark_variants.csv")
    parser.add_argument("--summary", type=Path, default=RESULT_DIR / "semantic_benchmark_summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest, variants = generate(args)
    write_csv(manifest, args.manifest, MANIFEST_FIELDS)
    write_csv(variants, args.variants, VARIANT_FIELDS)
    write_summary(manifest, variants, args.summary)
    print(f"Wrote {len(manifest)} semantic benchmark cases")
    print(f"Wrote {len(variants)} semantic benchmark variant rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
