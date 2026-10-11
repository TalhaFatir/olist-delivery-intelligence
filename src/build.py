"""Reproducible order-grain analysis of Olist's original public CSVs."""
import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
SOURCE = 'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce'


def read(name):
    with (RAW / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def cents(value):
    return int(Decimal(value) * 100)


def date(value):
    return datetime.fromisoformat(value) if value else None


def delivery_metrics(order):
    purchased = date(order['order_purchase_timestamp'])
    delivered = date(order['order_delivered_customer_date'])
    expected = date(order['order_estimated_delivery_date'])
    eligible = order['order_status'] == 'delivered' and all([purchased, delivered, expected])
    eligible = bool(eligible and delivered >= purchased and expected.date() >= purchased.date())
    if not eligible:
        return 0, None, None
    # Promises are calendar dates: delivery later on the promised day is on time.
    return 1, int(delivered.date() > expected.date()), round((delivered-purchased).total_seconds()/86400, 3)


def resolve_reviews(rows):
    selected = {}
    for r in rows:
        key = (r['review_answer_timestamp'], r['review_creation_date'], r['review_id'], int(r['review_score']))
        if r['order_id'] not in selected or key > selected[r['order_id']][0]:
            selected[r['order_id']] = (key, int(r['review_score']))
    return {k:v[1] for k,v in selected.items()}


def unique_index(rows, key):
    out = {r[key]:r for r in rows}
    assert len(out) == len(rows), f'Duplicate source key: {key}'
    return out


def run():
    names = ['olist_orders_dataset.csv','olist_customers_dataset.csv','olist_order_items_dataset.csv',
             'olist_order_reviews_dataset.csv','olist_products_dataset.csv','olist_sellers_dataset.csv',
             'product_category_name_translation.csv']
    source = {n:read(n) for n in names}
    orders = source[names[0]]
    unique_index(orders, 'order_id')
    customers = unique_index(source[names[1]], 'customer_id')
    products = unique_index(source[names[4]], 'product_id')
    sellers = unique_index(source[names[5]], 'seller_id')
    translation = {r['product_category_name']:r['product_category_name_english'] for r in source[names[6]]}
    reviews = resolve_reviews(source[names[3]])
    items = defaultdict(list)
    item_keys = set()
    order_ids = {r['order_id'] for r in orders}
    for r in source[names[2]]:
        assert r['order_id'] in order_ids and r['product_id'] in products and r['seller_id'] in sellers
        key = (r['order_id'], r['order_item_id'])
        assert key not in item_keys
        item_keys.add(key)
        items[r['order_id']].append(r)
    assert set(reviews) <= order_ids
    aliases = {key:f'Seller {i+1:04d}' for i,key in enumerate(sorted(sellers))}
    facts = []
    for o in orders:
        assert o['customer_id'] in customers
        basket = items[o['order_id']]
        categories = {translation.get(products[r['product_id']]['product_category_name'], 'unknown') for r in basket}
        seller_ids = {r['seller_id'] for r in basket}
        category = next(iter(categories)) if len(categories)==1 else 'multi_category' if categories else 'no_items'
        seller = aliases[next(iter(seller_ids))] if len(seller_ids)==1 else 'Multiple sellers' if seller_ids else 'No seller'
        eligible, late, days = delivery_metrics(o)
        facts.append((o['order_id'], o['order_purchase_timestamp'][:7], customers[o['customer_id']]['customer_state'],
                      category, seller, o['order_status'], eligible, late, days, reviews.get(o['order_id']),
                      sum(cents(r['price']) for r in basket), sum(cents(r['freight_value']) for r in basket)))
    db = ROOT/'data/olist.sqlite'
    with sqlite3.connect(db) as con:
        con.executescript('DROP VIEW IF EXISTS monthly_delivery; DROP VIEW IF EXISTS delivery_reviews; DROP VIEW IF EXISTS seller_priority; DROP TABLE IF EXISTS facts;')
        con.execute('CREATE TABLE facts(order_id TEXT PRIMARY KEY, month TEXT, state TEXT, category TEXT, seller TEXT, status TEXT, eligible INTEGER, late INTEGER, delivery_days REAL, review_score INTEGER, item_cents INTEGER, freight_cents INTEGER)')
        con.executemany('INSERT INTO facts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', facts)
        con.execute('CREATE INDEX segment_filter ON facts(month,state,category)')
        con.executescript((ROOT/'sql/analysis.sql').read_text())
        con.row_factory = sqlite3.Row
        def query(sql): return [dict(r) for r in con.execute(sql)]
        summary = query('SELECT count(*) orders,sum(eligible) eligible,sum(late) late,avg(CASE WHEN eligible=1 THEN delivery_days END) avg_days,sum(item_cents)/100.0 item_value_brl FROM facts')[0]
        review_summary = query('SELECT * FROM delivery_reviews')
        top = query('SELECT * FROM seller_priority LIMIT 10')
        monthly = query('SELECT * FROM monthly_delivery ORDER BY month')
    assert sum(r[10] for r in facts)==sum(cents(r['price']) for r in source[names[2]])
    assert sum(r[11] for r in facts)==sum(cents(r['freight_value']) for r in source[names[2]])
    quality = {
        'source':SOURCE,'license':'CC BY-NC-SA 4.0','retrieved':'2026-10-11',
        'archive_sha256':hashlib.sha256((RAW/'olist-source.zip').read_bytes()).hexdigest(),
        'files':{n:{'rows':len(source[n]),'sha256':hashlib.sha256((RAW/n).read_bytes()).hexdigest()} for n in names},
        'orders':len(facts),'eligible_orders':summary['eligible'],
        'excluded_delivery_orders':len(facts)-summary['eligible'],
        'review_rows_beyond_one_per_order':len(source[names[3]])-len(reviews),
        'orders_without_review':sum(r[9] is None for r in facts),
        'multi_seller_orders':sum(r[4]=='Multiple sellers' for r in facts),
        'multi_category_orders':sum(r[3]=='multi_category' for r in facts),
        'delivered_but_ineligible':sum(r[5]=='delivered' and not r[6] for r in facts),
        'item_value_reconciliation':'exact to source cents',
        'freight_reconciliation':'exact to source cents',
    }
    (ROOT/'data/source-manifest.json').write_text(json.dumps(quality,indent=2)+'\n')
    fields = ['order_id','month','state','category','seller','status','eligible','late','delivery_days','review_score','item_cents','freight_cents']
    for path in [ROOT/'data/orders_clean.csv',ROOT/'dist/downloads/orders_clean.csv']:
        with path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(fields);writer.writerows(facts)
    dimensions = [sorted({r[i] for r in facts}) for i in [1,2,3,4,5]]
    indices = [{v:i for i,v in enumerate(dim)} for dim in dimensions]
    compact = [[indices[i][r[i+1]] for i in range(5)]+[r[8],r[7],r[9],r[10],r[11]] for r in facts]
    payload = {'dimensions':dict(zip(['months','states','categories','sellers','statuses'],dimensions)),
               'rows':compact,'quality':quality,'summary':summary,'reviews':review_summary,'monthly':monthly}
    (ROOT/'dist/data.js').write_text('window.OLIST='+json.dumps(payload,separators=(',',':'),allow_nan=False)+';\n')
    late_pct = 100*summary['late']/summary['eligible']
    groups = {r['delivery_group']:r for r in review_summary}
    memo = f'''# Delivery Reliability: Decision Brief

Prepared by Talha Fatir. Independent historical analysis, not work commissioned by Olist.

## Observed Results
- {summary['orders']:,} source orders; {summary['eligible']:,} delivered orders with valid delivery dates qualify for delivery KPIs.
- {summary['late']:,} qualifying deliveries ({late_pct:.2f}%) arrived after the promised calendar date.
- Mean purchase-to-delivery time: {summary['avg_days']:.2f} days among eligible deliveries.
- Reviewed late deliveries average {groups['Late']['avg_score']:.3f}/5 versus {groups['On time']['avg_score']:.3f}/5 for reviewed on-time deliveries.
- Low reviews (1-2 stars): {groups['Late']['low_review_pct']:.2f}% late versus {groups['On time']['low_review_pct']:.2f}% on time. Denominators are {groups['Late']['reviewed_orders']:,} and {groups['On time']['reviewed_orders']:,} reviewed eligible orders respectively.

## Proposed Actions, Not Proven Benefits
1. Investigate high late-order counts among sellers with at least 100 eligible single-seller orders. Highest count in the full extract: {top[0]['seller']}, {top[0]['late_orders']:,} late / {top[0]['eligible_orders']:,} eligible. Aliases are analytical labels, not company names. Order-level delivery cannot attribute blame to a seller or carrier.
2. Separate approval, seller handoff and carrier transit in a follow-up investigation. This version measures end-to-end delivery only; do not label it carrier performance.
3. Pilot proactive updates for expected delays using information available before delivery. Define customer contact cost, complaint rate and repeat purchases before launch. No savings or causal uplift is estimated here.

## Limitations
Brazilian historical orders (2016-2018), not current Canadian market evidence. Delivered-only late rate omits open and failed orders. End-of-extract purchases may be incompletely observed. Partial early/late months are shown, not extrapolated. Reviews are voluntary; latest answered review per order is used, with deterministic tie-breaks. The delivery/review relationship is observational and may reflect other factors. Item value is not Olist revenue or profit; freight is a customer charge, not proven logistics cost. Mixed-category and multiple-seller orders remain separate groups. No raw review text, addresses or customer identifiers are exposed in the dashboard.

Source: {SOURCE}. Olist and collaborators, CC BY-NC-SA 4.0. Derived tables and analysis are shared under the same license. Currency: nominal BRL; no CAD conversion.
'''
    for path in [ROOT/'reports/decision-brief.md',ROOT/'dist/downloads/decision-brief.md']:
        path.write_text(memo,encoding='utf-8')
    (ROOT/'dist/downloads/analysis.sql').write_text((ROOT/'sql/analysis.sql').read_text())
    (ROOT/'dist/downloads/source-manifest.json').write_text(json.dumps(quality,indent=2)+'\n')
    print(json.dumps({'summary':summary,'reviews':review_summary,'quality':quality},indent=2))


if __name__=='__main__': run()
