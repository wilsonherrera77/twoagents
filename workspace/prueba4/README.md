# etl-csv-api (prueba4)

API en FastAPI con:
- Autenticación JWT (registro/login)
- SQLite (SQLAlchemy)
- Carga de CSV y procesamiento en background (estadísticas por columna)
- Endpoints: /health, /auth/register, /auth/login, /datasets/upload, /datasets/{id}/status, /datasets/{id}/result

## Local
pip install -r requirements.txt
uvicorn app.main:app --reload

## Docker
docker build -t etl-csv-api .
docker run -p 8000:8000 etl-csv-api