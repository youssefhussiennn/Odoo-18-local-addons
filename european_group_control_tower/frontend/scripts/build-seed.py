"""Converts data/european-group-shipments.xlsx + data/acid.xlsx into src/data/seed.json.
Only raw conversion happens here; all business logic lives in src/lib/importer.js.
Usage: python3 scripts/build-seed.py
"""
import json, math, os
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ship = pd.read_excel(os.path.join(root, "data", "european-group-shipments.xlsx"))
acid = pd.read_excel(os.path.join(root, "data", "acid.xlsx"))

def clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()[:10]
    if isinstance(v, (int, float)) and float(v).is_integer():
        return int(v)
    return v if not isinstance(v, str) else v.strip()

rows = [{k: clean(v) for k, v in r.items()} for r in ship.to_dict("records")]
acid_rows = [{"Order Reference": clean(r["Order Reference"]), "ACID#": str(clean(r["ACID#"]))} for r in acid.to_dict("records")]
os.makedirs(os.path.join(root, "src", "data"), exist_ok=True)
with open(os.path.join(root, "src", "data", "seed.json"), "w", encoding="utf-8") as f:
    json.dump({"shipments": rows, "acid": acid_rows}, f, ensure_ascii=False, separators=(",", ":"))
print(len(rows), "shipment rows,", len(acid_rows), "ACID rows")
