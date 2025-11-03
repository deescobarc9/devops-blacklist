import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    with patch('flask_jwt_extended.jwt_required', lambda *args, **kwargs: lambda f: f):
        from flask import Flask
        from flask_restful import Api
        from resources.blacklist_resource import BlacklistResource
        from resources.get_blacklist_resource import GetBlacklistResource
        
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        api = Api(test_app)
        
        api.add_resource(BlacklistResource, '/blacklist')
        api.add_resource(GetBlacklistResource, '/blacklist/<string:email>')
        
        @test_app.route('/blacklist/ping')
        def ping():
            return 'pong'
        
        @test_app.route('/')
        def root():
            return 'OK'
        
        yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    response = client.get('/blacklist/ping')
    assert response.status_code == 200
    assert response.data == b'pong'


def test_root(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.data == b'OK'


@patch('resources.blacklist_resource.Blacklist')
@patch('resources.blacklist_resource.db')
def test_add_blacklist_success(mock_db, mock_blacklist, client):
    mock_blacklist.query.filter_by.return_value.first.return_value = None
    
    response = client.post('/blacklist', json={
        'email': 'test@example.com',
        'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
        'blocked_reason': 'Test'
    })
    assert response.status_code == 201


@patch('resources.blacklist_resource.Blacklist')
def test_add_blacklist_invalid_email(mock_blacklist, client):
    response = client.post('/blacklist', json={
        'email': 'invalid-email',
        'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
    })
    assert response.status_code == 400


@patch('resources.blacklist_resource.Blacklist')
def test_add_blacklist_invalid_uuid(mock_blacklist, client):
    response = client.post('/blacklist', json={
        'email': 'test@example.com',
        'app_uuid': 'invalid-uuid'
    })
    assert response.status_code == 400


@patch('resources.blacklist_resource.Blacklist')
def test_add_blacklist_duplicate(mock_blacklist, client):
    mock_entry = Mock()
    mock_blacklist.query.filter_by.return_value.first.return_value = mock_entry
    
    response = client.post('/blacklist', json={
        'email': 'duplicate@example.com',
        'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
    })
    assert response.status_code == 409


def test_add_blacklist_missing_fields(client):
    response = client.post('/blacklist', json={'email': 'test@example.com'})
    assert response.status_code == 400


def test_add_blacklist_no_data(client):
    response = client.post('/blacklist', content_type='application/json')
    assert response.status_code in [400, 500]


@patch('resources.get_blacklist_resource.Blacklist')
def test_get_blacklist_exists(mock_blacklist, client):
    mock_entry = Mock()
    mock_entry.blocked_reason = 'Test reason'
    mock_blacklist.query.filter_by.return_value.first.return_value = mock_entry
    
    response = client.get('/blacklist/exists@example.com')
    assert response.status_code == 200
    data = response.get_json()
    assert data['existing'] == True
    assert data['blocked_reason'] == 'Test reason'


@patch('resources.get_blacklist_resource.Blacklist')
def test_get_blacklist_not_exists(mock_blacklist, client):
    mock_blacklist.query.filter_by.return_value.first.return_value = None
    
    response = client.get('/blacklist/notfound@example.com')
    assert response.status_code == 200
    data = response.get_json()
    assert data['existing'] == False


@patch('resources.blacklist_resource.Blacklist')
@patch('resources.blacklist_resource.db')
def test_add_blacklist_with_ip(mock_db, mock_blacklist, client):
    mock_blacklist.query.filter_by.return_value.first.return_value = None
    
    response = client.post('/blacklist', 
        json={
            'email': 'test2@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        },
        environ_base={'REMOTE_ADDR': '192.168.1.1'})
    assert response.status_code == 201


@patch('resources.blacklist_resource.Blacklist')
@patch('resources.blacklist_resource.db')
def test_add_blacklist_exception(mock_db, mock_blacklist, client):
    mock_blacklist.query.filter_by.side_effect = Exception('DB Error')
    
    response = client.post('/blacklist', json={
        'email': 'test@example.com',
        'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
    })
    assert response.status_code == 500


@patch('resources.get_blacklist_resource.Blacklist')
def test_get_blacklist_exception(mock_blacklist, client):
    mock_blacklist.query.filter_by.side_effect = Exception('DB Error')
    
    response = client.get('/blacklist/test@example.com')
    assert response.status_code == 500
