import os
import re
import time
import csv
import io
from datetime import datetime, timedelta
import random
from functools import wraps
from flask import Response, Blueprint, render_template, request, redirect, url_for, session, flash, abort, g
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Question, Attempt, Resume, ChatMessage
from .services.evaluator import evaluate
from .services import ai, resume as rs, english as en, eda, coach as iq, video as vd

bp = Blueprint("main", __name__)
DOMAINS = ["Software Developer", "Python Developer", "Java Developer", "Frontend Developer", "Backend Developer", "Data Analyst", "Data Scientist / ML Engineer", "QA / Testing Engineer", "Cloud / DevOps", "Cybersecurity", "SQL / Database Developer", "General Graduate Placement"]
MODULES = {"aptitude": "Aptitude", "gd": "Group Discussion", "hr": "HR Interview", "tech": "Technical Interview", "english": "English Coach", "video": "Video Interview"}

def login_required(f):
    @wraps(f)
    def wrap(*a, **k):
        g.user = db.session.get(User, session["uid"]) if session.get("uid") else None
        if g.user is None:
            session.clear()
            flash("Please sign in first.", "error")
            return redirect(url_for("main.login"))
        return f(*a, **k)
    return wrap

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email, pw = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if not name or "@" not in email or len(pw) < 8:
            flash("Enter a name, a valid email and a password of at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered. Sign in instead.", "error")
        else:
            db.session.add(User(name=name[:80], email=email, pw=generate_password_hash(pw)))
            db.session.commit()
            flash("Account created. Sign in to start practising.", "ok")
            return redirect(url_for("main.login"))
    return render_template("auth.html", mode="register")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if u and check_password_hash(u.pw, request.form.get("password", "")):
            session.clear()
            session["uid"] = u.id
            return redirect(url_for("main.dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")

@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("main.index"))

def stats(uid):
    rows = Attempt.query.filter_by(user_id=uid).order_by(Attempt.created.desc()).all()
    now = datetime.utcnow(); days = {a.created.date() for a in rows}
    d = now.date() if now.date() in days else now.date() - timedelta(1); streak = 0
    while d in days:
        streak += 1; d -= timedelta(1)
    by = {}
    for a in rows: by.setdefault((a.module, a.category or "General"), []).append(a.score)
    topics = sorted(((MODULES.get(m, m), c, round(sum(v) / len(v)), len(v)) for (m, c), v in by.items()), key=lambda t: t[2])
    return dict(rows=rows, n=len(rows), avg=round(sum(a.score for a in rows) / len(rows)) if rows else 0,
                week=sum(1 for a in rows if a.created > now - timedelta(7)), streak=streak, topics=topics,
                weak=[t for t in topics if t[2] < 60][:3],
                chart=[{"label": a.created.strftime("%d %b"), "score": round(a.score)} for a in reversed(rows[:12])])

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", s=stats(g.user.id), modules=MODULES, r=Resume.query.filter_by(user_id=g.user.id).first())

@bp.route("/progress")
@login_required
def progress():
    return render_template("progress.html", s=stats(g.user.id))

@bp.route("/visual")
@login_required
def visual():
    return render_template("visual.html")

SCENARIOS = {"Introduction": "Introduce yourself to a new team in 4 to 6 sentences.", "Workplace": "Explain a delay in your work to your manager politely.",
             "Interview": "Describe your biggest strength and give one example.", "Everyday": "Describe your usual day to a new friend.",
             "Presentation": "Open a 2-minute talk about a project you are proud of.", "Group discussion": "Give your opinion on remote work in 5 sentences."}

@bp.route("/english", methods=["GET", "POST"])
@login_required
def english():
    if request.method == "POST":
        sc, text = request.form.get("scenario", ""), request.form.get("answer", "").strip()[:3000]
        if sc not in SCENARIOS or len(text.split()) < 5:
            flash("Choose a scenario and write or speak at least a few words.", "error")
            return redirect(url_for("main.english"))
        dur = int(request.form["dur"]) if request.form.get("dur", "").isdigit() else 0
        r = en.check(text, dur); words = r["eval"]["words"]
        speech = {"seconds": dur, "wpm": round(words / (dur / 60)) if dur >= 10 else None, "fillers": r["eval"]["fillers"]}
        a = Attempt(user_id=g.user.id, module="english", category=sc, score=r["eval"]["score"], total=1,
                    detail={"question": SCENARIOS[sc], "answer": text, "eval": r["eval"], "corrections": r["corrections"], "improved": r["improved"], "speech": speech if dur else None})
        db.session.add(a); db.session.commit()
        return redirect(url_for("main.result", aid=a.id))
    return render_template("english.html", scenarios=SCENARIOS)

