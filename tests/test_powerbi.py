"""Native source regressions; actual DAX execution is verified in Desktop."""
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PowerBITests(unittest.TestCase):
    def test_review_filter_is_intersected(self):
        model = json.loads((ROOT/'powerbi/OlistDelivery.SemanticModel/model.bim').read_text())
        measures = {m['name']: m['expression'] for m in model['model']['tables'][0]['measures']}
        self.assertIn('KEEPFILTERS(NOT ISBLANK(Orders[review_score]))', measures['Reviewed Deliveries'])
        with (ROOT/'powerbi/data/Orders.csv').open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        for group, expected in [('Late', (6381, 3983)), ('On time', (89443, 8289))]:
            reviewed = [r for r in rows if r['delivery_group'] == group and r['review_score']]
            low = sum(int(r['review_score']) <= 2 for r in reviewed)
            self.assertEqual((len(reviewed), low), expected)

    def test_explicit_chronological_sort(self):
        charts = []
        for path in (ROOT/'powerbi/OlistDelivery.Report/definition/pages/delivery/visuals').glob('*/visual.json'):
            v = json.loads(path.read_text())['visual']
            if v['visualType'] in {'lineChart', 'clusteredColumnChart'}:
                charts.append(v)
                sort = v['query']['sortDefinition']['sort'][0]
                self.assertEqual(sort['direction'], 'Ascending')
                self.assertEqual(sort['field']['Column']['Property'], 'month')
        self.assertEqual(len(charts), 2)


if __name__ == '__main__':
    unittest.main()
