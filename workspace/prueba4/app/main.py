from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import json

from .db import Base, engine, SessionLocal
from .models import Dataset
from .auth import router as auth_router, get_current_user
from .services.stats import read_csv_dicts, compute_stats_iter

app = FastAPI(title="etl-csv-api (prueba4)")
app.include_router(auth_router)

# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/health')
def health():
    return {"status": "ok"}


@app.post('/datasets/upload')
async def upload_dataset(background: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail='missing file')
    ds = Dataset(filename=file.filename, status='processing')
    db.add(ds)
    db.commit()
    db.refresh(ds)

    # Schedule background computation
    async def _process(ds_id: int, upfile: UploadFile):
        s = SessionLocal()
        try:
            rows = read_csv_dicts(upfile.file)
            stats = compute_stats_iter(rows)
            result = {"columns": stats}
            # store
            obj = s.get(Dataset, ds_id)
            if obj:
                obj.status = 'done'
                obj.result_json = json.dumps(result)
                s.commit()
        except Exception as e:
            obj = s.get(Dataset, ds_id)
            if obj:
                obj.status = f'error: {e}'
                s.commit()
        finally:
            try:
                await upfile.close()
            except Exception:
                pass
            s.close()

    background.add_task(_process, ds.id, file)
    return {"dataset_id": ds.id, "status": ds.status}


@app.get('/datasets/{ds_id}/status')
def dataset_status(ds_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ds = db.get(Dataset, ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail='not found')
    return {"id": ds.id, "status": ds.status}


@app.get('/datasets/{ds_id}/result')
def dataset_result(ds_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ds = db.get(Dataset, ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail='not found')
    if not ds.result_json:
        raise HTTPException(status_code=400, detail='not ready')
    return JSONResponse(json.loads(ds.result_json))