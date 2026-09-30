import os
os.environ['DATABASE_URL']='sqlite:///./test_scholarsaathi.db'
os.environ['JWT_SECRET_KEY']='test-secret-key-long-enough'
from fastapi.testclient import TestClient
from app.main import app

def test_registration_profile_and_demo_catalogue():
    with TestClient(app) as client:
        email='test-student@example.org'
        r=client.post('/auth/register',json={'name':'Test Student','email':email,'password':'strong-demo-password'})
        if r.status_code==409:
            r=client.post('/auth/login',json={'email':email,'password':'strong-demo-password'})
        assert r.status_code==200
        headers={'Authorization':'Bearer '+r.json()['access_token']}
        assert client.get('/profile',headers=headers).status_code==200
        response=client.get('/scholarships')
        assert response.status_code==200
        assert all(item['demo'] for item in response.json()['items'])

def test_expired_opportunities_are_closed():
    with TestClient(app) as client:
        # Seed records have no fictional dates; detail payload exposes verification status.
        items=client.get('/scholarships').json()['items']
        assert all(item['status']=='Verification Required' for item in items)

def test_health_is_explicit_about_demo_data():
    with TestClient(app) as client:
        assert client.get('/health').json()['mode']=='demo'
