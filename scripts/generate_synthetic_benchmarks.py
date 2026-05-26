#!/usr/bin/env python3
"""
scripts/generate_synthetic_benchmarks.py

Generates synthetic BLIF benchmark circuits for the AIG correspondence experiments.
All generated files use only .names gates so they are compatible with the existing
BLIF parser in analyze_blif_matches.py.

Output directory: benchmarks/generated/

Families generated:
  XOR chains     — xor_chain_8, xor_chain_16, xor_chain_32
  MUX trees      — mux_tree_4, mux_tree_8, mux_tree_16
  Adders         — adder_4, adder_8
  Multipliers    — multiplier_2, multiplier_4
  Random Boolean — random_small (8 inputs), random_medium (16 inputs)

Usage:
  python3 scripts/generate_synthetic_benchmarks.py
  make generate-benchmarks
"""

import os
import random
import textwrap

OUT_DIR = os.path.join("benchmarks", "generated")

# Fixed seed for reproducible random networks.
RANDOM_SEED = 42


# ---------------------------------------------------------------------------
# BLIF writing helpers
# ---------------------------------------------------------------------------

def blif_header(model_name: str, inputs: list[str], outputs: list[str]) -> str:
    return (
        f".model {model_name}\n"
        f".inputs {' '.join(inputs)}\n"
        f".outputs {' '.join(outputs)}\n"
    )


def blif_xor_gate(output: str, a: str, b: str) -> str:
    """Write a 2-input XOR as four product cubes (standard BLIF expansion)."""
    return (
        f".names {a} {b} {output}\n"
        f"10 1\n"
        f"01 1\n"
    )


def blif_and_gate(output: str, a: str, b: str) -> str:
    return f".names {a} {b} {output}\n11 1\n"


def blif_or_gate(output: str, a: str, b: str) -> str:
    return (
        f".names {a} {b} {output}\n"
        f"1- 1\n"
        f"-1 1\n"
    )


def blif_not_gate(output: str, a: str) -> str:
    return f".names {a} {output}\n0 1\n"


def blif_mux_gate(output: str, sel: str, d1: str, d0: str) -> str:
    """MUX: output = sel ? d1 : d0."""
    return (
        f".names {sel} {d1} {d0} {output}\n"
        f"11- 1\n"
        f"0-1 1\n"
    )


def write_blif(filename: str, content: str) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        f.write(".end\n")
    print(f"  Written: {path}")


# ---------------------------------------------------------------------------
# XOR chain
# ---------------------------------------------------------------------------

