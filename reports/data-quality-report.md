# Data quality report

Source: real UCI Online Retail transactions; all countries retained. These are sales, not unconstrained demand.

| Check | Measured result |
|---|---:|
| Raw records | 541,909 |
| Retained positive-sales records | 520,893 |
| Removed records (all rules) | 21,016 |
| Exact duplicate rows removed | 5,268 |
| Cancellation rows after deduplication | 9,251 |
| Negative-quantity rows after deduplication | 10,587 |
| Return/cancellation union | 10,587 |
| Final partial-day rows excluded | 1,611 |
| Clean product count | 3,790 |
| Selected products | 25 |
| Selected daily rows | 9,323 |
| Zero-sales daily fraction | 21.71% |
| Mean daily sales / maximum | 49.62 / 4314 |

Retained observation dates: 2010-12-01 to 2011-12-08. Source ends at 2011-12-09 12:50:00; the final date is excluded by the predeclared completeness rule.

## Rules and reconciliation

Exact duplicate source rows are removed before identifiers are dropped. This is an assumption: identical legitimate purchases could be removed. Cancellation invoice prefixes and negative quantities are excluded, never made positive or subtracted from demand. Then remove non-six-digit invoices, product codes outside five digits plus up to two letters (excluding postage, fees and adjustments), invalid dates, nonpositive/nonfinite/noninteger quantities and nonpositive/nonfinite prices. Rules run in that order; diagnostic return counts overlap, removal counts below do not.

| rule                  |   rows_removed |
|:----------------------|---------------:|
| returns_cancellations |          10587 |
| invalid_invoice       |              3 |
| invalid_product_code  |           2391 |
| invalid_date          |              0 |
| invalid_quantity      |              0 |
| invalid_price         |           1156 |

Missing raw values: {'InvoiceNo': 0, 'StockCode': 0, 'Description': 1454, 'Quantity': 0, 'InvoiceDate': 0, 'UnitPrice': 0, 'CustomerID': 135080, 'Country': 0}. Missing customer IDs do not remove sales; no customer IDs are exported. Missing descriptions are retained; a training-only modal normalized description supplies catalog labels, with product code fallback. Descriptions are uppercased and whitespace normalized. Price proxies use training-only median retail price. No outlier clipping or retrospective product removal is used.

Selection uses only data through 2011-08-18, before the earliest development validation. Require 90 active days and 180 calendar days of history; rank by active days, units, then code. Keep 25. Each selected product is padded with zero recorded sales from its first training-observed sale through the common end date. Pre-listing days are excluded. A zero does not establish zero customer demand or stock availability. Closed days, missing records, and stockouts are indistinguishable here.

## Selected catalog (training-only metadata)

| product_id   |   active_days |   training_units | first_sale          |   median_retail_price |   history_days | product_name                       | metadata_cutoff   |
|:-------------|--------------:|-----------------:|:--------------------|----------------------:|---------------:|:-----------------------------------|:------------------|
| 85123A       |           209 |            27057 | 2010-12-01 00:00:00 |                  2.95 |            261 | WHITE HANGING HEART T-LIGHT HOLDER | 2011-08-18        |
| 22423        |           206 |            10204 | 2010-12-01 00:00:00 |                 12.75 |            261 | REGENCY CAKESTAND 3 TIER           | 2011-08-18        |
| 22457        |           206 |             5790 | 2010-12-01 00:00:00 |                  2.95 |            261 | NATURAL SLATE HEART CHALKBOARD     | 2011-08-18        |
| 85099B       |           204 |            29346 | 2010-12-01 00:00:00 |                  2.08 |            261 | JUMBO BAG RED RETROSPOT            | 2011-08-18        |
| 21212        |           204 |            27153 | 2010-12-01 00:00:00 |                  0.55 |            261 | PACK OF 72 RETROSPOT CAKE CASES    | 2011-08-18        |
| 84879        |           204 |            22834 | 2010-12-01 00:00:00 |                  1.69 |            261 | ASSORTED COLOUR BIRD ORNAMENT      | 2011-08-18        |
| 20725        |           203 |            13529 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG RED RETROSPOT            | 2011-08-18        |
| 22960        |           202 |             5777 | 2010-12-01 00:00:00 |                  4.25 |            261 | JAM MAKING SET WITH JARS           | 2011-08-18        |
| 21080        |           201 |             9855 | 2010-12-01 00:00:00 |                  0.85 |            261 | SET/20 RED RETROSPOT PAPER NAPKINS | 2011-08-18        |
| 82482        |           201 |             5634 | 2010-12-01 00:00:00 |                  2.55 |            261 | WOODEN PICTURE FRAME WHITE FINISH  | 2011-08-18        |
| 47566        |           200 |            14857 | 2010-12-03 00:00:00 |                  4.95 |            259 | PARTY BUNTING                      | 2011-08-18        |
| 20728        |           200 |             8329 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG CARS BLUE                | 2011-08-18        |
| 22666        |           200 |             4708 | 2010-12-01 00:00:00 |                  2.95 |            261 | RECIPE BOX PANTRY YELLOW DESIGN    | 2011-08-18        |
| 22197        |           198 |            26987 | 2010-12-01 00:00:00 |                  0.85 |            261 | SMALL POPCORN HOLDER               | 2011-08-18        |
| 22178        |           198 |            16151 | 2010-12-01 00:00:00 |                  1.25 |            261 | VICTORIAN GLASS HANGING T-LIGHT    | 2011-08-18        |
| 22384        |           198 |             7819 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG PINK POLKADOT            | 2011-08-18        |
| 22697        |           198 |             4825 | 2010-12-01 00:00:00 |                  2.95 |            261 | GREEN REGENCY TEACUP AND SAUCER    | 2011-08-18        |
| 22386        |           196 |            12436 | 2010-12-01 00:00:00 |                  2.08 |            261 | JUMBO BAG PINK POLKADOT            | 2011-08-18        |
| 20727        |           196 |             7712 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG BLACK SKULL.             | 2011-08-18        |
| 22727        |           196 |             3364 | 2010-12-01 00:00:00 |                  3.75 |            261 | ALARM CLOCK BAKELIKE RED           | 2011-08-18        |
| 21754        |           196 |             2063 | 2010-12-01 00:00:00 |                  5.95 |            261 | HOME BUILDING BLOCK WORD           | 2011-08-18        |
| 22383        |           195 |             9131 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG SUKI DESIGN              | 2011-08-18        |
| 22077        |           195 |             5134 | 2010-12-01 00:00:00 |                  1.65 |            261 | 6 RIBBONS RUSTIC CHARM             | 2011-08-18        |
| 20724        |           194 |            10611 | 2010-12-01 00:00:00 |                  0.85 |            261 | RED RETROSPOT CHARLOTTE BAG        | 2011-08-18        |
| 20726        |           194 |             7225 | 2010-12-01 00:00:00 |                  1.65 |            261 | LUNCH BAG WOODLAND                 | 2011-08-18        |

Machine-readable evidence: `data-quality-summary.json`; source provenance and SHA-256: `../data/source-manifest.json`. Essential gates fail loudly for missing schema, insufficient history, fewer than 25 eligible products, invalid daily values, or duplicate keys.
