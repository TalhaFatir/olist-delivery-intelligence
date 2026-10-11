# Business Requirements and Acceptance Criteria

Author: Talha Fatir. Independent historical portfolio case; no real stakeholder consultation claimed.

## Decision Owners (Proposed)
Operations lead: prioritize investigation. Customer experience lead: compare observed review patterns. Business analyst: maintain metric definitions and reconcile source totals.

## Current Analysis Flow
Original CSVs -> schema/key checks -> item aggregation and latest-review resolution -> one-row-per-order fact table -> SQL views -> dashboard and decision brief.

## Requirements
| ID | Requirement | Acceptance criterion |
|---|---|---|
| BR-01 | Filter by year, customer state and category | KPI, chart, seller queue and selection export use identical filter predicates |
| BR-02 | Measure delivery reliability | Date-only promise comparison; missing/invalid/non-delivered orders excluded and counted |
| BR-03 | Compare review outcomes | Show group denominators; exclude absent reviews; define low reviews as scores 1-2 |
| BR-04 | Prioritize seller investigation | Single-seller orders only; default minimum 100 eligible orders; sortable count/rate/volume |
| BR-05 | Preserve financial totals | Order item value and freight charges reconcile exactly to input cents, without join multiplication |
| BR-06 | Support independent review | Original source URL, license, file hashes, SQL, cleaned CSV and decision memo available |
| BR-07 | Handle sparse selections | Empty selection shows N/A for undefined rates/quantiles, no NaN or misleading zeros |

## Proposed Pilot, Not an Executed Experiment
Randomize eligible orders forecast to be late using information available before delivery. Treatment receives a proactive status message, control gets current communication. Primary metric: complaint/contact rate. Guardrails: contact cost and unsubscribes. Secondary metric: later repeat purchases with a fixed follow-up window. Determine sample size from baseline and a predeclared minimum detectable effect before launch. Do not randomize using actual final delay, which is only known after the fact.

The provided historical extract has no executed randomized intervention and cannot establish pilot uplift or savings. This version does not train a delay prediction model.
