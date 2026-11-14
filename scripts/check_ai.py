"""Run: python scripts/check_ai.py   Tells you whether your AI key is loaded and working."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # loads .env
from app.services import ai
if not ai.configured():
    print("No AI_API_KEY found in .env. The app will run in demo mode.")
else:
    q, label = ai.new_question("hr", [], "", "Python Developer")
    print("AI works. Sample question:", q) if q else print("Key found, but the AI call failed (wrong key, no credit, or no internet).")