@bp.route("/aptitude")
@login_required
def aptitude():
    cats = [c for (c,) in db.session.query(Question.category).filter_by(module="aptitude").distinct()]
    return render_template("aptitude_start.html", cats=cats)

@bp.route("/aptitude/quiz")
@login_required
def quiz():
    q = Question.query.filter_by(module="aptitude")
    if request.args.get("category"): q = q.filter_by(category=request.args["category"])
    if request.args.get("difficulty"): q = q.filter_by(difficulty=request.args["difficulty"])
    qs = q.all()
    random.shuffle(qs)
    qs = qs[:10]
    if not qs:
        flash("No questions match that choice yet. Try another category or difficulty.", "error")
        return redirect(url_for("main.aptitude"))
    session["quiz"] = [x.id for x in qs]
    session["quiz_cat"] = request.args.get("category") or "Mixed"
    view = [{"q": x, "opts": random.sample(list(enumerate(x.options)), len(x.options))} for x in qs]
    return render_template("quiz.html", items=view, seconds=len(qs) * 60)

@bp.route("/aptitude/submit", methods=["POST"])
@login_required
def submit_quiz():
    ids = session.pop("quiz", None)
    if not ids:
        return redirect(url_for("main.aptitude"))
    items, correct = [], 0
    for x in Question.query.filter(Question.id.in_(ids)).all():
        p = request.form.get(f"q{x.id}", "")
        picked = int(p) if p.isdigit() and int(p) < len(x.options) else None
        ok = picked == x.answer
        correct += ok
        items.append({"text": x.text, "options": x.options, "picked": picked, "answer": x.answer, "explanation": x.explanation, "category": x.category, "ok": ok})
    el = request.form.get("elapsed", "0")
    a = Attempt(user_id=g.user.id, module="aptitude", category=session.get("quiz_cat"), total=len(items), domain=session.get("domain"),
                score=round(correct / len(items) * 100, 1), detail={"items": items, "correct": correct, "seconds": int(el) if el.isdigit() else 0})
    db.session.add(a)
    db.session.commit()
    return redirect(url_for("main.result", aid=a.id))

def bank(module):
    q = Question.query.filter_by(module=module)
    if module == "tech":
        return q.filter_by(domain=session.get("domain", "")).all() or q.filter_by(domain="General Graduate Placement").all() or q.all()
    return q.all()

@bp.app_context_processor
def inject_domain():
    return {"domain": session.get("domain", "General Graduate Placement"), "DOMAINS": DOMAINS}

@bp.route("/domain", methods=["POST"])
@login_required
def set_domain():
    custom = re.sub(r"[^A-Za-z0-9 /&.+#-]", "", request.form.get("custom", "")).strip()[:60]
    d = request.form.get("domain", "")
    session["domain"] = custom or (d if d in DOMAINS else "General Graduate Placement")
    session.pop("cur", None)
    nxt = request.form.get("next", "")
    flash("Domain set to %s." % session["domain"], "ok")
    return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt else url_for("main.dashboard"))

def pick_question(module):
    asked = session.get("asked", [])
    text, label = ai.new_question(module, asked, session.get("last", ""), session.get("domain", ""))
    if text:
        cur = {"text": text, "kw": "", "cat": "AI-generated", "label": label}
    else:
        pool = bank(module)
        fresh = [x for x in pool if x.text[:120] not in asked] or pool
        if not fresh:
            return None
        x = random.choice(fresh)
        cur = {"text": x.text, "kw": x.keywords or "", "cat": x.category, "label": "Sample question"}
    session["asked"] = (asked + [cur["text"][:120]])[-8:]
    session["cur"] = dict(cur, module=module)
    return cur

@bp.route("/practice/<module>", methods=["GET", "POST"])
@login_required
def practice(module):
    if module not in ("gd", "hr", "tech"):
        abort(404)
    cur = session.get("cur")
    if request.method == "POST":
        text = request.form.get("answer", "").strip()
        if not cur or cur.get("module") != module or len(text.split()) < 5:
            flash("Write at least a few words (or use Transcribe) before submitting.", "error")
            return redirect(url_for("main.practice", module=module))
        ev = ai.evaluate_answer(cur["text"], text) or evaluate(module, text, cur["kw"])
        ev.setdefault("words", len(text.split()))
        ev.setdefault("fillers", 0)
        num = lambda k: int(request.form.get(k, "0")) if request.form.get(k, "0").isdigit() else 0
        dur, words = num("dur"), len(text.split())
        speech = {"seconds": dur, "wpm": round(words / (dur / 60)) if dur >= 10 else None, "fillers": ev["fillers"]}
        fr, fok = num("vis_frames"), request.form.get("vis_face_ok") == "1"
        visual = {"frames": fr, "lit": round(100 * num("vis_lit") / fr), "face": round(100 * num("vis_face") / fr) if fok else None,
                  "centred": round(100 * num("vis_centre") / fr) if fok else None} if fr >= 3 else None
        a = Attempt(user_id=g.user.id, module=module, category=cur["cat"], score=ev["score"], total=1, domain=session.get("domain"),
                    detail={"question": cur["text"], "answer": text[:5000], "eval": ev, "speech": speech if dur else None, "visual": visual})
        db.session.add(a)
        db.session.commit()
        session["last"] = text[:200]
        session.pop("cur", None)
        return redirect(url_for("main.result", aid=a.id))
    if request.args.get("new") or not cur or cur.get("module") != module:
        cur = pick_question(module)
    return render_template("practice.html", q=cur, module=module, name=MODULES[module])

