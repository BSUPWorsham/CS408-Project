import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app


def test_home_page():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"Hello, World" in response.data


def test_health_endpoint():
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"