import pytest

PAGES = ["/", "/about", "/practice-areas", "/resources", "/contact", "/how-social-security-works"]


@pytest.mark.parametrize("path", PAGES)
def test_public_pages_load(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert b"Aplin Law" in resp.data


def test_nav_and_footer_on_every_page(client):
    html = client.get("/about").data
    assert b'aria-label="Main navigation"' in html
    assert b"site-footer" in html


def test_contact_saves_submission(client, app):
    resp = client.post("/contact", data={"sender_name": "Pat", "sender_email": "pat@example.com", "message": "Hello"})
    assert resp.status_code == 302
    from app.models import ContactSubmission
    with app.app_context():
        assert ContactSubmission.query.count() == 1


def test_contact_validation(client):
    resp = client.post("/contact", data={"sender_name": "", "sender_email": "bad", "message": ""})
    assert resp.status_code == 200
    assert b"Enter your name." in resp.data


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
