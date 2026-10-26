from app import db
from app.models import User
from tests.conftest import STAFF_EMAIL, STAFF_PASSWORD


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Staff sign in" in resp.data


def test_staff_login_valid_credentials(client, login):
    resp = login()
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin")
    dash = client.get("/admin")
    assert dash.status_code == 200
    assert b"Test Staff" in dash.data


def test_login_is_case_insensitive_on_email(client, login):
    assert login(email=STAFF_EMAIL.upper()).status_code == 302


def test_login_wrong_password(client, login):
    resp = login(password="wrong")
    assert resp.status_code == 401
    assert b"Incorrect email or password." in resp.data
    assert client.get("/admin").status_code == 302  # still logged out


def test_login_unknown_email_gives_same_message(client, staff_user):
    resp = client.post("/login", data={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401
    assert b"Incorrect email or password." in resp.data


def test_password_is_stored_hashed(app, staff_user):
    user = db.session.get(User, staff_user.user_id)
    assert user.password_hash != STAFF_PASSWORD
    assert user.check_password(STAFF_PASSWORD)
    assert not user.check_password("nope")


def test_unauthorized_dashboard_access(client):
    resp = client.get("/admin")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_next_redirect_after_login(client, staff_user):
    resp = client.get("/admin")
    login_url = resp.headers["Location"]
    assert "next=" in login_url
    resp = client.post(login_url, data={"email": STAFF_EMAIL, "password": STAFF_PASSWORD})
    assert resp.headers["Location"].endswith("/admin")


def test_open_redirect_is_blocked(client, staff_user):
    resp = client.post("/login?next=https://evil.example/phish",
                       data={"email": STAFF_EMAIL, "password": STAFF_PASSWORD})
    assert resp.status_code == 302
    assert "evil.example" not in resp.headers["Location"]
    assert resp.headers["Location"].endswith("/admin")


def test_logout_ends_session(client, login):
    login()
    resp = client.post("/logout")
    assert resp.status_code == 302
    assert client.get("/admin").status_code == 302


def test_logout_requires_post(client, login):
    login()
    assert client.get("/logout").status_code == 405


def test_logged_in_user_skips_login_page(client, login):
    login()
    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin")
