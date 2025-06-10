
from fastapi.testclient import TestClient
from app.main import app


def test_ui_served():
    with TestClient(app) as client:
        resp = client.get('/ui')
        assert resp.status_code == 200
        assert 'text/html' in resp.headers['content-type']


def test_user_workflow():
    with TestClient(app) as client:
        # Login
        response = client.post('/token', data={'username': 'admin', 'password': 'admin123'})
        assert response.status_code == 200
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Create user
        response = client.post('/users', json={'username': 'operator1', 'password': 'pass', 'role': 'Operator'}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == 'operator1'

        user_id = data['id']

        # Update user
        response = client.patch(f'/users/{user_id}', json={'role': 'Manager'}, headers=headers)
        assert response.status_code == 200
        assert response.json()['role'] == 'Manager'

        # Deactivate user
        response = client.post(f'/users/{user_id}/deactivate', headers=headers)
        assert response.status_code == 200
        assert response.json()['is_active'] is False

        # Create project and batch
        response = client.post('/projects', json={'name': 'Proj1', 'client_name': 'ClientA'}, headers=headers)
        proj_id = response.json()['id']
        response = client.post('/batches', json={
            'project_id': proj_id,
            'reception_date': '2024-01-01T00:00:00Z',
            'due_date': '2024-01-02T00:00:00Z',
            'initial_volume': 10
        }, headers=headers)
        assert response.status_code == 200
        batch_id = response.json()['id']

        # Update status
        response = client.put(f'/batches/{batch_id}/status', json={'status': 'Triage in Progress'}, headers=headers)
        assert response.status_code == 200
        assert response.json()['status'] == 'Triage in Progress'


def test_phase2_features():
    with TestClient(app) as client:
        # Admin login
        resp = client.post('/token', data={'username': 'admin', 'password': 'admin123'})
        token = resp.json()['access_token']
        admin_headers = {'Authorization': f'Bearer {token}'}

        # Create operator
        resp = client.post('/users', json={'username': 'op2', 'password': 'pass2', 'role': 'Operator'}, headers=admin_headers)
        op_id = resp.json()['id']

        # Create project and batch
        resp = client.post('/projects', json={'name': 'Proj2', 'client_name': 'ClientB'}, headers=admin_headers)
        proj_id = resp.json()['id']
        resp = client.post('/batches', json={
            'project_id': proj_id,
            'reception_date': '2024-01-03T00:00:00Z',
            'due_date': '2024-01-04T00:00:00Z',
            'initial_volume': 5
        }, headers=admin_headers)
        batch_id = resp.json()['id']

        # Assign operator
        resp = client.post('/assignments', json={'user_id': op_id, 'batch_id': batch_id}, headers=admin_headers)
        assert resp.status_code == 200

        # Create shift
        resp = client.post('/shifts', json={'user_id': op_id, 'start_time': '2024-01-03T09:00:00Z', 'end_time': '2024-01-03T17:00:00Z'}, headers=admin_headers)
        assert resp.status_code == 200

        # Operator login and get shifts
        resp = client.post('/token', data={'username': 'op2', 'password': 'pass2'})
        op_token = resp.json()['access_token']
        op_headers = {'Authorization': f'Bearer {op_token}'}
        resp = client.get('/shifts', headers=op_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Performance log
        resp = client.post('/performance/start', json={'batch_id': batch_id}, headers=op_headers)
        log_id = resp.json()['log_id']
        resp = client.post('/performance/stop', json={'batch_id': batch_id, 'items_processed': 5, 'log_id': log_id}, headers=op_headers)
        assert resp.status_code == 200

        # Log quality
        resp = client.post('/quality', json={'batch_id': batch_id, 'operator_id': op_id, 'errors': 1}, headers=admin_headers)
        assert resp.status_code == 200

        # Dashboard
        resp = client.get('/dashboard', headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert 'leaderboard' in data
