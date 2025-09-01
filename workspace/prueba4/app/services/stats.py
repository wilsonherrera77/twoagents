import csv
from io import TextIOWrapper
from typing import Dict, Any, Iterable


def try_float(s: str):
    try:
        return float(s)
    except Exception:
        return None


def compute_stats_iter(rows: Iterable[dict]) -> Dict[str, Any]:
    cols = {}
    headers_known = False
    headers = []
    for r in rows:
        if not headers_known:
            headers = list(r.keys())
            for h in headers:
                cols[h] = {"count": 0, "nulls": 0, "numeric_count": 0, "sum": 0.0, "min": None, "max": None}
            headers_known = True
        for h in headers:
            val = r.get(h)
            c = cols[h]
            c["count"] += 1
            if val is None or val == "":
                c["nulls"] += 1
                continue
            fv = try_float(val)
            if fv is not None:
                c["numeric_count"] += 1
                c["sum"] += fv
                c["min"] = fv if c["min"] is None else min(c["min"], fv)
                c["max"] = fv if c["max"] is None else max(c["max"], fv)
    result = {}
    for h, c in cols.items():
        mean = (c["sum"] / c["numeric_count"]) if c["numeric_count"] > 0 else None
        result[h] = {
            "count": c["count"],
            "nulls": c["nulls"],
            "numeric_count": c["numeric_count"],
            "min": c["min"],
            "max": c["max"],
            "mean": mean,
        }
    return result


def read_csv_dicts(file_obj) -> Iterable[dict]:
    wrapper = TextIOWrapper(file_obj, encoding="utf-8", errors="replace")
    reader = csv.DictReader(wrapper)
    for row in reader:
        yield row