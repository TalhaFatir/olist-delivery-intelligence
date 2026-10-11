# Olist | Delivery Performance & Customer Experience

**Talha Fatir | Economics graduate, University of Calgary**

Independent business analytics using real, anonymized historical Olist marketplace transactions. Not a fictional dataset, not work commissioned by Olist, and not a claim of implemented business outcomes.

## Business Question
Where are deliveries missing customer expectations, how do reviews differ, and which sellers warrant operational investigation?

## Findings Across the Full Extract
- 99,441 orders; 96,470 eligible delivered orders.
- 6,534 late deliveries: 6.77% of eligible deliveries, using calendar-date promises.
- Reviewed late orders average 2.27/5 versus 4.29/5 on time.
- 1-2-star reviews account for 62.42% of reviewed late orders versus 9.27% on time.
- These are descriptive associations, not proof that delay caused dissatisfaction.

## Deliverables
- `dist/index.html`: local interactive dashboard, with year/state/category filters, seller priority queue, exports, metric definitions and evidence.
- `data/orders_clean.csv`: one row per order; integer-cent financial values.
- `data/olist.sqlite` (generated, not tracked): queryable order-grain database.
- `sql/analysis.sql`: monthly performance, review comparison and seller priority views.
- `reports/decision-brief.md`: evidence, proposed actions and limitations.
- `reports/business-requirements.md`: stakeholder requirements and acceptance criteria.
- `powerbi/OlistDelivery.pbip`: native three-page Power BI report, imported order-grain model and documented DAX measures.
- `src/build_powerbi.py` and `src/validate_powerbi.py`: reproducible native report generation and source-contract/layout checks.
- `data/source-manifest.json`: exact input row counts, SHA-256 hashes and quality checks.

## Source and License
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), Olist and collaborators, **CC BY-NC-SA 4.0**. Retrieved October 11, 2026. The source archive was downloaded from Kaggle's public dataset API, not an unverified mirror. Data covers Brazil, 2016-2018; it is not current Canadian business data. Values are nominal Brazilian reais (BRL).

Derived tables, charts and analysis retain CC BY-NC-SA 4.0. Original project code is also provided under that license. Third-party libraries retain their own licenses. Source CSVs remain unchanged locally in ignored `data/raw/`; generated dashboard extracts omit customer identifiers, precise locations and review text. See `LICENSE.md` and `THIRD-PARTY-NOTICES.md`.

## Reproduce
Download and extract the original Kaggle archive into `data/raw/`, keeping the archive as `olist-source.zip`. Python 3.10+ standard library is sufficient:

```powershell
python src/build.py
python -m unittest discover -s tests -p "test_*.py"
node --test tests/frontend.test.cjs
python src/build_powerbi.py
```

Open `dist/index.html` directly; it does not require an account or external API. For HTTP preview: `python -m http.server 5174 --directory dist --bind 127.0.0.1`.

## Measurement Boundaries
Delivery KPIs include delivered orders with valid purchase/delivery/promise dates. Same-day arrival is on time. Eight delivered records fail eligibility checks. Open/failed orders do not enter the delivery denominator; this is not an all-order SLA success rate. Partial edge months and incomplete end-of-extract follow-up are not extrapolated.

Multiple reviews resolve to the latest answered review per order, with deterministic timestamp/ID/score tie-breaks. Financial values aggregate all items before order-level joins, avoiding multiplication by item or review rows. Mixed categories and multiple sellers remain explicit groups; seller ranking excludes multiple-seller orders. Seller aliases are generated analytical labels, not company names. Item value is GMV, not Olist revenue or profit. Freight charges are not verified carrier costs. Review comparison excludes missing reviews and does not control for confounding or voluntary response bias.

## Scope
This project demonstrates SQL, metric design, operational analysis, data validation, interactive reporting and business requirements. Public Power BI publication is pending Desktop refresh and service verification.
