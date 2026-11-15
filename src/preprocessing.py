"""Deterministic positive-sales preparation and training-only catalog selection."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.common import ROOT, config, sha256, write_json
from src.data_loader import load_raw


def clean_transactions(raw):
    required = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice"}
    if required - set(raw):
        raise ValueError(f"Missing essential columns: {required - set(raw)}")
    df = raw.copy()
    quality = {"raw_transactions": len(df), "missing_values": {c: int(v) for c, v in df.isna().sum().items()}}
    # Exact duplicates include original customer identity; identity is then discarded.
    duplicated = df.duplicated()
    quality["duplicates_removed"] = int(duplicated.sum())
    df = df.loc[~duplicated].copy()
    df["InvoiceNo"] = df.InvoiceNo.astype("string").str.strip().str.upper()
    df["StockCode"] = df.StockCode.astype("string").str.strip().str.upper()
    df["InvoiceDate"] = pd.to_datetime(df.InvoiceDate, errors="coerce")
    for column in ["Quantity", "UnitPrice"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["Description"] = df.Description.astype("string").str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    cancelled = df.InvoiceNo.str.startswith("C", na=False)
    negative = df.Quantity.lt(0)
    quality["cancellation_rows_after_dedup"] = int(cancelled.sum())
    quality["negative_quantity_rows_after_dedup"] = int(negative.sum())
    quality["return_or_cancellation_union"] = int((cancelled | negative).sum())
    # Sequential removal counts reconcile exactly to raw rows. Diagnostic counts can overlap.
    rules = [
        ("returns_cancellations", cancelled | negative),
        ("invalid_invoice", ~df.InvoiceNo.str.fullmatch(r"\d{6}", na=False)),
        ("invalid_product_code", ~df.StockCode.str.fullmatch(r"\d{5}[A-Z]{0,2}", na=False)),
        ("invalid_date", df.InvoiceDate.isna()),
        ("invalid_quantity", ~np.isfinite(df.Quantity) | df.Quantity.le(0) | df.Quantity.mod(1).ne(0)),
        ("invalid_price", ~np.isfinite(df.UnitPrice) | df.UnitPrice.le(0)),
    ]
    keep = pd.Series(True, index=df.index)
    removed = {}
    for name, invalid in rules:
        invalid = invalid.fillna(True)
        removed[name] = int((keep & invalid).sum())
        keep &= ~invalid
    clean = df.loc[keep, ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice"]].copy()
    clean["date"] = clean.InvoiceDate.dt.normalize()
    clean = clean.rename(columns={"StockCode": "product_id", "Quantity": "units", "UnitPrice": "retail_price", "Description": "product_name"})
    quality.update({"sequential_removed": removed, "valid_transactions_before_partial_day_exclusion": len(clean),
                    "removed_transactions_before_partial_day_exclusion": len(raw) - len(clean)})
    if clean.empty or clean.date.nunique() < 120:
        raise ValueError("Essential data-quality gate failed: empty or insufficient dated sales history")
    return clean, quality


def split_dates(end, cfg):
    holdout_start = pd.Timestamp(end) - pd.Timedelta(days=cfg["primary_horizon"] - 1)
    first_validation = holdout_start - pd.Timedelta(days=cfg["backtest_windows"] * cfg["primary_horizon"])
    return {"history_end": str(pd.Timestamp(end).date()), "holdout_start": str(holdout_start.date()),
            "selection_cutoff": str((first_validation - pd.Timedelta(days=1)).date())}


def select_products(clean, cutoff, cfg):
    # Catalog labels, retail price proxies, ranking and eligibility only see this prefix.
    train = clean.loc[clean.date.le(pd.Timestamp(cutoff))]
    stats = train.groupby("product_id").agg(active_days=("date", "nunique"), training_units=("units", "sum"), first_sale=("date", "min"), median_retail_price=("retail_price", "median"))
    stats["history_days"] = (pd.Timestamp(cutoff) - stats.first_sale).dt.days + 1
    eligible = stats.loc[(stats.active_days >= cfg["min_active_days"]) & (stats.history_days >= cfg["min_history_days"])]
    selected = eligible.reset_index().sort_values(["active_days", "training_units", "product_id"], ascending=[False, False, True]).head(cfg["products"]).copy()
    if len(selected) < cfg["products"]:
        raise ValueError(f"Only {len(selected)} eligible products; need {cfg['products']}. Do not silently relax selection.")
    names = train.dropna(subset=["product_name"])
    names = names.loc[names.product_name.ne("")].groupby(["product_id", "product_name"]).size().rename("n").reset_index()
    names = names.sort_values(["product_id", "n", "product_name"], ascending=[True, False, True]).drop_duplicates("product_id").set_index("product_id").product_name
    selected["product_name"] = selected.product_id.map(names).fillna(selected.product_id)
    selected["metadata_cutoff"] = str(pd.Timestamp(cutoff).date())
    return selected


def aggregate_daily(clean, catalog, end):
    blocks = []
    for product in catalog.itertuples():
        dates = pd.date_range(product.first_sale, end, freq="D")
        sales = clean.loc[clean.product_id.eq(product.product_id)].groupby("date").units.sum()
        blocks.append(pd.DataFrame({"product_id": product.product_id, "date": dates,
                                    "units": sales.reindex(dates, fill_value=0).to_numpy()}))
    daily = pd.concat(blocks, ignore_index=True)
    if daily.duplicated(["product_id", "date"]).any() or daily.units.lt(0).any() or not np.isfinite(daily.units).all():
        raise ValueError("Daily validation failed: duplicate keys or invalid unit sales")
    return daily


def prepare():
    cfg = config()
    raw = load_raw()
    clean, quality = clean_transactions(raw)
    end = clean.date.max()
    quality["source_last_timestamp"] = str(clean.InvoiceDate.max())
    quality["partial_day_rows_excluded"] = 0
    if cfg["exclude_last_calendar_day"]:
        quality["partial_day_rows_excluded"] = int(clean.date.eq(end).sum())
        clean = clean.loc[clean.date.lt(end)].copy()
        end -= pd.Timedelta(days=1)
    dates = split_dates(end, cfg)
    catalog = select_products(clean, dates["selection_cutoff"], cfg)
    daily = aggregate_daily(clean, catalog, end)
    quality.update({"valid_transactions": len(clean), "removed_transactions": len(raw) - len(clean),
                    "products_after_cleaning": int(clean.product_id.nunique()), "selected_products": catalog.product_id.tolist(),
                    "date_start": str(clean.date.min().date()), "date_end": str(end.date()), **dates,
                    "daily_rows": len(daily), "zero_sales_fraction": float(daily.units.eq(0).mean()),
                    "selected_daily_mean": float(daily.units.mean()), "selected_daily_max": float(daily.units.max()),
                    "customer_ids_exported": False, "source_type": "UCI real historical transactions",
                    "quality_pass": bool(len(raw) == len(clean) + len(raw) - len(clean) and len(catalog) == cfg["products"])})
    folder = ROOT / "data/processed"
    folder.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(folder / "products.csv", index=False)
    daily.to_csv(folder / "daily_sales.csv", index=False)
    quality["daily_sha256"] = sha256(folder / "daily_sales.csv")
    quality["catalog_sha256"] = sha256(folder / "products.csv")
    write_json(ROOT / "reports/data-quality-summary.json", quality)
    (ROOT / "reports/data-quality-report.md").write_text(data_quality_markdown(quality, catalog))
    return quality


def data_quality_markdown(q, catalog):
    return f"""# Data quality report

