"""Read-only checks for the fixed numerical claims and artifact-backed slides."""
import csv
import json
from collections import defaultdict
from html.parser import HTMLParser
from math import isclose

from scripts.analysis.audit_approximate_distance import ROOT
from scripts.publication.approximate_examples import verified_examples


class Deck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slides = []
        self.current = None
        self.in_notes = False
        self.sources = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and attrs.get('class') == 'slide':
            self.current = dict(title=attrs['data-title'], notes='', references=0)
            self.slides.append(self.current)
        if tag == 'aside' and attrs.get('class') == 'notes':
            self.in_notes = True
        if tag == 'a' and self.current:
            self.current['references'] += 1
            prefix = 'https://github.com/stefi19/aig_optimization_experiments/blob/main/'
            if attrs.get('href', '').startswith(prefix):
                self.sources.append(attrs['href'][len(prefix):])
    def handle_endtag(self, tag):
        if tag == 'aside':
            self.in_notes = False
        if tag == 'section':
            self.current = None
    def handle_data(self, data):
        if self.in_notes:
            self.current['notes'] += data


def check():
    folder = ROOT / 'results/formal_approximate_correspondence'
    def read(name):
        with (folder/name).open() as stream:
            return list(csv.DictReader(stream))
    ranks = {row['method']: row for row in read('ranking_summary.csv')
             if row['split'] == 'heldout' and row['family'] == 'all'}
    for method, hits in [('structural',10),('hybrid',6),('contextual',6),('global',4)]:
        assert isclose(float(ranks[method]['precision1']), hits/24), method
    cases = [row for row in read('cases.csv') if row['evidence'] == 'controlled_algebraic_rewrite']
    assert len(cases) == 48
    for split in ('development','heldout'):
        group = [row for row in cases if row['split'] == split]
        assert len(group) == 24 and sum(not row['lineage'] for row in group) == 4
    records = read('reconstruction.csv')
    groups = defaultdict(list)
    for row in records:
        groups[(row['split'],row['ordering'],int(row['budget']),int(row['seed']))].append(row)
    for (split,order,budget,seed), group in groups.items():
        assert len(group) == (10 if split == 'development' else 8)
        accepted = {row['target_id'] for row in group if row['accepted'] == '1'}
        assert len(accepted) == (1 if order == 'sampled_distance' or budget >= 64 else 0)
        if budget == 176 and order == 'enumeration':
            guided = groups[(split,'sampled_distance',budget,seed)]
            assert accepted == {row['target_id'] for row in guided if row['accepted'] == '1'}
    assert len({row['artifact_sha256'] for row in records if row['accepted'] == '1'}) == 1
    for order,checks,seconds in [('enumeration',8379,1.230),('sampled_distance',7417,1.238)]:
        group = [row for row in records if row['ordering'] == order and row['budget'] == '176']
        assert sum(int(row['exact_checks']) for row in group) == checks
        assert sum(int(row['formal_cec_calls']) for row in group) == 12
        assert abs(sum(float(row['runtime_seconds']) for row in group)-seconds) < .0005
    examples = verified_examples()
    assert examples == json.loads((ROOT/'docs/presentation/assets/approximate/verified_examples.json').read_text())
    for example in examples.values():
        assert sum(row['multiplicity'] for row in example['table']) == 256
    odc,rare = examples['reconvergent_mask'],examples['rare_observable']
    assert odc['stats'][odc['ancestor']]['distance_count'] == 128
    assert odc['stats'][odc['ancestor']]['contextual_count'] == 0
    assert rare['stats'][rare['ancestor']]['contextual_count'] == 4
    assert rare['stats'][rare['selected']]['contextual_count'] == 2
    parser = Deck(); parser.feed((ROOT/'docs/presentation/index.html').read_text())
    assert all((ROOT/source).is_file() for source in parser.sources)
    assert len(parser.slides) == 34
    assert all(len(slide['notes']) >= 200 and slide['references'] for slide in parser.slides)
    assert len({slide['title'] for slide in parser.slides}) == len(parser.slides)
    return dict(slides=len(parser.slides),artifact_examples=len(examples),assignments_per_example=256,status='passed')


if __name__ == '__main__':
    print(json.dumps(check()))
