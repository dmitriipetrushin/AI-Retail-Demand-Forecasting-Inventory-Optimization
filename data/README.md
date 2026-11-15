# Data provenance and preparation

Official source: [UCI Online Retail, dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail).

Citation: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33.

License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The source page was checked before the actual download. `source-manifest.json` records download time, license, source URL and archive/workbook SHA-256. Attribution applies to the processed derivatives too; the repository's MIT license applies to code and original documentation, not to the underlying dataset.

Run `python -m scripts.download_data` and `python -m scripts.prepare_data` from the project root. The approximately 23 MB workbook and archive live in ignored `raw/`. Only the small, daily product-level positive-sales derivative and training-only catalog are retained in `processed/`. No customer or invoice IDs are exported.

Modifications: exact duplicate removal; exclusion of cancellations, negative/invalid quantities, invalid invoice/product codes, invalid dates and nonpositive/nonfinite prices; normalization of product descriptions; exclusion of the final partial date; training-only eligibility/ranking of 25 products; daily aggregation and zero padding. See `reports/data-quality-report.md` for counts, rules, selected products and cutoffs.

All countries remain in the series; prices are nominal historical GBP. The data describes recorded sales of a non-store retailer with wholesale customers. Availability and stockout censoring are unknown, so sales and zero sales must not be interpreted as unconstrained demand. No synthetic fallback was used in this completed real-data study. If the official source is unavailable, checked-in processed data still supports the documented dashboard and artifact review; a fresh raw-data reproduction must wait for the source rather than claim a synthetic run as real.
