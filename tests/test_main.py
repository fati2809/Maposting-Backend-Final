
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch("app.config.get_supabase_client") as mock:
    mock.return_value = MagicMock()
    from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json()["ok"] == True

def test_login_missing_fields():
    response = client.post("/login", json={})
    assert response.status_code == 422

def test_login_wrong_credentials():
    with patch("app.services.auth_service.AuthService.sign_in") as mock_signin:
        from fastapi import HTTPException
        mock_signin.side_effect = HTTPException(status_code=401, detail="Credenciales incorrectas")
        response = client.post("/login", json={
            "email_user": "noexiste@test.com",
            "pass_user": "wrongpass"
        })
        assert response.status_code == 401

def test_register_missing_fields():
    response = client.post("/register", json={})
    assert response.status_code == 422

def test_logout_post():
    with patch("app.services.auth_service.AuthService.sign_out") as mock_out:
        mock_out.return_value = {"success": True}
        response = client.post("/logout")
        assert response.status_code == 200

def test_options_catchall():
    response = client.options("/cualquier-ruta")
    assert response.status_code == 204

def test_check_auth_no_header():
    response = client.get("/check-auth")
    assert response.status_code == 401
