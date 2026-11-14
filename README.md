# InterviewIQ AI
Practice Smart. Speak Confidently. Get Interview Ready.

## Windows setup
```
cd interviewiq-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/seed.py
python run.py
```
Open http://127.0.0.1:5000, register, sign in. Run tests with `pytest`.

## Try each module
- Aptitude: pick a category, answer, submit (or let the timer end). See score, explanations, time.
- Group Discussion, HR, Technical: read the question, type or record an answer, submit, read the feedback.

## Demo mode
All open-ended feedback comes from `app/services/evaluator.py`: a rule-based checker (length, structure words, keywords, fillers, STAR parts). It is labelled as a demo score. No AI provider is connected.

## Add questions
Edit `SAMPLES` in `app/seed.py` (aptitude needs 4 options and `answer` = index 0-3), delete `instance/interviewiq.db`, run `python scripts/seed.py`.

## Voice
Speech recognition works in Chrome and Edge and asks for microphone permission. Other browsers use typing.

## Troubleshooting
- `python` not found: reinstall Python and tick "Add to PATH".
- `ModuleNotFoundError`: activate `.venv` and run `pip install -r requirements.txt`.
- Mic error: allow the microphone in the browser address bar, or type.

## Not built yet
Resume/JD analysis, PDF reports, AI-provider evaluation, text-to-speech, profile/settings pages, coding editor, deployment guide.

## Resume, AI and analysis (added)
- Resume page: upload a text-based PDF (max 2 MB), optionally paste a job description. Only the extracted text is stored; the PDF itself is not saved. "Delete my resume data" removes it.
- AI: put `AI_API_KEY` in `.env` (server side only) to get AI questions and AI answer feedback. Without it, everything uses labelled demo rules. If the provider fails, the app falls back silently to demo.
- Speech: measured duration, words per minute and filler words. Pauses, pronunciation and emotion are not measured.
- Camera (optional): lighting and face-in-frame only, processed in your browser. Face detection works only where the browser has FaceDetector (some Chrome setups).

## HR round: new questions and camera cues
- With `AI_API_KEY` set, every HR, GD and technical question is generated fresh, avoids the last 8 questions, and the HR question can follow up on your previous answer. Without a key it picks a different sample question each time.
- The HR page opens the camera panel by default (you still must press Turn on camera). It reports lighting, face in frame and centring only. Emotion or "reaction" reading is deliberately not built: it is unreliable and unfair, and the project rules forbid judging people from their face.

## Deploy on Render (from GitHub)
1. Push the project to a GitHub repository (never commit `.env`; `.gitignore` already excludes it).
2. On render.com choose New > Web Service (or New > Blueprint) and select the repository.
3. Build command: `pip install -r requirements.txt`. Start command: `gunicorn run:app`.
4. Add environment variables `SECRET_KEY` (long random text) and optionally `AI_API_KEY`.
5. Render gives you a permanent `https://....onrender.com` link.
Note: on Render's free plan the SQLite file is wiped on every restart or redeploy, so accounts and history reset. Sample questions are re-added automatically. Use a paid persistent disk or a hosted database to keep data.

## EDA & Insights
Open **Insights** in the top bar. Filters: date range and module. Shows n, mean, median, min, max, range and standard deviation, charts (score histogram, module bars, trend line, stacked aptitude correct/incorrect/unanswered) each with a table, rule-based insights, topic table, CSV export, and a **Compare** page (baseline vs later period).
- Percentage-point change = later minus baseline (60 to 75 = +15 points). Relative change = difference / baseline (+25%); shown as "Not defined" if the baseline is 0. Under 2 points counts as Unchanged. No significance test is run.
- Missing or out-of-range scores are excluded, never counted as zero. Outliers are not removed.
- Only your own records are used. Run `pytest` to test the calculations and user isolation.
- Not built yet: box plot, heatmap, scatter plot, domain/difficulty filters, CSV dataset explorer, PDF analysis report, Playwright tests.

## IQ Coach chatbot
Floating chat button on every signed-in page plus a full page at **AI Coach**. With `AI_API_KEY` set, answers come from the AI and are labelled "AI-generated". Without a key (or if the provider fails) a rule-based demo coach answers a fixed set of topics, labelled "Demo coach (rule-based)". Messages are stored per user (Clear chat deletes them), limited to 1000 characters and 15 per minute. The coach cannot run actions: it only suggests links. Resume text is not sent to the AI.
## Browser tests
`pip install -r requirements-dev.txt`, `playwright install chromium`, then `pytest tests/e2e -v`. Checks login redirect, sign-up/sign-in, chat, horizontal overflow at 5 screen sizes and console errors, and saves screenshots to `tests/e2e/screenshots`. Screenshot comparison against baselines is not implemented yet.
