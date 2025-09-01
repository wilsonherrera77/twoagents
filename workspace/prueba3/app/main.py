from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import csv
from io import TextIOWrapper
from typing import Dict, Any

app = FastAPI(title="csv-stats-api")

@app.get("/health")
def health():
    return {"status": "ok"}


def _try_float(s: str):
    try:
        return float(s)
    except Exception:
        return None


def compute_stats(rows):
    # rows: list of dict
    columns = {}
    # initialize columns with headers
    headers = set()
    for r in rows:
        headers.update(r.keys())
    for h in headers:
        columns[h] = {
            "count": 0,
            "nulls": 0,
            "numeric_count": 0,
            "sum": 0.0,
            "min": None,
            "max": None,
        }
    for r in rows:
        for h in headers:
            val = r.get(h)
            columns[h]["count"] += 1
            if val is None or val == "":
                columns[h]["nulls"] += 1
                continue
            fv = _try_float(val)
            if fv is not None:
                c = columns[h]
                c["numeric_count"] += 1
                c["sum"] += fv
                c["min"] = fv if c["min"] is None else min(c["min"], fv)
                c["max"] = fv if c["max"] is None else max(c["max"], fv)
    # finalize: compute mean and drop sum
    result: Dict[str, Any] = {}
    for h, c in columns.items():
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


@app.post("/stats")
async def stats(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing file")
    try:
        wrapper = TextIOWrapper(file.file, encoding="utf-8", errors="replace")
        reader = csv.DictReader(wrapper)
        rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid csv: {e}")
    finally:
        try:
            await file.close()
        except Exception:
            pass
    stats = compute_stats(rows)
    return JSONResponse({"columns": stats, "rows": len(rows)})