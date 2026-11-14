from datetime import datetime
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(20), nullable=False)   # aptitude, hr, gd, tech
    category = db.Column(db.String(40), nullable=False)
    difficulty = db.Column(db.String(10), default="easy")
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)
    answer = db.Column(db.Integer)
    explanation = db.Column(db.Text)
    keywords = db.Column(db.String(300))
    domain = db.Column(db.String(60), default="General Graduate Placement")

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    module = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(40))
    score = db.Column(db.Float, nullable=False)
    total = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    detail = db.Column(db.JSON)
    domain = db.Column(db.String(60))

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(120))
    text = db.Column(db.Text)
    jd = db.Column(db.Text)
    result = db.Column(db.JSON)
    created = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # user or assistant
    content = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(40))
    created = db.Column(db.DateTime, default=datetime.utcnow)
