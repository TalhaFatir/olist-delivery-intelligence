# Native Power BI Report

Open `OlistDelivery.pbip` in Power BI Desktop with PBIP/PBIR support. Before refreshing on another computer, change the `DataFolder` Power Query parameter to the absolute path of `powerbi/data`. Local credentials and imported caches are excluded from Git. The order-grain CSV is bundled; integer financial cents are divided by 100 for BRL. Empty numeric fields become null, not zero.

Measures are included in the semantic model and exported to `measures.dax`. Each page has independent year/state/category slicers. Review comparison includes eligible deliveries with nonblank review scores. Seller measures exclude 'Multiple sellers' and 'No seller' and require at least 100 eligible deliveries in the selected context.

Three built pages: Delivery Overview, Seller Priorities, Evidence & Scope. Item value is GMV, not Olist revenue; freight charged is not verified carrier cost. Review differences are associations, not causal effects. Historical Brazil coverage, 2016-2018; Olist public dataset, CC BY-NC-SA 4.0. See the root README for source attribution and boundaries.

Rebuild: `python src/build_powerbi.py`. Optional full generated-source schema checks require `jsonschema` and `referencing`: `python src/validate_powerbi.py`. After Desktop saves a newer schema, `--structural-only` validates fields, totals and layout without claiming full schema validation. P90 uses nearest-rank logic, matching the browser rather than interpolated percentiles.

Publication status: all three pages refreshed and rendered in Desktop. Corrected review-filter context and source totals verified; saved-source structural checks passed. Public service publication is pending.
