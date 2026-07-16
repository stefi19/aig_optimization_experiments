"""Deterministic RTL emitter for typed direct semantic expressions."""

from __future__ import annotations

from semantic_ast import SemanticExpr


def emit_candidate_module(
    *,
    module_name: str,
    input_buses: list[dict[str, object]],
    output_bus: dict[str, object],
    expr: SemanticExpr,
) -> str:
    ports = [str(bus["name"]) for bus in input_buses] + [str(output_bus["name"])]
    lines = [f"module {module_name}({', '.join(ports)});"]
    for bus in input_buses:
        signed = " signed" if bus.get("signed", False) else ""
        width = int(bus["width"])
        rng = f"[{width - 1}:0] " if width > 1 else ""
        lines.append(f"  input{signed} {rng}{bus['name']};")
    out_width = int(output_bus["width"])
    out_rng = f"[{out_width - 1}:0] " if out_width > 1 else ""
    lines.append(f"  output {out_rng}{output_bus['name']};")
    lines.append(f"  assign {output_bus['name']} = {expr.rtl_text};")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"