Source: real UCI Online Retail transactions; all countries retained. These are sales, not unconstrained demand.

| Check | Measured result |
|---|---:|
| Raw records | {q['raw_transactions']:,} |
| Retained positive-sales records | {q['valid_transactions']:,} |
| Removed records (all rules) | {q['removed_transactions']:,} |
| Exact duplicate rows removed | {q['duplicates_removed']:,} |
| Cancellation rows after deduplication | {q['cancellation_rows_after_dedup']:,} |
| Negative-quantity rows after deduplication | {q['negative_quantity_rows_after_dedup']:,} |
| Return/cancellation union | {q['return_or_cancellation_union']:,} |
| Final partial-day rows excluded | {q['partial_day_rows_excluded']:,} |
| Clean product count | {q['products_after_cleaning']:,} |
| Selected products | {len(catalog)} |
| Selected daily rows | {q['daily_rows']:,} |
| Zero-sales daily fraction | {q['zero_sales_fraction']:.2%} |
| Mean daily sales / maximum | {q['selected_daily_mean']:.2f} / {q['selected_daily_max']:.0f} |

Retained observation dates: {q['date_start']} to {q['date_end']}. Source ends at {q['source_last_timestamp']}; the final date is excluded by the predeclared completeness rule.

## Rules and reconciliation

Exact duplicate source rows are removed before identifiers are dropped. This is an assumption: identical legitimate purchases could be removed. Cancellation invoice prefixes and negative quantities are excluded, never made positive or subtracted from demand. Then remove non-six-digit invoices, product codes outside five digits plus up to two letters (excluding postage, fees and adjustments), invalid dates, nonpositive/nonfinite/noninteger quantities and nonpositive/nonfinite prices. Rules run in that order; diagnostic return counts overlap, removal counts below do not.

{pd.DataFrame(list(q['sequential_removed'].items()), columns=['rule', 'rows_removed']).to_markdown(index=False)}

Missing raw values: {q['missing_values']}. Missing customer IDs do not remove sales; no customer IDs are exported. Missing descriptions are retained; a training-only modal normalized description supplies catalog labels, with product code fallback. Descriptions are uppercased and whitespace normalized. Price proxies use training-only median retail price. No outlier clipping or retrospective product removal is used.

Selection uses only data through {q['selection_cutoff']}, before the earliest development validation. Require 90 active days and 180 calendar days of history; rank by active days, units, then code. Keep 25. Each selected product is padded with zero recorded sales from its first training-observed sale through the common end date. Pre-listing days are excluded. A zero does not establish zero customer demand or stock availability. Closed days, missing records, and stockouts are indistinguishable here.

## Selected catalog (training-only metadata)

{catalog.to_markdown(index=False)}

Machine-readable evidence: `data-quality-summary.json`; source provenance and SHA-256: `../data/source-manifest.json`. Essential gates fail loudly for missing schema, insufficient history, fewer than 25 eligible products, invalid daily values, or duplicate keys.
"""
