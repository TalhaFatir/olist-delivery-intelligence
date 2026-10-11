# Olist Delivery Intelligence | SQL & Power BI

**Talha Fatir | Economics graduate, University of Calgary**

**SQL (SQLite) | Power BI | DAX | Power Query | Business Analysis**

Independent business analytics using real, anonymized historical Olist marketplace transactions. Not a fictional dataset, not work commissioned by Olist, and not a claim of implemented business outcomes.

## Live Power BI Dashboard

**[Open the interactive report](https://app.powerbi.com/view?r=eyJrIjoiMDhhOTAyZWUtOTgxYy00NTlmLTk1MTgtZjJkYTg1MzRmMGE3IiwidCI6ImM3MzNiYzhmLWMwODYtNGFhYS05YmQ4LTZiZjZhMTRiYWJjMSJ9)** | Public viewing, no sign-in required.

Three pages: Delivery Overview, Seller Priorities, and Evidence & Scope. Filter by purchase year, customer state and order category. This public report and its semantic model contain derived public Olist data only. Historical Brazil, 2016-2018; source attribution and measurement boundaries below.

## Business Question
Where are deliveries missing customer expectations, how do reviews differ, and which sellers warrant operational investigation?

## SQL Analysis and Power BI Reporting

SQL is part of the executed analysis pipeline, not just a sample file. The cleaned order-grain data is loaded into SQLite, and `sql/analysis.sql` creates three views:

- `monthly_delivery`: delivery volume, late rate and item value by purchase month.
- `delivery_reviews`: review scores and low-review shares for late versus on-time deliveries.
- `seller_priority`: single-seller groups with at least 100 eligible deliveries, ranked by late-order count.

The build executes these views to generate findings and dashboard outputs. Power BI imports the cleaned CSV through Power Query and calculates interactive metrics in DAX; it does not use a direct SQLite connection.

Example queries against the generated SQLite database:

```sql
SELECT delivery_group, reviewed_orders, avg_score, low_review_pct
FROM delivery_reviews;

SELECT seller, eligible_orders, late_orders, late_pct
FROM seller_priority
ORDER BY late_orders DESC, seller
LIMIT 10;
```

| Delivery group | Reviewed orders | Average score | 1-2 star share |
|---|---:|---:|---:|
| Late | 6,381 | 2.27 / 5 | 62.42% |
| On time | 89,443 | 4.29 / 5 | 9.27% |

## Findings Across the Full Extract
- 99,441 orders; 96,470 eligible delivered orders.
- 6,534 late deliveries: 6.77% of eligible deliveries, using calendar-date promises.
- Reviewed late orders average 2.27/5 versus 4.29/5 on time.
- 1-2-star reviews account for 62.42% of reviewed late orders versus 9.27% on time.
- These are descriptive associations, not proof that delay caused dissatisfaction.

## Deliverables
- `powerbi/OlistDelivery.pbip`: native three-page Power BI report with slicers, seller priorities and evidence.
- `powerbi/measures.dax`: delivery, review and seller metrics used in the report.
- `sql/analysis.sql`: executed monthly performance, review comparison and seller priority views.
- `data/orders_clean.csv`: one row per order; integer-cent financial values.
- `data/olist.sqlite` (generated, not tracked): queryable order-grain database.
- `reports/decision-brief.md`: evidence, proposed actions and limitations.
- `reports/business-requirements.md`: stakeholder requirements and acceptance criteria.
- `src/build_powerbi.py` and `src/validate_powerbi.py`: reproducible native report generation and source-contract/layout checks.
- `data/source-manifest.json`: exact input row counts, SHA-256 hashes and quality checks.

## Source and License
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), Olist and collaborators, **CC BY-NC-SA 4.0**. Retrieved October 11, 2026. The source archive was downloaded from Kaggle's public dataset API, not an unverified mirror. Data covers Brazil, 2016-2018; it is not current Canadian business data. Values are nominal Brazilian reais (BRL).

Derived tables, charts and analysis retain CC BY-NC-SA 4.0. Original project code is also provided under that license. Third-party libraries retain their own licenses. Source CSVs remain unchanged locally in ignored `data/raw/`; generated dashboard extracts omit customer identifiers, precise locations and review text. See `LICENSE.md` and `THIRD-PARTY-NOTICES.md`.

## Reproduce
For the native report, open `powerbi/OlistDelivery.pbip` and follow the [Power BI setup guide](powerbi/README.md). The imported CSV is included. For source preparation, SQLite execution and verification, see the [reproducibility guide](reports/reproducibility.md). Supporting scripts prepare and validate the data; the primary portfolio deliverable is the SQL analysis and published Power BI report.

## Measurement Boundaries
Delivery KPIs include delivered orders with valid purchase/delivery/promise dates. Same-day arrival is on time. Eight delivered records fail eligibility checks. Open/failed orders do not enter the delivery denominator; this is not an all-order SLA success rate. Partial edge months and incomplete end-of-extract follow-up are not extrapolated.

Multiple reviews resolve to the latest answered review per order, with deterministic timestamp/ID/score tie-breaks. Financial values aggregate all items before order-level joins, avoiding multiplication by item or review rows. Mixed categories and multiple sellers remain explicit groups; seller ranking excludes multiple-seller orders. Seller aliases are generated analytical labels, not company names. Item value is GMV, not Olist revenue or profit. Freight charges are not verified carrier costs. Review comparison excludes missing reviews and does not control for confounding or voluntary response bias.

## Scope
This project demonstrates SQL, metric design, operational analysis, data validation, interactive reporting and business requirements. The native report has been refreshed and verified in Desktop, published to Power BI Service, and checked through its public viewing link on October 11, 2026.
