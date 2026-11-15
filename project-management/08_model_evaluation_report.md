# Measured model evaluation

Owner: Dmitry Petrushin. Independent implementation; no fictional role is claimed as an actual reviewer.

Selected **auto_ets** using three chronological development windows. Development WAPE **79.15%**, a **16.94%** relative reduction versus weekly seasonal naive. The predeclared 5% development gate **passed**.

Final untouched holdout 2011-11-11–2011-12-08: MAE **50.010**, RMSE **156.552**, WAPE **70.54%**, bias **-20.85%**, MASE **0.922**. 6 products have higher holdout WAPE than seasonal naive; no products were removed. Holdout improvement against naive is 34.58%. This result did not drive model reselection.

| phase       | model          |    wape |      mae |      rmse |     bias |    mase |
|:------------|:---------------|--------:|---------:|----------:|---------:|--------:|
| development | seasonal_naive | 0.95298 | 51.92238 | 138.43716 | -0.12247 | 1.04908 |
| development | moving_average | 0.92039 | 50.14697 | 117.06020 |  0.00815 | 1.01081 |
| development | auto_ets       | 0.79151 | 43.12496 | 112.23453 | -0.05925 | 0.87604 |
| development | croston_sba    | 0.91521 | 49.86453 | 117.46204 | -0.01324 | 0.99190 |
| holdout     | seasonal_naive | 1.07835 | 76.44857 | 224.78529 |  0.17253 | 1.27568 |
| holdout     | moving_average | 0.75776 | 53.72071 | 153.28720 | -0.13616 | 1.01142 |
| holdout     | auto_ets       | 0.70542 | 50.01043 | 156.55227 | -0.20851 | 0.92199 |
| holdout     | croston_sba    | 0.80463 | 57.04336 | 152.53864 | -0.00677 | 1.04745 |

Detailed formulas, undefined-metric handling, fold results, artifact integrity and limits: [forecast evaluation](../reports/forecast-evaluation.md). Product errors: [failure analysis](../reports/forecast-failure-analysis.md). Test status is recorded in the readiness decision rather than assumed from forecasting success.
