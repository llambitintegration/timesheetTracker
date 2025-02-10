import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_headers_on_main_endpoint():
    """Test CORS headers are present on main endpoint"""
    headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Access-Control-Request-Method": "GET",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_preflight():
    """Test OPTIONS request handling"""
    headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_credentials():
    """Test that credentials setting matches API client configuration"""
    headers = {"Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "false"

def test_cors_complex_preflight():
    """Test complex preflight request with multiple headers and methods"""
    headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-custom-header,authorization",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert response.headers["access-control-allow-headers"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-max-age"] == "3600"
    assert response.headers["access-control-allow-credentials"] == "false"

def test_api_client_cors_configuration():
    """Test specific API client CORS configuration"""
    headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Test GET request
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert response.headers["access-control-allow-credentials"] == "false"

    # Test preflight for specific API client headers
    preflight_headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type,accept",
    }
    response = client.options("/", headers=preflight_headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert response.headers["access-control-allow-credentials"] == "false"
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_expose_headers():
    """Test that specific headers are exposed to the client"""
    headers = {"Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    exposed_headers = response.headers["access-control-expose-headers"].split(",")
    assert "X-Total-Count" in exposed_headers
    assert "X-Correlation-ID" in exposed_headers

def test_cors_max_age():
    """Test the max-age header in preflight response"""
    headers = {
        "Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-max-age"] == "3600"

def test_cors_on_error_response():
    """Test CORS headers are present even on error responses"""
    headers = {"Origin": "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"}
    response = client.get("/nonexistent-path", headers=headers)
    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"
    assert "GET" in response.headers["access-control-allow-methods"]