import pytest
from app import create_app, db
from app.models import Attempt
from app.seed import seed
from app.services import video
from tests.test_app import signup

@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all(); seed(); yield app.test_client()

TEXT = "Um I am agree that my self is a student. Basically I like teamwork and I worked on a project."
def payload(**k):
    d = {"question": "Tell me about yourself.", "answer": TEXT, "dur": 60, "segments": [{"text": "I like teamwork", "conf": 0.4}],
         "pauses": [2500, 3000, 4500], "first_ms": 8000, "vis": {"frames": 10, "lit": 3, "face": 5, "centre": 2, "face_ok": True}}
    d.update(k); return d

def test_feedback_reports_measured_problems():
    r = video.build("Tell me about yourself.", TEXT, "", 60, [{"text": "I like teamwork", "conf": 0.4}], [2500, 3000, 4500], 8000, {"frames": 10, "lit": 30, "face": 50, "centred": 20})
    text = " ".join(i["wrong"] for i in r["issues"])
    assert "paused 3" in text and "8.0 seconds" in text and "Lighting" in text and "not recognise" in text and "grammar" in text
    assert r["speech"]["pauses"] == 3 and r["speech"]["longest"] == 4.5

def test_route_saves_and_validates(client):
    signup(client)
    j = client.post("/video/answer", json=payload()).get_json()
    assert j["issues"] and Attempt.query.one().module == "video"
    assert client.get(j["url"]).status_code == 200
    assert client.post("/video/answer", json={"question": "x", "answer": "hi"}).status_code == 400
    assert len(client.get("/video/questions").get_json()["questions"]) == 3