@bp.route("/result/<int:aid>")
@login_required
def result(aid):
    a = Attempt.query.filter_by(id=aid, user_id=g.user.id).first_or_404()
    return render_template("result.html", a=a, name=MODULES.get(a.module, a.module))

@bp.route("/history")
@login_required
def history():
    q = Attempt.query.filter_by(user_id=g.user.id)
    m = request.args.get("module")
    if m in MODULES: q = q.filter_by(module=m)
    return render_template("history.html", attempts=q.order_by(Attempt.created.desc()).all(), modules=MODULES, sel=m)

@bp.route("/resume", methods=["GET", "POST"])
@login_required
def resume():
    if request.method == "POST":
        f, jd = request.files.get("pdf"), request.form.get("jd", "").strip()[:8000]
        if not f or not f.filename.lower().endswith(".pdf") or f.mimetype != "application/pdf":
            flash("Choose a PDF file (max 2 MB).", "error")
            return redirect(url_for("main.resume"))
        text, err = rs.extract_text(f.stream)
        if err:
            flash(err, "error")
            return redirect(url_for("main.resume"))
        Resume.query.filter_by(user_id=g.user.id).delete()
        res = rs.analyze(text, jd)
        qs, label = ai.make_questions(res["matched"] or res["skills"], res["missing"])
        res.update(questions=qs, label=label)
        db.session.add(Resume(user_id=g.user.id, filename=os.path.basename(f.filename)[:120], text=text[:20000], jd=jd, result=res))
        db.session.commit()
        return redirect(url_for("main.resume"))
    return render_template("resume.html", r=Resume.query.filter_by(user_id=g.user.id).first(), ai_on=ai.configured())

@bp.route("/resume/delete", methods=["POST"])
@login_required
def resume_delete():
    Resume.query.filter_by(user_id=g.user.id).delete()
    db.session.commit()
    flash("Your resume and extracted text were deleted.", "ok")
    return redirect(url_for("main.resume"))

def _d(s):
    try: return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError): return None

def _rows(uid, start, end, module):
    rows = Attempt.query.filter_by(user_id=uid).order_by(Attempt.created).all()  # only this user's records
    keep = [a for a in rows if (not module or a.module == module) and (not start or a.created.date() >= start) and (not end or a.created.date() <= end)]
    return eda.valid(keep)

def _filters():
    f = {k: request.args.get(k, "") for k in ("start", "end", "module")}
    if f["module"] not in MODULES: f["module"] = ""
    return f

@bp.route("/insights")
@login_required
def insights():
    f = _filters()
    rows, bad = _rows(g.user.id, _d(f["start"]), _d(f["end"]), f["module"])
    return render_template("insights.html", f=f, d=eda.summary(rows, MODULES), bad=bad, modules=MODULES)

@bp.route("/insights/export.csv")
@login_required
def insights_csv():
    f = _filters()
    rows, _ = _rows(g.user.id, _d(f["start"]), _d(f["end"]), f["module"])
    out = io.StringIO(); w = csv.writer(out); w.writerow(["date", "module", "topic", "score_percent"])
    safe = lambda v: "'" + v if v and v[0] in "=+-@" else v
    for a in rows: w.writerow([a.created.strftime("%Y-%m-%d"), a.module, safe(a.category or ""), a.score])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=insights.csv"})

@bp.route("/insights/compare")
@login_required
def compare():
    today = datetime.utcnow().date()
    q = lambda k, dflt: _d(request.args.get(k)) or dflt
    p = {"a0": q("a_start", today - timedelta(60)), "a1": q("a_end", today - timedelta(31)), "b0": q("b_start", today - timedelta(30)), "b1": q("b_end", today),
         "module": request.args.get("module", "") if request.args.get("module") in MODULES else ""}
    A, _ = _rows(g.user.id, p["a0"], p["a1"], p["module"]); B, _ = _rows(g.user.id, p["b0"], p["b1"], p["module"])
    return render_template("compare.html", c=eda.compare(A, B), topics=eda.topic_compare(A, B, MODULES), p=p, modules=MODULES)

