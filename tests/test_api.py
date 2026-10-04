import pytest
from app import app, db
import json

import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    # Use memory database for testing
    if os.path.exists("data/test_api_db.sqlite"):
        os.remove("data/test_api_db.sqlite")
    db.db_path = 'data/test_api_db.sqlite'
    db.init_db()
    with app.test_client() as client:
        yield client
    if os.path.exists("data/test_api_db.sqlite"):
        os.remove("data/test_api_db.sqlite")

def test_health(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert json.loads(rv.data)['status'] == 'healthy'

def test_register_success(client):
    rv = client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    assert rv.status_code == 201
    assert "user_id" in json.loads(rv.data)

def test_register_duplicate(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    rv = client.post('/api/register', json={
        "name": "Student2",
        "email": "student@test.com",
        "password": "password123"
    })
    assert rv.status_code == 409

def test_register_validation(client):
    # Test invalid email
    rv = client.post('/api/register', json={
        "name": "Student",
        "email": "studenttest.com",
        "password": "password123"
    })
    assert rv.status_code == 400
    
    # Test short password
    rv = client.post('/api/register', json={
        "name": "Student",
        "email": "student2@test.com",
        "password": "123"
    })
    assert rv.status_code == 400

def test_login_success(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    rv = client.post('/api/login', json={
        "email": "student@test.com",
        "password": "password123"
    })
    assert rv.status_code == 200
    assert "access_token" in json.loads(rv.data)

def test_login_failure(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    rv = client.post('/api/login', json={
        "email": "student@test.com",
        "password": "wrongpassword"
    })
    assert rv.status_code == 401

def test_query_ai(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    login_rv = client.post('/api/login', json={
        "email": "student@test.com",
        "password": "password123"
    })
    token = json.loads(login_rv.data)['access_token']
    
    rv = client.post('/api/query', 
        json={"question": "What is my GPA?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert rv.status_code == 200
    assert "answer" in json.loads(rv.data)

def test_get_history(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123"
    })
    login_rv = client.post('/api/login', json={
        "email": "student@test.com",
        "password": "password123"
    })
    token = json.loads(login_rv.data)['access_token']
    
    client.post('/api/query', 
        json={"question": "What is my GPA?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    rv = client.get('/api/history', headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
    assert len(json.loads(rv.data)) == 1

def test_admin_route_forbidden(client):
    client.post('/api/register', json={
        "name": "Student",
        "email": "student@test.com",
        "password": "password123",
        "role": "student"
    })
    login_rv = client.post('/api/login', json={
        "email": "student@test.com",
        "password": "password123"
    })
    token = json.loads(login_rv.data)['access_token']
    
    rv = client.get('/api/admin/suspicious', headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403

def test_admin_route_success(client):
    client.post('/api/register', json={
        "name": "Admin",
        "email": "admin@test.com",
        "password": "password123",
        "role": "admin"
    })
    login_rv = client.post('/api/login', json={
        "email": "admin@test.com",
        "password": "password123"
    })
    token = json.loads(login_rv.data)['access_token']
    
    rv = client.get('/api/admin/suspicious', headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 200
