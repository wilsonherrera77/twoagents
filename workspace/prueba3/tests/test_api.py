from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_stats_basic():
    csv_text = 'a,b,c\n1,2,x\n3,,y\n,4,z\n'
    files = {'file': ('data.csv', csv_text, 'text/csv')}
    r = client.post('/stats', files=files)
    assert r.status_code == 200
    data = r.json()
    assert data['rows'] == 3
    cols = data['columns']
    assert 'a' in cols and 'b' in cols and 'c' in cols
    assert cols['a']['numeric_count'] == 2
    assert cols['b']['numeric_count'] == 2
    assert cols['c']['numeric_count'] == 0