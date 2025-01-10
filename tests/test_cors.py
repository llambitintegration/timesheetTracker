import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_headers_on_main_endpoint():
    """Test CORS headers are present on main endpoint"""
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-methods"] == "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    assert "access-control-expose-headers" in response.headers

def test_cors_preflight():
    """Test OPTIONS request handling"""
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/time-entries/by-date/2025-01-09", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-headers"] == "*"
    assert response.headers["access-control-max-age"] == "3600"

def test_cors_time_entries_endpoint():
    """Test CORS headers on time entries endpoint"""
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.get("/time-entries/by-date/2025-01-09", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-methods"] == "GET, POST, PUT, DELETE, OPTIONS, PATCH"

def test_cors_allow_credentials():
    """Test that credentials are not allowed (development mode)"""
    headers = {
        "Origin": "https://example.com",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-credentials" not in response.headers  # Should not be present since allow_credentials=False

def test_cors_header_exposure():
    """Test that necessary headers are exposed through CORS"""
    headers = {
        "Origin": "https://example.com",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-expose-headers"] == "*"

def test_cors_multiple_methods():
    """Test CORS allows multiple HTTP methods"""
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "PUT",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/time-entries/", headers=headers)
    assert response.status_code == 200
    allowed_methods = response.headers["access-control-allow-methods"]
    assert all(method in allowed_methods for method in ["GET", "POST", "PUT", "DELETE", "PATCH"])