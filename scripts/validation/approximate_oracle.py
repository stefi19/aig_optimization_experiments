from itertools import product


def scalar_values(net, assignment, requested, overrides=None):
    values = dict(assignment)
    values.update(overrides or {})
    drivers = {node.output: node for node in net.nodes}
    visiting = set()

    def visit(name):
        if name in values:
            return values[name]
        if name in visiting:
            raise ValueError("cyclic graph")
        visiting.add(name)
        node = drivers[name]
        fanins = [visit(n) for n in node.inputs]
        if not fanins:
            value = int("1" in [r.strip() for r in node.cover])
        else:
            rows = [r.split() for r in node.cover if r.strip()]
            polarities = {r[1] if len(r) == 2 else "1" for r in rows}
            if len(polarities) > 1:
                raise ValueError("mixed polarity")
            hit = any(all(c == "-" or int(c) == x for c, x in zip(r[0], fanins, strict=True)) for r in rows)
            value = int(hit) if polarities != {"0"} else int(not hit)
        visiting.remove(name)
        values[name] = value
        return value

    return {name: visit(name) for name in requested}


def oracle_pair(source, optimized, target, candidate, invert=False):
    if set(source.inputs) != set(optimized.inputs):
        raise ValueError("unaligned primary inputs")
    count = 1 << len(source.inputs)
    disagree = contextual = hamming = absolute = observe = 0
    worst_absolute = worst_hamming = 0
    witness = None
    for bits in product((0, 1), repeat=len(source.inputs)):
        assignment = dict(zip(source.inputs, bits, strict=True))
        f = scalar_values(source, assignment, [candidate])[candidate] ^ int(invert)
        base = scalar_values(optimized, assignment, [target, *optimized.outputs])
        changed = scalar_values(optimized, assignment, optimized.outputs, {target: f})
        toggled = scalar_values(optimized, assignment, optimized.outputs, {target: 1 - base[target]})
        d = int(f != base[target])
        errors = [int(base[y] != changed[y]) for y in optimized.outputs]
        output_error = int(any(errors))
        o = int(any(base[y] != toggled[y] for y in optimized.outputs))
        if output_error != d * o:
            raise AssertionError("observability identity failed")
        delta = abs(sum((base[y] - changed[y]) * (1 << i) for i, y in enumerate(optimized.outputs)))
        disagree += d
        contextual += output_error
        observe += o
        hamming += sum(errors)
        absolute += delta
        worst_hamming = max(worst_hamming, sum(errors))
        worst_absolute = max(worst_absolute, delta)
        if output_error and witness is None:
            witness = assignment
    return dict(distance=disagree / count, contextual_error=contextual / count,
                observability=observe / count, output_hamming=hamming / count,
                mae=absolute / count, wce=worst_absolute, worst_hamming=worst_hamming,
                witness=witness)
