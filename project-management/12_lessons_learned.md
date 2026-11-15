# Lessons learned from the independent implementation

1. The UCI metadata's general missing-value description is not a substitute for checking the file: the workbook contains 1,454 missing descriptions and 135,080 missing customer IDs. Missing customer IDs do not invalidate sales, and identifiers are unnecessary for product-level forecasting.
2. Product choice is part of model leakage control. Catalog selection, modal descriptions and median retail-price assumptions were all computed before the earliest validation origin, not from the final dataset.
3. Daily completeness is a decision. The source stops at 12:50 on 2011-12-09. Excluding that final date avoids treating a partial day as a full low-sales observation, but removes real records and must be reported.
4. Relative model improvement and operational usefulness are different judgments. AutoETS passed the development hypothesis; absolute error, product-specific failures and stockout censoring still restrict confidence.
5. Mathematical feasibility is different from meeting every target. Zero purchasing is feasible under a zero budget because shortages are penalized rather than prohibited. Mandatory-order tests separately demonstrate true infeasibility.
6. Forecasting and allocation effects require separate comparators. B and C share a forecast; A and B share FIFO allocation. A cost reduction from C cannot be attributed entirely to the forecasting model.
7. Purchase expenditure over a short horizon can distort policy comparisons. The simulation reports closing/in-transit assets and an alternative asset-adjusted cost, along with service levels, rather than reducing the business case to one cost percentage.
8. Two initial leakage-test assertions failed because NumPy's generic equality helper received pandas Series. A small reproduction isolated the assertion API issue; array comparisons preserved the intended tests. Forecast code and the frozen protocol were not changed to make these tests pass.
9. Integrity checks make reporting harder to accidentally rewrite. The frozen protocol and initial holdout manifest protect reproducible evidence; later modeling work needs a separately labeled experiment.
10. A responsible implementation recommendation has three levels: a useful local demo, a conditional analytical pilot and a production NO-GO. Documentation should explain why each is justified rather than presenting a single optimistic deployment label.

These are observations from code, data and verification in this project. No fictional team feedback, stakeholder quotes, actual ROI or business adoption is claimed.
