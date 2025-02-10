import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_headers_on_health_endpoint():
    """Test CORS headers are present on health endpoint"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "POST" in response.headers["access-control-allow-methods"]

def test_cors_preflight():
    """Test OPTIONS request handling"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/time-entries", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_credentials():
    """Test that credentials setting matches development configuration"""
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "false"

def test_cors_exposed_headers():
    """Test that specific headers are exposed to the client"""
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
    exposed_headers = response.headers["access-control-expose-headers"].split(",")
    assert "X-Total-Count" in exposed_headers


def test_cors_on_time_entries_options():
    """Test CORS headers on time entries OPTIONS request"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/time-entries", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "GET" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "*"
    assert response.headers["access-control-allow-credentials"] == "false"
    assert "X-Total-Count" in response.headers["access-control-expose-headers"]
    assert "X-Correlation-ID" in response.headers["access-control-expose-headers"]


    assert "X-Correlation-ID" in exposed_headers

def test_cors_on_time_entries():
    """Test CORS headers on time entries endpoint"""
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/time-entries", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-credentials"] == "false"