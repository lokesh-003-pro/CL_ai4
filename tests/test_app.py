import pytest
from app import create_app, db
from app.models import Question, Attempt
from app.seed import seed

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    with app.app_context():
        db.create_all(); seed()
        yield app.test_client()

def signup(c, email="a@x.com"):
    c.post("/register", data={"name": "A", "email": email, "password": "password1"})
    return c.post("/login", data={"email": email, "password": "password1"})

def test_register_login_and_protection(client):
    assert client.get("/dashboard").status_code == 302
    assert signup(client).status_code == 302
    assert client.get("/dashboard").status_code == 200

def test_aptitude_scoring_and_persistence(client):
    signup(client)
    client.get("/aptitude/quiz")
    with client.session_transaction() as s: ids = s["quiz"]
    data = {f"q{i}": str(db.session.get(Question, i).answer) for i in ids}
    r = client.post("/aptitude/submit", data=data)
    assert r.status_code == 302
    a = Attempt.query.one()
    assert a.score == 100 and a.detail["correct"] == len(ids)

def test_hr_demo_eval_saved(client):
    signup(client)
    client.get("/practice/hr")
    r = client.post("/practice/hr", data={"answer": "First I studied skills because experience matters. For example I led a team and the result improved."})
    assert r.status_code == 302 and Attempt.query.one().module == "hr"

def test_users_cannot_see_others_results(client):
    signup(client)
    client.get("/practice/gd")
    client.post("/practice/gd", data={"answer": "AI will change jobs and skills for many people today."})
    client.post("/logout"); signup(client, "b@x.com")
    assert client.get("/result/1").status_code == 404

def test_new_pages_and_english_check(client):
    signup(client)
    for url in ("/dashboard", "/progress", "/visual", "/english", "/resume", "/history"):
        assert client.get(url).status_code == 200
    r = client.post("/english", data={"scenario": "Introduction", "answer": "i am agree with this plan and my self is a student."})
    assert r.status_code == 302
    a = Attempt.query.filter_by(module="english").one()
    assert a.detail["corrections"] and "I agree" in a.detail["improved"]
