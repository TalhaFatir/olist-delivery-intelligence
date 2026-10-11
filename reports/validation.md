# Validation Record

Checked October 11, 2026.

| Check | Result |
|---|---|
| Original input | Kaggle public dataset archive; SHA-256 and per-file hashes in source-manifest.json |
| Source keys | Unique orders, customers, products, sellers and order/item keys; joins checked |
| Fact grain | 99,441 unique orders, no item/review join multiplication |
| Eligible deliveries | 96,470; eight delivered records fail date checks |
| Late deliveries | 6,534; calendar-date promise comparison |
| Review resolution | Latest answered review per order; deterministic tie-break; 551 rows beyond one per order |
| Financial reconciliation | Item value and freight charges equal raw item totals to the cent |
| Python tests | 8 passed: six source/SQL tests plus native review-filter and chronological-sort regressions |
| JavaScript tests | 6 passed: syntax, browser/SQL totals, empty selection, quantiles/filters, seller queue, state partitions |
| Desktop preview | 1280px default browser width; charts render and no page-level horizontal overflow |
| Mobile preview | 390 x 844 and 320 x 740; no page-level horizontal overflow |
| Filter interaction | 2018 + SP returns 23,871 orders; seller queue returns 33 qualifying sellers |
| Seller queue | Search, empty search result, pagination and reset checked |
| Review mode | Low-review and mean-score modes checked |
| Empty slice | 2016 / AC / Security And Services returns 0 orders and N/A for rates/quantiles |
| Static downloads | Clean CSV, SQL, decision brief and manifest endpoints return HTTP 200 |
| Dynamic filtered export | Button exercised; automated download event timed out, so final browser download completion is not verified |
| Power BI generated source | 48 official-schema documents passed; 40 visual layouts and model references checked; 99,441 source rows and exact financial totals reconciled |
| Power BI runtime | Desktop refreshed and all three pages rendered; on time 93.2%, late 6,534, P90 23.1 days; reviewed late 6,381 / low 3,983, on time 89,443 / low 8,289; matching published service metrics verified |
| Public Power BI | Publish-to-web success confirmed; public view renders overview and corrected review shares without an authentication prompt; three-page navigation available |
| Power BI saved source | Desktop saved 40 visuals; model references, exact source totals and layout passed structural checks. Generated source passed 48 schema documents before Desktop upgraded report schemas; not a full schema validation of Desktop's saved format |
| GitHub | Public TalhaFatir/olist-delivery-intelligence upload verified; commit author Talha Fatir <talha01677@gmail.com> |

Browser QA initially identified an application syntax error; repaired and a script-parsing test added. Final dashboard rendered, and filters/views were checked after repair. Local file delivery uses script-loaded data, not fetch. No statistical causal inference, experiment results or realized operational savings are claimed.

Native runtime QA caught a review-score filter replacement: the reviewed-delivery denominator now uses KEEPFILTERS so 1-2-star restrictions intersect rather than disappear. Verified low-review shares are 62.4% late versus 9.3% on time. Chronological month sorting and descending seller late-count sorting are explicit.
