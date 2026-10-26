import pytest
from app import create_app, db
from app.models import User

STAFF_EMAIL = "staff@aplinlaw.com"
STAFF_PASSWORD = "correct-horse-battery"


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def staff_user(app):
    user = User(email=STAFF_EMAIL, full_name="Test Staff")
    user.set_password(STAFF_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def login(client, staff_user):
    def _login(email=STAFF_EMAIL, password=STAFF_PASSWORD, **kwargs):
        return client.post("/login", data={"email": email, "password": password}, **kwargs)
    return _login
