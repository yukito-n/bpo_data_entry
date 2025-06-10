import os
import importlib
from fastapi.testclient import TestClient


def test_test_pages_served():
    os.environ['APP_ENV'] = 'test'
    import app.main as main
    importlib.reload(main)
    with TestClient(main.app) as client:
        resp = client.get('/test/index.html')
        assert resp.status_code == 200
        assert 'Test Environment' in resp.text
    os.environ.pop('APP_ENV')
