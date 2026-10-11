"""Generate a portable native Power BI project from the order-grain extract."""
import csv
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'powerbi'
REPORT = OUT / 'OlistDelivery.Report'
MODEL = OUT / 'OlistDelivery.SemanticModel'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def literal(value):
    return {'expr': {'Literal': {'Value': 'true' if value is True else 'false' if value is False else str(value)+'D' if isinstance(value, (float, int)) else "'"+str(value).replace("'", "''")+"'"}}}


def field(name, measure=False):
    return {'field': {'Measure' if measure else 'Column': {'Expression': {'SourceRef': {'Entity': 'Orders'}}, 'Property': name}}, 'queryRef': 'Orders.'+name, 'nativeQueryRef': name}


def build_model():
    with (ROOT/'data/orders_clean.csv').open(encoding='utf-8', newline='') as f:
        records = list(csv.DictReader(f))
    for r in records:
        r['year'] = r['month'][:4]
        r['delivery_group'] = 'Excluded' if r['eligible'] != '1' else 'Late' if r['late'] == '1' else 'On time'
    dest = OUT/'data/Orders.csv'
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    measures = []
    def add(name, expression, fmt='#,0', folder='Delivery'):
        measures.append({'name': name, 'expression': expression, 'formatString': fmt, 'displayFolder': folder})
    add('Order Count', 'COUNTROWS(Orders)')
    add('Eligible Deliveries', 'CALCULATE(COUNTROWS(Orders), Orders[eligible] = 1)')
    add('Late Deliveries', 'CALCULATE([Eligible Deliveries], Orders[late] = 1)')
    add('On Time Rate', 'DIVIDE([Eligible Deliveries] - [Late Deliveries], [Eligible Deliveries])', '0.0%')
    add('Late Rate', 'DIVIDE([Late Deliveries], [Eligible Deliveries])', '0.00%')
    add('Excluded Orders', 'CALCULATE(COUNTROWS(Orders), Orders[eligible] = 0)')
    add('Mean Delivery Days', 'CALCULATE(AVERAGE(Orders[delivery_days]), Orders[eligible] = 1)', '0.0')
    add('P90 Delivery Days', 'VAR T = FILTER(Orders, Orders[eligible] = 1 && NOT ISBLANK(Orders[delivery_days])) VAR N = COUNTROWS(T) RETURN IF(N > 0, MAXX(TOPN(ROUNDUP(N * 0.9, 0), T, Orders[delivery_days], ASC), Orders[delivery_days]))', '0.0')
    add('Reviewed Deliveries', 'CALCULATE([Eligible Deliveries], NOT ISBLANK(Orders[review_score]))', '#,0', 'Customer experience')
    add('Low Reviews', 'CALCULATE([Reviewed Deliveries], Orders[review_score] IN {1, 2})', '#,0', 'Customer experience')
    add('Low Review Rate', 'DIVIDE([Low Reviews], [Reviewed Deliveries])', '0.0%', 'Customer experience')
    add('Mean Review Score', 'CALCULATE(AVERAGE(Orders[review_score]), Orders[eligible] = 1)', '0.00', 'Customer experience')
    add('Item Value BRL', 'SUM(Orders[item_cents]) / 100', '"R$" #,0.00', 'Financial context')
    add('Freight Charged BRL', 'SUM(Orders[freight_cents]) / 100', '"R$" #,0.00', 'Financial context')
    qualifying = 'SELECTEDVALUE(Orders[seller]) <> "Multiple sellers" && SELECTEDVALUE(Orders[seller]) <> "No seller" && HASONEVALUE(Orders[seller]) && [Eligible Deliveries] >= 100'
    for n, source, fmt in [('Seller Eligible', 'Eligible Deliveries', '#,0'), ('Seller Late', 'Late Deliveries', '#,0'), ('Seller Late Rate', 'Late Rate', '0.0%'), ('Seller Mean Days', 'Mean Delivery Days', '0.0')]:
        add(n, f'IF({qualifying}, [{source}])', fmt, 'Seller investigation')
    for n, text in [
        ('Report Title', 'OLIST / Delivery Intelligence'),
        ('Source Note', 'Talha Fatir | Public Olist data | Brazil, 2016-2018 | CC BY-NC-SA 4.0'),
        ('Delivery Rule', 'Late = arrival calendar date after promise; valid delivered orders only.'),
        ('Review Rule', 'Latest answered review per order; missing reviews excluded. Association, not causation.'),
        ('Seller Rule', 'Single-seller orders only; at least 100 eligible deliveries in selection.'),
        ('Money Rule', 'Item value is GMV, not revenue. Freight charged is not verified carrier cost.'),
        ('Scope Rule', 'Historical Brazil extract; partial edge months. No current Canadian market claims.')]:
        add(n, '"'+text+'"', '', 'Context')
    ints = {'eligible', 'late', 'review_score', 'item_cents', 'freight_cents'}
    cols = [{'name': c, 'sourceColumn': c, 'dataType': 'int64' if c in ints else 'double' if c == 'delivery_days' else 'string', 'summarizeBy': 'none'} for c in records[0]]
    mtypes = {'string': 'type text', 'int64': 'Int64.Type', 'double': 'type number'}
    types = ', '.join('{"'+c['name']+'", '+mtypes[c['dataType']]+'}' for c in cols)
    numeric = ', '.join('"'+c['name']+'"' for c in cols if c['dataType'] != 'string')
    expr = ['let', ' Source = Csv.Document(File.Contents(DataFolder & "/Orders.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),', ' Headers = Table.PromoteHeaders(Source,[PromoteAllScalars=true]),', f' Nulls = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,{{{numeric}}}),', f' Typed = Table.TransformColumnTypes(Nulls,{{{types}}},"en-CA")', 'in', ' Typed']
    table = {'name': 'Orders', 'columns': cols, 'measures': measures, 'partitions': [{'name': 'Orders', 'mode': 'import', 'source': {'type': 'm', 'expression': expr}}]}
    write(MODEL/'model.bim', {'name': 'OlistDelivery', 'compatibilityLevel': 1600, 'model': {'culture': 'en-US', 'sourceQueryCulture': 'en-CA', 'defaultPowerBIDataSourceVersion': 'powerBI_V3', 'expressions': [{'name': 'DataFolder', 'kind': 'm', 'expression': '"'+(OUT/'data').as_posix()+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}], 'tables': [table]}})
    write(MODEL/'definition.pbism', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json', 'version': '1.0', 'settings': {}})
    (OUT/'measures.dax').write_text('\n\n'.join(m['name']+' =\n'+m['expression'] for m in measures), encoding='utf-8')


def build_report():
    definition = REPORT/'definition'
    write(OUT/'OlistDelivery.pbip', {'version': '1.0', 'artifacts': [{'report': {'path': 'OlistDelivery.Report'}}], 'settings': {'enableAutoRecovery': True}})
    write(REPORT/'definition.pbir', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json', 'version': '4.0', 'datasetReference': {'byPath': {'path': '../OlistDelivery.SemanticModel'}}})
    write(definition/'version.json', {'$schema': SCHEMA+'/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'})
    theme = {'name': 'Olist Delivery', 'dataColors': ['#147D81', '#DC6B59', '#768B61', '#A17BA5'], 'background': '#F5F7F7', 'foreground': '#253437', 'tableAccent': '#147D81'}
    write(REPORT/'StaticResources/RegisteredResources/OlistTheme.json', theme)
    write(definition/'report.json', {'$schema': SCHEMA+'/report/3.1.0/schema.json', 'themeCollection': {'customTheme': {'name': 'OlistTheme', 'type': 'RegisteredResources', 'reportVersionAtImport': {'visual': '2.1.0', 'page': '1.0.0', 'report': '3.1.0'}}}, 'resourcePackages': [{'name': 'RegisteredResources', 'type': 'RegisteredResources', 'items': [{'name': 'OlistTheme', 'path': 'OlistTheme.json', 'type': 'CustomTheme'}]}]})
    pages = [('delivery', '01 Delivery Overview'), ('sellers', '02 Seller Priorities'), ('evidence', '03 Evidence & Scope')]
    write(definition/'pages/pages.json', {'$schema': SCHEMA+'/pagesMetadata/1.0.0/schema.json', 'pageOrder': [p[0] for p in pages], 'activePageName': 'delivery'})
    for pageid, title in pages:
        page = definition/'pages'/pageid
        write(page/'page.json', {'$schema': SCHEMA+'/page/1.0.0/schema.json', 'name': pageid, 'displayName': title, 'displayOption': 'FitToPage', 'width': 1440, 'height': 900, 'objects': {'background': [{'properties': {'color': {'solid': {'color': literal('#F5F7F7')}}, 'transparency': literal(0)}}]}})
        index = 0
        def visual(kind, label, x, y, w, h, roles, objects=None):
            nonlocal index
            index += 1
            name = uuid.uuid5(uuid.NAMESPACE_URL, f'olist-delivery/{pageid}/{index}').hex[:20]
            config = {'visualType': kind, 'query': {'queryState': {r: {'projections': p} for r, p in roles.items()}}, 'visualContainerObjects': {'title': [{'properties': {'show': literal(bool(label)), 'text': literal(label), 'fontSize': literal(12), 'fontColor': {'solid': {'color': literal('#253437')}}}}], 'background': [{'properties': {'show': literal(True), 'color': {'solid': {'color': literal('#FFFFFF')}}, 'transparency': literal(0)}}]}}
            if objects:
                config['objects'] = objects
            write(page/'visuals'/name/'visual.json', {'$schema': SCHEMA+'/visualContainer/2.1.0/schema.json', 'name': name, 'position': {'x': x, 'y': y, 'width': w, 'height': h, 'z': index, 'tabOrder': index}, 'visual': config})
        def card(n, label, x, y, w, h, size=26):
            visual('card', label, x, y, w, h, {'Values': [field(n, True)]}, {'labels': [{'properties': {'fontSize': literal(size), 'color': {'solid': {'color': literal('#147D81')}}}}], 'categoryLabels': [{'properties': {'show': literal(False)}}]})
        def chart(kind, label, category, measure, x, y, w, h):
            visual(kind, label, x, y, w, h, {'Category': [field(category)], 'Y': [field(measure, True)]})
        def table(label, columns, measures, x, y, w, h):
            visual('tableEx', label, x, y, w, h, {'Values': [field(n) for n in columns]+[field(n, True) for n in measures]})
        card('Report Title', title, 32, 20, 650, 76, 23)
        for i, (c, label, width) in enumerate([('year', 'Purchase year', 150), ('state', 'Customer state', 180), ('category', 'Order category', 340)]):
            x = [710, 880, 1080][i]
            visual('slicer', label, x, 20, width, 76, {'Values': [field(c)]}, {'selection': [{'properties': {'singleSelect': literal(True), 'selectAllCheckboxEnabled': literal(False)}}], 'data': [{'properties': {'mode': literal('Dropdown')}}]})
        metrics = [('Order Count', 'Orders'), ('On Time Rate', 'On time | Eligible deliveries'), ('P90 Delivery Days', 'P90 purchase-to-delivery | Days'), ('Late Deliveries', 'Late deliveries')]
        if pageid == 'evidence':
            metrics = [('Order Count', 'Orders'), ('Eligible Deliveries', 'Eligible delivered orders'), ('Excluded Orders', 'Excluded from delivery KPIs'), ('Item Value BRL', 'Item value | GMV, not revenue')]
        for i, (n, label) in enumerate(metrics):
            card(n, label, 32+i*350, 120, 326, 110)
        if pageid == 'delivery':
            chart('lineChart', 'Late rate by purchase month | Eligible deliveries', 'month', 'Late Rate', 32, 255, 850, 275)
            chart('clusteredBarChart', '1-2 star share | Reviewed eligible deliveries', 'delivery_group', 'Low Review Rate', 910, 255, 498, 275)
            chart('clusteredColumnChart', 'Eligible delivery volume by purchase month', 'month', 'Eligible Deliveries', 32, 555, 850, 230)
            table('Review comparison | Missing scores excluded', ['delivery_group'], ['Reviewed Deliveries', 'Mean Review Score', 'Low Review Rate'], 910, 555, 498, 230)
        elif pageid == 'sellers':
            table('Seller investigation queue | At least 100 eligible single-seller orders', ['seller'], ['Seller Eligible', 'Seller Late', 'Seller Late Rate', 'Seller Mean Days'], 32, 255, 850, 465)
            chart('clusteredBarChart', 'Late delivery count by customer state', 'state', 'Late Deliveries', 910, 255, 498, 465)
            card('Seller Rule', 'Attribution boundary', 32, 745, 1376, 50, 12)
        else:
            table('Status reconciliation | All orders', ['status'], ['Order Count'], 32, 255, 650, 270)
            table('Delivery denominator reconciliation', ['delivery_group'], ['Order Count', 'Reviewed Deliveries'], 710, 255, 698, 270)
            for i, (n, label) in enumerate([('Delivery Rule', 'Eligibility'), ('Review Rule', 'Review resolution'), ('Money Rule', 'Financial scope'), ('Scope Rule', 'Interpretation')]):
                card(n, label, 32, 545+i*65, 1376, 55, 12)
        card('Source Note', 'Independent portfolio analysis | Not commissioned by Olist', 32, 820, 1376, 60, 11)


if __name__ == '__main__':
    build_model()
    build_report()
    print(f'Built 3 native pages: {OUT / "OlistDelivery.pbip"}')
