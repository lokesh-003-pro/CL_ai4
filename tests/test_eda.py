from datetime import datetime, timedelta
from types import SimpleNamespace as NS
import pytest
from app import create_app, db
from app.models import Attempt
from app.services import eda
from tests.test_app import signup

def A(score, mod="hr", cat="Intro", days=0):
    return NS(score=score, module=mod, category=cat, detail=None, created=datetime.utcnow() - timedelta(days=days))

def test_describe_and_missing():
    rows, bad = eda.valid([A(50), A(None), A(150), A(70)])
    assert bad == 2 and eda.describe([a.score for a in rows])["mean"] == 60 and eda.describe([]) is None
    assert eda.describe([80])["std"] is None

def test_percentage_points_vs_relative():
    c = eda.compare([A(60)], [A(75)])
    assert c["pp"] == 15 and c["rel"] == 25 and c["label"] == "Improved"
    assert eda.rel_change(0, 50) is None and eda.label(1.5) == "Unchanged" and eda.label(-3) == "Declined"
    assert eda.compare([], [A(1)])["ok"] is False

def test_insights_do_not_invent():
    d = eda.summary([A(50, "hr"), A(60, "hr"), A(90, "aptitude"), A(80, "aptitude")], {"hr": "HR", "aptitude": "Aptitude"})
    assert any("higher than" in t for t in d["tips"]) and d["stats"]["n"] == 4
    assert "not enough data" in eda.summary([A(50)], {})["tips"][0].lower()

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all(); yield app.test_client()

def test_user_isolation_and_pages(client):
    signup(client, "a@x.com")
    db.session.add(Attempt(user_id=1, module="hr", category="SecretTopic", score=70, total=1)); db.session.commit()
    assert b"SecretTopic" in client.get("/insights/export.csv").data
    assert client.get("/insights").status_code == 200 and client.get("/insights/compare").status_code == 200
    client.post("/logout"); signup(client, "b@x.com")
    assert b"SecretTopic" not in client.get("/insights/export.csv").data