RATE = {}

@bp.route("/coach")
@login_required
def coach():
    return render_template("coach.html")

@bp.route("/coach/history")
@login_required
def coach_history():
    ms = ChatMessage.query.filter_by(user_id=g.user.id).order_by(ChatMessage.id).all()[-50:]
    return {"messages": [{"role": m.role, "content": m.content, "label": m.label, "time": m.created.strftime("%H:%M")} for m in ms]}

@bp.route("/coach/message", methods=["POST"])
@login_required
def coach_message():
    data = request.get_json(silent=True)
    msg = data.get("message") if isinstance(data, dict) else None
    if not isinstance(msg, str) or not msg.strip() or len(msg) > 1000:
        return {"error": "Type a message of 1 to 1000 characters."}, 400
    now = time.time(); hits = [t for t in RATE.get(g.user.id, []) if now - t < 60]
    if len(hits) >= 15:
        return {"error": "You are sending messages too quickly. Please wait a moment."}, 429
    RATE[g.user.id] = hits + [now]
    msg = msg.strip()
    hist = ChatMessage.query.filter_by(user_id=g.user.id).order_by(ChatMessage.id.desc()).limit(10).all()[::-1]
    last = Attempt.query.filter_by(user_id=g.user.id).order_by(Attempt.created.desc()).first()
    ctx = {"weak": stats(g.user.id)["weak"], "improve": ((last.detail or {}).get("eval", {}).get("improvements", []) if last else [])}
    reply, label, acts = iq.respond(msg, [{"role": m.role, "content": m.content} for m in hist], ctx)
    db.session.add(ChatMessage(user_id=g.user.id, role="user", content=msg))
    db.session.add(ChatMessage(user_id=g.user.id, role="assistant", content=reply, label=label))
    db.session.commit()
    return {"reply": reply, "label": label, "actions": [{"label": l, "url": url_for(e, **k)} for l, e, k in acts]}

@bp.route("/coach/clear", methods=["POST"])
@login_required
def coach_clear():
    ChatMessage.query.filter_by(user_id=g.user.id).delete()
    db.session.commit()
    return {"ok": True}

@bp.route("/video")
@login_required
def video():
    return render_template("video.html")

@bp.route("/video/questions")
@login_required
def video_questions():
    pool = Question.query.filter_by(module="hr").all()
    out = []
    for x in random.sample(pool, min(3, len(pool))):
        t, _ = ai.new_question("hr", [o["text"] for o in out], "", session.get("domain", "")) if ai.configured() else (None, None)
        out.append({"text": t or x.text})
    return {"questions": out}

@bp.route("/video/answer", methods=["POST"])
@login_required
def video_answer():
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or not isinstance(d.get("question"), str) or not isinstance(d.get("answer"), str) or len(d["answer"].split()) < 5 or len(d["answer"]) > 5000:
        return {"error": "Speak or type at least a few words before finishing."}, 400
    num = lambda v, hi: max(0, min(hi, v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0
    segs = [{"text": str(s.get("text", ""))[:300], "conf": num(s.get("conf"), 1)} for s in (d.get("segments") or [])[:60] if isinstance(s, dict)]
    pauses = [num(p, 600000) for p in (d.get("pauses") or [])[:100]]
    first = d.get("first_ms"); first = num(first, 600000) if first is not None else None
    v = d.get("vis") if isinstance(d.get("vis"), dict) else {}
    fr = int(num(v.get("frames"), 3600)); fok = v.get("face_ok") is True
    pc = lambda k: round(100 * num(v.get(k), fr) / fr) if fr else 0
    vis = {"frames": fr, "lit": pc("lit"), "face": pc("face") if fok else None, "centred": pc("centre") if fok else None} if fr >= 3 else None
    row = Question.query.filter_by(text=d["question"]).first()
    r = vd.build(d["question"], d["answer"].strip(), row.keywords if row else "", num(d.get("dur"), 3600), segs, pauses, first, vis)
    a = Attempt(user_id=g.user.id, module="video", category="Video interview", score=r["ev"]["score"], total=1, domain=session.get("domain"),
                detail={"question": d["question"][:300], "answer": d["answer"].strip(), "eval": r["ev"], "speech": r["speech"], "visual": vis,
                        "issues": r["issues"], "corrections": r["corrections"], "improved": r["improved"]})
    db.session.add(a); db.session.commit()
    return {"id": a.id, "url": url_for("main.result", aid=a.id), "score": r["ev"]["score"], "label": r["ev"]["label"], "issues": r["issues"],
            "corrections": r["corrections"], "improved": r["improved"], "speech": r["speech"]}
