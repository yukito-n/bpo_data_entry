
from fastapi.testclient import TestClient
from app.main import app


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
