from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    if overrides:
        app.config.update(overrides)
    db.init_app(app)
    csrf.init_app(app)
    from . import models
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
        from .seed import seed
        seed()  # adds sample questions if the database is empty
    return app
