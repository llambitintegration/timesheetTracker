import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_headers_on_main_endpoint():
    """Test CORS headers are present on main endpoint"""
    headers = {
        "Origin": "http://example.com",  # Changed to HTTP for development testing
        "Access-Control-Request-Method": "GET",
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_preflight():
    """Test OPTIONS request handling"""
    headers = {
        "Origin": "http://example.com",  # HTTP origin for development
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-headers"] == "*"

def test_cors_allows_http():
    """Test that HTTP origins are allowed during development"""
    headers = {
        "Origin": "http://localhost:3000",  # Common development origin
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"

def test_cors_allows_all_methods():
    """Test that all HTTP methods are allowed"""
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    headers = {"Origin": "http://example.com"}

    for method in methods:
        if method == "OPTIONS":
            response = client.options("/", headers=headers)
        else:
            response = client.request(method, "/", headers=headers)
        assert response.status_code in [200, 405]  # 405 is acceptable for unsupported methods
        assert response.headers["access-control-allow-origin"] == "*"
        assert method in response.headers["access-control-allow-methods"]

def test_cors_allows_all_headers():
    """Test that all headers are allowed"""
    custom_headers = [
        "X-Custom-Header",
        "Authorization",
        "Content-Type",
        "Accept",
    ]

    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": ",".join(custom_headers),
    }

    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-headers"] == "*"

# New test cases for better coverage

def test_cors_expose_headers():
    """Test that specific headers are exposed to the client"""
    headers = {"Origin": "http://example.com"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    exposed_headers = response.headers["access-control-expose-headers"].split(",")
    assert "X-Total-Count" in exposed_headers
    assert "X-Correlation-ID" in exposed_headers

def test_cors_max_age():
    """Test the max-age header in preflight response"""
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-max-age"] == "3600"

def test_cors_credentials():
    """Test that credentials are allowed"""
    headers = {"Origin": "http://example.com"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"

def test_cors_complex_preflight():
    """Test complex preflight request with multiple headers and methods"""
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-custom-header,authorization",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-allow-headers"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-max-age"] == "3600"
    assert response.headers["access-control-allow-credentials"] == "true"

def test_cors_on_error_response():
    """Test CORS headers are present even on error responses"""
    headers = {"Origin": "http://example.com"}
    response = client.get("/nonexistent-path", headers=headers)
    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "*"
    assert "GET" in response.headers["access-control-allow-methods"]