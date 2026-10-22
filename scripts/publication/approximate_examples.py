"""Recompute the presentation's two case studies from committed BLIF artifacts.

No generated measurements are modified. Tables group *all* PI assignments,
retaining multiplicities rather than treating the rare predicate as a fair PI.
"""
import csv
import hashlib
import json
from collections import Counter
from itertools import product

from analyze_blif_matches import parse_blif
from scripts.analysis.audit_approximate_distance import ROOT
from scripts.validation.approximate_oracle import oracle_pair, scalar_values


def verified_examples():
    folder = ROOT / 'results/formal_approximate_correspondence'
    def rows(name):
        with (folder / name).open() as stream:
            return list(csv.DictReader(stream))
    cases = {row['case_id']: row for row in rows('cases.csv')}
    measured = rows('candidates.csv')
    ranking = rows('ranking_queries.csv')
    examples = {}
    for family in ('reconvergent_mask', 'rare_observable'):
        case_id = f'heldout_{family}_0'
        case = cases[case_id]
        source, optimized = (parse_blif(ROOT / case[key]) for key in ('source', 'optimized'))
        drivers = {node.output: node for node in optimized.nodes}
        a = drivers['t'].inputs[0]
        rest = drivers['rare'].inputs
        b = next(name for name in optimized.inputs if name != a and name not in rest)
        pool = [row for row in measured if row['case_id'] == case_id]
        selected = next(row['top1_candidate'] for row in ranking if row['case_id'] == case_id and row['method'] == 'global')
        ancestor = case['lineage']
        stats = {}
        for candidate in (ancestor, selected):
            values = oracle_pair(source, optimized, 't', candidate)
            recorded = next(row for row in pool if row['candidate'] == candidate)
            for metric in ('distance', 'contextual_error', 'observability'):
                assert values[metric] == float(recorded[metric]), (case_id, candidate, metric)
            witness = json.loads(recorded['contextual_counterexample'])
            if witness:
                base = scalar_values(optimized, witness, optimized.outputs)
                replacement = scalar_values(source, witness, [candidate])[candidate]
                changed = scalar_values(optimized, witness, optimized.outputs, {'t': replacement})
                assert base != changed, (case_id, candidate, 'counterexample')
            stats[candidate] = dict(distance_count=round(values['distance'] * 256),
                                    contextual_count=round(values['contextual_error'] * 256),
                                    witness=witness)
        grouped = Counter()
        for bits in product((0, 1), repeat=len(source.inputs)):
            assignment = dict(zip(source.inputs, bits, strict=True))
            old = scalar_values(source, assignment, [ancestor, selected, *source.outputs])
            base = scalar_values(optimized, assignment, ['t', *optimized.outputs])
            assert all(old[y] == base[y] for y in source.outputs)
            rare = int(all(assignment[name] for name in rest))
            assert base['t'] == assignment[a]
            expected_ancestor = assignment[a] ^ (assignment[b] if family == 'reconvergent_mask' else rare)
            expected_selected = assignment[a] if family == 'reconvergent_mask' else assignment[a] ^ (rare & assignment[b])
            assert old[ancestor] == expected_ancestor and old[selected] == expected_selected
            y_ancestor = scalar_values(optimized, assignment, ['y'], {'t': old[ancestor]})['y']
            y_selected = scalar_values(optimized, assignment, ['y'], {'t': old[selected]})['y']
            key = (assignment[a], assignment[b], rare if family == 'rare_observable' else -1,
                   base['t'], old[ancestor], old[selected], base['y'], y_ancestor, y_selected)
            grouped[key] += 1
        table = [dict(zip(('a','b','r','t','ancestor','selected','y','y_ancestor','y_selected','multiplicity'), (*key, count), strict=True))
                 for key, count in sorted(grouped.items())]
        examples[family] = dict(case_id=case_id, a=a, b=b, rest=rest, ancestor=ancestor, selected=selected,
                                assignments=256, stats=stats, table=table,
                                artifacts={key:dict(path=case[key], sha256=hashlib.sha256((ROOT/case[key]).read_bytes()).hexdigest())
                                           for key in ('source','optimized')})
    return examples


if __name__ == '__main__':
    print(json.dumps(verified_examples(), indent=2))
