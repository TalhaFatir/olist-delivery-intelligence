import csv
import importlib.util
import sqlite3
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'src/build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class AnalysisTests(unittest.TestCase):
    def test_promised_day_is_on_time(self):
        o={'order_status':'delivered','order_purchase_timestamp':'2018-01-01 10:00:00',
           'order_delivered_customer_date':'2018-01-03 23:59:59','order_estimated_delivery_date':'2018-01-03 00:00:00'}
        self.assertEqual(b.delivery_metrics(o)[:2],(1,0))
        o['order_delivered_customer_date']='2018-01-04 00:00:00'
        self.assertEqual(b.delivery_metrics(o)[:2],(1,1))
        o['order_status']='canceled'
        self.assertEqual(b.delivery_metrics(o),(0,None,None))

    def test_invalid_dates_excluded(self):
        o={'order_status':'delivered','order_purchase_timestamp':'2018-01-03 10:00:00',
           'order_delivered_customer_date':'2018-01-01 00:00:00','order_estimated_delivery_date':'2018-01-04 00:00:00'}
        self.assertEqual(b.delivery_metrics(o),(0,None,None))
        o['order_delivered_customer_date']=''
        self.assertEqual(b.delivery_metrics(o),(0,None,None))

    def test_review_latest_and_order_invariant(self):
        rows=[dict(order_id='x',review_id='a',review_answer_timestamp='2018-01-01',review_creation_date='2018-01-01',review_score='1'),
              dict(order_id='x',review_id='b',review_answer_timestamp='2018-01-02',review_creation_date='2018-01-01',review_score='5')]
        self.assertEqual(b.resolve_reviews(rows),{'x':5})
        self.assertEqual(b.resolve_reviews(rows[::-1]),{'x':5})

    def test_source_grain_and_values(self):
        with sqlite3.connect(ROOT/'data/olist.sqlite') as con:
            self.assertEqual(con.execute('SELECT count(*),count(distinct order_id) FROM facts').fetchone(),(99441,99441))
            self.assertEqual(con.execute('SELECT sum(eligible),sum(late) FROM facts').fetchone(),(96470,6534))
            self.assertEqual(con.execute('SELECT count(*) FROM facts WHERE eligible=0 AND (late IS NOT NULL OR delivery_days IS NOT NULL)').fetchone()[0],0)
            self.assertEqual(con.execute('SELECT count(*) FROM facts WHERE review_score NOT BETWEEN 1 AND 5 OR item_cents<0 OR freight_cents<0').fetchone()[0],0)

    def test_exact_financial_reconciliation(self):
        with (ROOT/'data/raw/olist_order_items_dataset.csv').open(newline='',encoding='utf-8') as f:
            rows=list(csv.DictReader(f))
        with sqlite3.connect(ROOT/'data/olist.sqlite') as con:
            actual=con.execute('SELECT sum(item_cents),sum(freight_cents) FROM facts').fetchone()
        self.assertEqual(actual,(sum(b.cents(r['price']) for r in rows),sum(b.cents(r['freight_value']) for r in rows)))

    def test_sql_review_denominators(self):
        with sqlite3.connect(ROOT/'data/olist.sqlite') as con:
            view=con.execute('SELECT sum(reviewed_orders),sum(low_reviews) FROM delivery_reviews').fetchone()
            direct=con.execute('SELECT count(*),sum(review_score<=2) FROM facts WHERE eligible=1 AND review_score IS NOT NULL').fetchone()
            self.assertEqual(view,direct)
            self.assertEqual(con.execute("SELECT count(*) FROM seller_priority WHERE eligible_orders<100 OR seller IN ('Multiple sellers','No seller')").fetchone()[0],0)

if __name__=='__main__':unittest.main()
