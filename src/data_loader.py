"""Official UCI acquisition. No customer-level records are exported."""
from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from src.common import ROOT, sha256, utc_now, write_json

SOURCE = "https://archive.ics.uci.edu/dataset/352/online+retail"
DOWNLOAD = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
CITATION = "Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33."
EXPECTED_COLUMNS = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]


def download_data(raw_dir=ROOT / "data/raw"):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / "online-retail.zip"
    workbook = raw_dir / "Online Retail.xlsx"
    verified_on = utc_now()[:10]
    if not archive.exists():
        # Confirm the official page still states the permitted license before acquisition.
        with urllib.request.urlopen(SOURCE, timeout=30) as response:
            source_page = response.read().decode("utf-8")
        if "creativecommons.org/licenses/by/4.0" not in source_page:
            raise ValueError("Could not verify CC BY 4.0 on the official page; inspect its license before downloading")
        tmp = archive.with_suffix(".tmp")
        try:
            with urllib.request.urlopen(DOWNLOAD, timeout=120) as response, tmp.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            tmp.replace(archive)
        finally:
            tmp.unlink(missing_ok=True)
    with zipfile.ZipFile(archive) as z:
        members = [n for n in z.namelist() if Path(n).name == "Online Retail.xlsx"]
        if len(members) != 1:
            raise ValueError("Official archive must contain one Online Retail.xlsx")
        if not workbook.exists():
            workbook.write_bytes(z.read(members[0]))
    manifest_path = ROOT / "data/source-manifest.json"
    if manifest_path.exists():
        from src.common import read_json
        old = read_json(manifest_path)
        if old["archive_sha256"] != sha256(archive) or old["workbook_sha256"] != sha256(workbook):
            raise ValueError("Source checksum differs from recorded provenance; inspect before replacing evidence")
        return old
    manifest = {"dataset_id": 352, "source": SOURCE, "download_url": DOWNLOAD,
                "citation": CITATION, "license": "CC BY 4.0", "license_url": LICENSE,
                "downloaded_at_utc": utc_now(), "license_verified_on": verified_on,
                "archive_sha256": sha256(archive), "workbook_sha256": sha256(workbook),
                "synthetic": False, "modifications": "Positive-sales filtering, training-only product selection, daily aggregation; identifiers removed."}
    write_json(manifest_path, manifest)
    return manifest


def load_raw(path=ROOT / "data/raw/Online Retail.xlsx"):
    if not Path(path).exists():
        raise FileNotFoundError("Run python -m scripts.download_data first.")
    frame = pd.read_excel(path, engine="openpyxl", dtype={"InvoiceNo": "string", "StockCode": "string"})
    missing = set(EXPECTED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required source columns: {sorted(missing)}")
    return frame
