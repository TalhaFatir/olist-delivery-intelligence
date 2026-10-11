-- One row per order. Item values and reviews are resolved before joining.
CREATE VIEW monthly_delivery AS
SELECT month, count(*) AS orders, sum(eligible) AS eligible_orders,
       sum(late) AS late_orders,
       round(100.0*sum(late)/nullif(sum(eligible),0),2) AS late_pct,
       round(avg(CASE WHEN eligible=1 THEN delivery_days END),2) AS avg_days,
       round(sum(item_cents)/100.0,2) AS item_value_brl
FROM facts GROUP BY month;

CREATE VIEW delivery_reviews AS
SELECT CASE late WHEN 1 THEN 'Late' WHEN 0 THEN 'On time' END AS delivery_group,
       count(*) AS reviewed_orders, round(avg(review_score),3) AS avg_score,
       sum(CASE WHEN review_score<=2 THEN 1 ELSE 0 END) AS low_reviews,
       round(100.0*sum(CASE WHEN review_score<=2 THEN 1 ELSE 0 END)/count(*),2) AS low_review_pct
FROM facts WHERE eligible=1 AND review_score IS NOT NULL GROUP BY late;

CREATE VIEW seller_priority AS
SELECT seller, count(*) AS eligible_orders, sum(late) AS late_orders,
       round(100.0*sum(late)/count(*),2) AS late_pct,
       round(avg(delivery_days),2) AS avg_days,
       count(review_score) AS reviewed_orders, round(avg(review_score),2) AS avg_score
FROM facts WHERE eligible=1 AND seller NOT IN ('Multiple sellers','No seller')
GROUP BY seller HAVING count(*)>=100 ORDER BY late_orders DESC, seller;
