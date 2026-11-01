from datetime import date
from pathlib import Path
import sqlite3

# FIXED: Explicitly imported render_template_string
from flask import Flask, flash, g, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.secret_key = "change-this-for-a-deployed-app"
DB_PATH = Path(__file__).parent / "backing_rescue.db"

HTML = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rescue Plan</title><style>
* {box-sizing:border-box;} body {margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; background:#f0f2f5; color:#1c1e21; padding:20px; line-height:1.5;}
header {max-width:1200px; margin:0 auto 20px; padding:20px; background:#1877f2; color:#fff; border-radius:8px;} header h1 {margin:0 0 5px; font-size:28px;} header p {margin:0; opacity:0.9;}
.stats {display:flex; gap:12px; margin-bottom:20px;} .stat {flex:1; min-width:145px; background:#fff; border:1px solid #e4e6eb; border-radius:12px; padding:15px;}
.stat strong {display:block; font-size:24px; color:#1877f2;} .stat span {font-size:12px; color:#65676b;}
.grid {display:grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap:16px; max-width:1200px; margin:0 auto;}
.panel {background:#fff; border:1px solid #e4e6eb; border-radius:12px; padding:20px;} .panel h2 {margin:0 0 16px; font-size:18px; border-bottom:1px solid #e4e6eb; padding-bottom:10px;}
label {display:block; font-size:12px; font-weight:bold; margin-bottom:6px; color:#65676b;}
input {width:100%; padding:10px; border:1px solid #ccd0d5; border-radius:6px; margin-bottom:12px; font-size:14px;}
button {background:#1877f2; color:#fff; border:none; padding:10px 20px; font-size:14px; font-weight:bold; border-radius:6px; cursor:pointer; width:100%; transition:background 0.2s;}
button:hover {background:#166fe5;}
.flash {background:#e7f3ff; color:#1877f2; padding:12px; border-radius:6px; margin-bottom:16px; font-size:14px;}
.muted {color:#65676b; font-size:13px;} ol {padding-left:20px; margin:10px 0;} li {margin-bottom:8px;}
.topic-list {list-style:none; padding:0; margin:0;}
.topic-item {display:flex; justify-content:between; align-items:center; padding:12px; border-bottom:1px solid #f0f2f5;}
.topic-item:last-child {border-bottom:none;}
.badge {font-size:11px; padding:3px 8px; border-radius:12px; font-weight:bold;}
.badge-done {background:#e7f3ff; color:#1877f2;}
.badge-progress {background:#fef3c7; color:#d97706;}
.badge-overdue {background:#fee2e2; color:#dc2626;}
.inline-form {margin:0;} .btn-link {background:none; border:none; color:#1877f2; text-decoration:underline; cursor:pointer; padding:0; font-size:13px;}
.resources a {display:block; margin-bottom:8px; color:#1877f2; text-decoration:none;} .resources a:hover {text-decoration:underline;}
</style></head><body>
<header><h1>Rescue Plan</h1><p>Simple academic recovery planner: organize topics, set targets, and track progress.</p></header>
<main class="grid">
    {% with messages = get_flashed_messages() %}
        {% if messages %}{% for msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}
    {% endwith %}
    
    <section class="panel">
        <h2>Progress Overview</h2>
        <div class="stats">
            <div class="stat"><strong>{{ completed }} / {{ total }}</strong><span>Topics Completed</span></div>
            <div class="stat"><strong>{{ percent }}%</strong><span>Completion Rate</span></div>
        </div>
        <h2>Quick-Start Guide</h2>
        <p class="muted">Try one manageable session at a time:</p>
        <ol class="muted">
            <li><strong>Choose one topic</strong> from your list.</li>
            <li><strong>Study for 25 minutes</strong>, then take a 5-minute break.</li>
            <li><strong>Practice</strong> a few questions and note doubts.</li>
            <li><strong>Mark the topic complete</strong> when you feel ready.</li>
        </ol>
    </section>

    <section class="panel">
        <h2>Add Backlog Topic</h2>
        <form method="post" action="{{ url_for('add_topic') }}">
            <label for="subject">Subject</label>
            <input id="subject" name="subject" required maxlength="80" placeholder="e.g., Mathematics">
            
            <label for="topic">Topic to Study</label>
            <input id="topic" name="topic" required maxlength="160" placeholder="e.g., Integration">
            
            <label for="due_date">Target Date (optional)</label>
            <input id="due_date" name="due_date" type="date" min="{{ today }}">
            
            <button type="submit">Add to Plan</button>
        </form>
    </section>

    <section class="panel">
        <h2>My Backlog Topics</h2>
        {% if topics %}
            <ul class="topic-list">
            {% for item in topics %}
                <li class="topic-item">
                    <div style="flex:1;">
                        <strong>[{{ item['subject'] }}]</strong> {{ item['topic'] }}
                        <div class="muted">
                            {% if item['due_date'] %}
                                Due: {{ item['due_date'] }}
                                {% if item['done'] %}
                                    <span class="badge badge-done">Completed</span>
                                {% elif item['due_date'] < today %}
                                    <span class="badge badge-overdue">Overdue</span>
                                {% else %}
                                    <span class="badge badge-progress">In Progress</span>
                                {% endif %}
                            {% else %}
                                {% if item['done'] %}
                                    <span class="badge badge-done">Completed</span>
                                {% else %}
                                    <span class="badge badge-progress">In Progress</span>
                                {% endif %}
                            {% endif %}
                        </div>
                    </div>
                    <form class="inline-form" method="post" action="{{ url_for('toggle_topic', topic_id=item['id']) }}">
                        <button type="submit" class="btn-link">{% if item['done'] %}Mark Incomplete{% else %}Mark Done{% endif %}</button>
                    </form>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p class="muted">No topics added yet. Fill out the form above to start!</p>
        {% endif %}
    </section>

    <section class="panel">
        <h2>Starter Learning Resources</h2>
        <div class="resources">
            <a href="https://www.khanacademy.org/" target="_blank" rel="noopener">Khan Academy &mdash; explanations and practices</a>
            <a href="https://ncert.nic.in" target="_blank" rel="noopener">NCERT Textbooks &mdash; textbook chapters/pdfs</a>
            <a href="https://geeksforgeeks.org" target="_blank" rel="noopener">GeeksforGeeks &mdash; CS/coding topics</a>
        </div>
        <p class="muted" style="margin-top:20px; font-size:11px;">Your topics are stored locally in this project's SQLite database.</p>
    </section>
</main>
</body></html>
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(errors=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0
            )
        """)
        db.commit()

@app.get("/")
def index():
    db = get_db()
    topics = db.execute("SELECT * FROM topics ORDER BY done ASC, due_date IS NULL, due_date ASC").fetchall()
    total = len(topics)
    completed = sum(1 for item in topics if item["done"])
    percent = int((completed / total) * 100) if total > 0 else 0
    
    # FIXED: Replaced standard file rendering with string rendering block
    return render_template_string(
        HTML, 
        topics=topics, 
        total=total, 
        completed=completed, 
        percent=percent, 
        today=date.today().isoformat()
    )

@app.post("/topics")
def add_topic():
    subject = request.form.get("subject", "").strip()
    topic = request.form.get("topic", "").strip()
    due_date = request.form.get("due_date", "").strip() or None
    
    if not subject or not topic:
        flash("Please provide both a subject and a topic.")
        return redirect(url_for("index"))
        
    if due_date and due_date < date.today().isoformat():
        flash("Target date cannot be in the past.")
        return redirect(url_for("index"))
        
    db = get_db()
    # FIXED: Sanitized SQL parameter interpolation
    db.execute("INSERT INTO topics (subject, topic, due_date) VALUES (?, ?, ?)", (subject, topic, due_date))
    db.commit()
    
    flash(f"Added topic: {topic}")
    return redirect(url_for("index"))

@app.post("/topics/<int:topic_id>/toggle")
def toggle_topic(topic_id):
    db = get_db()
    db.execute("UPDATE topics SET done = CASE WHEN done = 1 THEN 0 ELSE 1 END WHERE id = ?", (topic_id,))
    db.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()  
    app.run(debug=True)
