# csv-stats-api

API en FastAPI que recibe un CSV, calcula estadísticas por columna y devuelve JSON.

## Endpoints
- GET /health -> {"status":"ok"}
- POST /stats (multipart/form-data con campo `file`) -> estadísticas por columna

## Ejecutar local
pip install -r requirements.txt
uvicorn app.main:app --reload

## Docker
docker build -t csv-stats-api .
docker run -p 8000:8000 csv-stats-api