"""Schema, source-contract and visual-layout checks; Desktop verification is separate."""
import csv
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'
CACHE=ROOT/'outputs/powerbi-schema-cache'


def schema(url):
    if not url.startswith('https://developer.microsoft.com/json-schemas/'):
        raise ValueError('Unexpected schema host')
    CACHE.mkdir(parents=True,exist_ok=True)
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if not path.exists():
        with urllib.request.urlopen(url.replace('/schema.embedded.json','/schema-embedded.json'),timeout=45) as response:
            path.write_text(json.dumps(json.load(response)),encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def run(structural_only=False):
    checked=0
    registry=Registry(retrieve=lambda uri:Resource.from_contents(schema(uri),default_specification=DRAFT7))
    report=OUT/'OlistDelivery.Report'
    for path in list(report.rglob('*.json'))+[report/'definition.pbir',OUT/'OlistDelivery.SemanticModel/definition.pbism']:
        if '.pbi' in path.parts:
            continue
        doc=json.loads(path.read_text())
        if '$schema' not in doc:continue
        if structural_only:continue
        errors=list(Draft7Validator(schema(doc['$schema']),registry=registry).iter_errors(doc))
        if errors:raise ValueError(f'{path.name}: {errors[0].json_path}: {errors[0].message}')
        checked+=1
    model=json.loads((OUT/'OlistDelivery.SemanticModel/model.bim').read_text())['model']
    tables={t['name']:t for t in model['tables']}
    data={}
    for name,table in tables.items():
        with (OUT/'data'/f'{name}.csv').open(newline='',encoding='utf-8') as stream:
            reader=csv.DictReader(stream)
            assert {c['sourceColumn'] for c in table['columns']}==set(reader.fieldnames),name
            data[name]=list(reader)
            assert data[name],name
    for r in model.get('relationships',[]):
        pk=[row[r['toColumn']] for row in data[r['toTable']]]
        assert len(pk)==len(set(pk)),r['name']
        assert {row[r['fromColumn']] for row in data[r['fromTable']]}<=set(pk),r['name']
    visuals=0
    for page in (report/'definition/pages').glob('*/page.json'):
        config=json.loads(page.read_text())
        positions=[]
        for path in (page.parent/'visuals').glob('*/visual.json'):
            v=json.loads(path.read_text());p=v['position'];visuals+=1
            assert 0<=p['x'] and p['x']+p['width']<=config['width']
            assert 0<=p['y'] and p['y']+p['height']<=config['height']
            for other in positions:
                assert not (p['x']<other['x']+other['width'] and other['x']<p['x']+p['width'] and p['y']<other['y']+other['height'] and other['y']<p['y']+p['height']),path
            positions.append(p)
            for role in v['visual']['query']['queryState'].values():
                for projection in role['projections']:
                    f=projection['field'];kind='Measure' if 'Measure' in f else 'Column';ref=f[kind]
                    table=tables[ref['Expression']['SourceRef']['Entity']]
                    assert ref['Property'] in {x['name'] for x in table.get('measures' if kind=='Measure' else 'columns',[])}
    rows=data['Orders']
    assert len(rows)==99441 and len({r['order_id'] for r in rows})==99441
    assert sum(r['eligible']=='1' for r in rows)==96470
    assert sum(r['late']=='1' for r in rows)==6534
    assert all(r['late']=='' and r['delivery_days']=='' for r in rows if r['eligible']=='0')
    assert sum(int(r['item_cents']) for r in rows)==1359164370
    result={'schema_files':checked,'schema_validation':'not requested' if structural_only else 'passed','tables':len(tables),'visuals':visuals,'order_rows':len(rows),'eligible':96470,'late':6534,'item_cents':1359164370}
    (OUT/'source-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--structural-only',action='store_true')
    run(parser.parse_args().structural_only)
