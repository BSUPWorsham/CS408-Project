import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("path, text", [
    ("/", b"Start your free case review"),
    ("/about", b"How we work"),
    ("/practice-areas", b"The stages of a claim"),
    ("/how-social-security-works", b"Work credits"),
    ("/resources", b"Social Security Administration"),
    ("/contact", b"Send message"),
    ("/intake", b"Free Case Review"),
    ("/login", b"Staff Sign In"),
])
def test_public_pages_render(client, path, text):
    response = client.get(path)
    assert response.status_code == 200
    assert text in response.data


def test_navigation_on_every_page(client):
    html = client.get("/resources").data
    for href in (b'href="/about"', b'href="/practice-areas"',
                 b'href="/how-social-security-works"', b'href="/contact"'):
        assert href in html
    assert b'aria-current="page"' in html


def test_all_five_claim_stages_listed(client):
    html = client.get("/practice-areas").data
    for stage in (b"Initial application", b"Reconsideration", b"Hearing before a judge",
                  b"Appeals Council", b"Federal court"):
        assert stage in html


def test_contact_valid_submission_redirects_with_message(client):
    response = client.post("/contact", data={
        "name": "Pat Doe", "email": "pat@example.com",
        "message": "I was denied last month and have questions.",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Your message was received" in response.data


def test_contact_missing_fields_shows_errors(client):
    response = client.post("/contact", data={"name": "", "email": "bad", "message": "hi"})
    assert response.status_code == 400
    assert b"Please enter your name." in response.data
    assert b"Please enter a valid email address." in response.data


def test_unknown_page_returns_404(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert b"find that page" in response.data


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
