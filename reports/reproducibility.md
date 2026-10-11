# Reproducibility

## Source Preparation and SQL Execution

Download and extract the original Kaggle archive into `data/raw/`, keeping the archive as `olist-source.zip`. Python 3.10+ standard library is sufficient for the analysis pipeline.

```powershell
python src/build.py
python -m unittest discover -s tests -p "test_*.py"
```

`src/build.py` cleans and aggregates source records, loads one row per order into SQLite, executes `sql/analysis.sql`, and queries its views for monthly performance, review comparison and seller priorities. The database is generated at `data/olist.sqlite` and is not tracked in Git.

Using an installed SQLite client:

```sql
SELECT * FROM monthly_delivery ORDER BY month;
SELECT * FROM delivery_reviews;
SELECT * FROM seller_priority ORDER BY late_orders DESC, seller LIMIT 10;
```

## Native Power BI

```powershell
python src/build_powerbi.py
```

Open `powerbi/OlistDelivery.pbip`; set the `DataFolder` parameter to your absolute `powerbi/data` folder before refresh. Power Query imports the CSV; DAX provides interactive metrics. SQL is executed upstream, not through a live SQLite connector in Power BI.

Optional schema validation requires `jsonschema` and `referencing`:

```powershell
python src/validate_powerbi.py
```

After Desktop saves a newer schema version, `--structural-only` checks references, totals and nonoverlapping layout without claiming full schema validation.

## Optional Browser Companion

The `dist` folder is a separate HTML/CSS/JavaScript companion, not a Java application and not required to view the public Power BI report. Its frontend tests require Node.js:

```powershell
node --test tests/frontend.test.cjs
```

Open `dist/index.html` directly, or use `python -m http.server 5174 --directory dist --bind 127.0.0.1` for a local HTTP preview.
