import pytest
from app import create_app, db
from app.seed import seed
from tests.test_app import signup

@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all(); seed(); yield app.test_client()

def test_domain_changes_technical_question(client):
    signup(client)
    client.post("/domain", data={"domain": "Python Developer", "next": "/practice/tech?new=1"})
    page = client.get("/practice/tech?new=1").get_data(as_text=True)
    assert "list and a tuple" in page or "decorators" in page
    client.post("/domain", data={"domain": "Cybersecurity", "next": "/practice/tech?new=1"})
    assert "phishing" in client.get("/practice/tech?new=1").get_data(as_text=True) or "authorization" in client.get("/practice/tech?new=1").get_data(as_text=True)

def test_custom_role_and_safe_redirect(client):
    signup(client)
    r = client.post("/domain", data={"domain": "x", "custom": "Embedded <b>Engineer</b>", "next": "//evil.com"})
    assert r.headers["Location"].endswith("/dashboard")
    assert "Embedded bEngineerb" in client.get("/practice/tech").get_data(as_text=True)
