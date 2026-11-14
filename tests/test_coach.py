import pytest
from app import create_app, db
from app.models import ChatMessage
from app.services import ai
from tests.test_app import signup

@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all(); yield app.test_client()

def send(c, msg): return c.post("/coach/message", json={"message": msg})

def test_demo_reply_without_key(client):
    signup(client)
    j = send(client, "Prepare me for a Python interview").get_json()
    assert j["label"].startswith("Demo coach") and "Python" in j["reply"]
    assert client.get("/coach/history").get_json()["messages"][1]["role"] == "assistant"

@pytest.mark.parametrize("payload", [{}, {"message": ""}, {"message": 5}, {"message": "x" * 1001}])
def test_invalid_payloads(client, payload):
    signup(client)
    assert client.post("/coach/message", json=payload).status_code == 400

def test_requires_login(client):
    assert client.post("/coach/message", json={"message": "hi"}).status_code == 302

def test_provider_error_falls_back(client, monkeypatch):
    signup(client)
    monkeypatch.setenv("AI_API_KEY", "dummy")
    monkeypatch.setattr(ai, "chat", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("quota")))
    j = send(client, "Create a 7-day study plan").get_json()
    assert "not responding" in j["reply"] and j["label"].startswith("Demo coach")

def test_ai_label_when_provider_works(client, monkeypatch):
    signup(client)
    monkeypatch.setenv("AI_API_KEY", "dummy")
    monkeypatch.setattr(ai, "chat", lambda *a, **k: "stub answer")
    assert send(client, "hello").get_json()["label"] == "AI-generated"

def test_user_isolation_and_clear(client):
    signup(client, "a@x.com"); send(client, "my secret question")
    client.post("/logout"); signup(client, "b@x.com")
    assert client.get("/coach/history").get_json()["messages"] == []
    send(client, "b message"); client.post("/coach/clear")
    assert ChatMessage.query.filter_by(user_id=2).count() == 0 and ChatMessage.query.filter_by(user_id=1).count() == 2
