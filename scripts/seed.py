import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.seed import seed
with create_app().app_context():
    n = seed()
    print(f"Added {n} sample questions." if n else "Questions already present; nothing added.")