def generate_xor_chain(n: int) -> str:
    """
    XOR chain: out = x0 ^ x1 ^ x2 ^ ... ^ x(n-1)

    This is interesting because ABC's resyn2 drastically restructures
    XOR chains into balanced trees, making exact node matching fail
    while support overlap remains high.
    """
    inputs = [f"x{i}" for i in range(n)]
    outputs = ["out"]

    lines = [blif_header(f"xor_chain_{n}", inputs, outputs)]

    # Build chain left-to-right
    prev = inputs[0]
    for i in range(1, n):
        node = f"xor{i}"
        lines.append(blif_xor_gate(node, prev, inputs[i]))
        prev = node

    # Rename last internal node to out
    lines.append(f".names {prev} out\n1 1\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# MUX tree
# ---------------------------------------------------------------------------

def generate_mux_tree(n_data: int) -> str:
    """
    Balanced MUX tree that selects one of n_data data inputs.

    n_data must be a power of 2.  Uses ceil(log2(n_data)) selector inputs.
    This exercises refactor/resub because the tree has a lot of structural
    redundancy that ABC can reduce.
    """
    import math
    n_sel = int(math.log2(n_data))
    assert 2**n_sel == n_data, "n_data must be a power of 2"

    data = [f"d{i}" for i in range(n_data)]
    sel = [f"s{i}" for i in range(n_sel)]
    inputs = data + sel
    outputs = ["out"]

    lines = [blif_header(f"mux_tree_{n_data}", inputs, outputs)]

    level = list(data)
    sel_idx = n_sel - 1
    node_counter = 0

    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            node = f"mux_n{node_counter}"
            node_counter += 1
            lines.append(blif_mux_gate(node, sel[sel_idx], level[i + 1], level[i]))
            next_level.append(node)
        level = next_level
        sel_idx -= 1

    # Buffer to output
    lines.append(f".names {level[0]} out\n1 1\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# Ripple-carry adder
# ---------------------------------------------------------------------------

def generate_adder(n_bits: int) -> str:
    """
    n-bit ripple-carry adder with carry-out.

    Inputs: a0..a(n-1), b0..b(n-1), cin
    Outputs: sum0..sum(n-1), cout

    Each full adder is built from basic AND/OR/XOR gates.
    This tests whether ABC's balance command restructures carries.
    """
    a = [f"a{i}" for i in range(n_bits)]
    b = [f"b{i}" for i in range(n_bits)]
    inputs = a + b + ["cin"]
    outputs = [f"sum{i}" for i in range(n_bits)] + ["cout"]

    lines = [blif_header(f"adder_{n_bits}", inputs, outputs)]

    carry = "cin"
    for i in range(n_bits):
        # sum_i = a_i XOR b_i XOR carry_in
        ab_xor = f"ab_xor{i}"
        lines.append(blif_xor_gate(ab_xor, a[i], b[i]))
        lines.append(blif_xor_gate(f"sum{i}", ab_xor, carry))

        # carry_out = (a_i AND b_i) OR (carry_in AND (a_i XOR b_i))
        ab_and = f"ab_and{i}"
        c_ab = f"c_ab{i}"
        carry_out = f"carry{i}"
        lines.append(blif_and_gate(ab_and, a[i], b[i]))
        lines.append(blif_and_gate(c_ab, carry, ab_xor))
        lines.append(blif_or_gate(carry_out, ab_and, c_ab))
        carry = carry_out

    # Final carry to output
    lines.append(f".names {carry} cout\n1 1\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# Simple multiplier (array multiplier style)
# ---------------------------------------------------------------------------

def generate_multiplier(n_bits: int) -> str:
    """
    n x n array multiplier.

    Inputs: a0..a(n-1), b0..b(n-1)
    Outputs: p0..p(2n-1)

    Array multiplier generates partial products and sums them.
    Even small multipliers (n=2,4) have many internal nodes,
    making them good tests for support overlap under rewriting.
    """
    a = [f"a{i}" for i in range(n_bits)]
    b = [f"b{i}" for i in range(n_bits)]
    inputs = a + b
    outputs = [f"p{i}" for i in range(2 * n_bits)]

    lines = [blif_header(f"multiplier_{n_bits}", inputs, outputs)]

    node_counter = [0]

    def fresh(prefix="n"):
        name = f"{prefix}{node_counter[0]}"
        node_counter[0] += 1
        return name

    # Partial products: pp[i][j] = a[i] AND b[j]
    pp = {}
    for i in range(n_bits):
        for j in range(n_bits):
            name = fresh("pp")
            lines.append(blif_and_gate(name, a[i], b[j]))
            pp[(i, j)] = name

    # For n=2, hardwire the sum columns directly — keeps the BLIF manageable.
    # For larger n, use a simple ripple approach column by column.
    product_bits = {}

    if n_bits == 2:
        # p0 = a0 & b0
        lines.append(f".names {pp[(0,0)]} p0\n1 1\n")
        # p1 = (a0&b1) XOR (a1&b0)
        xor1 = fresh("x")
        lines.append(blif_xor_gate(xor1, pp[(0, 1)], pp[(1, 0)]))
        lines.append(f".names {xor1} p1\n1 1\n")
        # p2 = (a1&b1) XOR carry from p1
        carry1 = fresh("c")
        lines.append(blif_and_gate(carry1, pp[(0, 1)], pp[(1, 0)]))
        xor2 = fresh("x")
        lines.append(blif_xor_gate(xor2, pp[(1, 1)], carry1))
        lines.append(f".names {xor2} p2\n1 1\n")
        # p3 = carry
        carry2 = fresh("c")
        lines.append(blif_and_gate(carry2, pp[(1, 1)], carry1))
        lines.append(f".names {carry2} p3\n1 1\n")
        return "".join(lines)

    # General: collect partial products per column, sum with half/full adders
    columns = [[] for _ in range(2 * n_bits)]
    for i in range(n_bits):
        for j in range(n_bits):
            columns[i + j].append(pp[(i, j)])

    # Reduce each column to at most 2 values (carry-save style)
    carry_bits = [[] for _ in range(2 * n_bits + 1)]

    for col in range(2 * n_bits):
        bits = columns[col] + carry_bits[col]

        while len(bits) >= 3:
            a_bit, b_bit, c_bit = bits.pop(), bits.pop(), bits.pop()
            # Full adder
            ab = fresh("fa_ab")
            abc = fresh("fa_s")
            carry_fa = fresh("fa_c")
            lines.append(blif_xor_gate(ab, a_bit, b_bit))
            lines.append(blif_xor_gate(abc, ab, c_bit))
            # carry = majority(a,b,c)
            ab_and = fresh("and")
            ac_and = fresh("and")
            bc_and = fresh("and")
            carry_or1 = fresh("or")
            lines.append(blif_and_gate(ab_and, a_bit, b_bit))
            lines.append(blif_and_gate(ac_and, a_bit, c_bit))
            lines.append(blif_and_gate(bc_and, b_bit, c_bit))
            lines.append(blif_or_gate(carry_or1, ab_and, ac_and))
            lines.append(blif_or_gate(carry_fa, carry_or1, bc_and))
            bits.append(abc)
            carry_bits[col + 1].append(carry_fa)

        if len(bits) == 2:
            # Half adder
            a_bit, b_bit = bits
            ha_s = fresh("ha_s")
            ha_c = fresh("ha_c")
            lines.append(blif_xor_gate(ha_s, a_bit, b_bit))
            lines.append(blif_and_gate(ha_c, a_bit, b_bit))
            bits = [ha_s]
            carry_bits[col + 1].append(ha_c)

        # Whatever is left (0 or 1 bit) goes to the product
        if bits:
            product_bits[col] = bits[0]
        else:
            # Constant zero
            zero = fresh("zero")
            lines.append(f".names {zero}\n")  # constant 0
            product_bits[col] = zero

    for col in range(2 * n_bits):
        node = product_bits.get(col)
        if node:
            lines.append(f".names {node} p{col}\n1 1\n")
        else:
            lines.append(f".names p{col}\n")  # constant 0

    return "".join(lines)


# ---------------------------------------------------------------------------
# Random Boolean network
# ---------------------------------------------------------------------------

def generate_random_network(name: str, n_inputs: int, n_gates: int, n_outputs: int) -> str:
    """
    Random Boolean network with 2-input AND/OR/XOR gates.

    This is useful for testing that the analysis handles circuits where
    there is no obvious structural pattern.  The random seed is fixed so
    results are reproducible.
    """
    rng = random.Random(RANDOM_SEED)

    inputs = [f"x{i}" for i in range(n_inputs)]
    outputs = [f"out{i}" for i in range(n_outputs)]

    lines = [blif_header(name, inputs, outputs)]

    # Available signal names (start with just the inputs)
    available = list(inputs)
    gate_names = []

    for g in range(n_gates):
        gate_name = f"g{g}"
        gate_names.append(gate_name)

        a = rng.choice(available)
        b = rng.choice(available)

        gate_type = rng.choice(["and", "or", "xor"])
        if gate_type == "and":
            lines.append(blif_and_gate(gate_name, a, b))
        elif gate_type == "or":
            lines.append(blif_or_gate(gate_name, a, b))
        else:
            lines.append(blif_xor_gate(gate_name, a, b))

        available.append(gate_name)

    # Connect outputs to random gate outputs
    for i, out in enumerate(outputs):
        src = rng.choice(gate_names) if gate_names else inputs[0]
        lines.append(f".names {src} {out}\n1 1\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Generating synthetic BLIF benchmarks → {OUT_DIR}/")

    # 1. XOR chains
    for n in [8, 16, 32]:
        write_blif(f"xor_chain_{n}.blif", generate_xor_chain(n))

    # 2. MUX trees
    for n in [4, 8, 16]:
        write_blif(f"mux_tree_{n}.blif", generate_mux_tree(n))

    # 3. Ripple-carry adders
    for n in [4, 8]:
        write_blif(f"adder_{n}.blif", generate_adder(n))

    # 4. Multipliers
    for n in [2, 4]:
        write_blif(f"multiplier_{n}.blif", generate_multiplier(n))

    # 5. Random Boolean networks
    write_blif("random_small.blif",  generate_random_network("random_small",  8, 12, 2))
    write_blif("random_medium.blif", generate_random_network("random_medium", 16, 24, 4))

    print(f"\nDone. {len(os.listdir(OUT_DIR))} benchmarks written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
