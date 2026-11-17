"""
app.py  — SSBM Frame Data Database
COMP 3005 Term Project — Evan Mindanao (101392044)

Flask backend: serves the HTML UI and exposes JSON API endpoints.
All queries use raw SQL executed against the SQLite3 database (no ORM).
"""

import sqlite3, os
from flask import Flask, g, jsonify, request, render_template, abort

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "ssbm_framedata.db")


# ── DB connection helpers ─────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()


def query(sql, params=()):
    """Run a SELECT and return list of dicts."""
    cur = get_db().execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def execute(sql, params=()):
    """Run INSERT/UPDATE/DELETE; return lastrowid."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid


# ─────────────────────────────────────────────────────────────────────────────
# UI Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────────────────────
# API — Characters
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/characters")
def api_characters():
    """R1: List all characters with attributes."""
    rows = query("""
        SELECT char_id, char_name, weight, gravity, fall_speed,
               air_speed, run_speed, tier
        FROM   characters
        ORDER  BY tier, char_name
    """)
    return jsonify(rows)


@app.route("/api/characters/<int:char_id>")
def api_character_detail(char_id):
    """R1: Single character + all their moves (N:N join)."""
    char = query(
        "SELECT * FROM characters WHERE char_id = ?", (char_id,)
    )
    if not char:
        abort(404)

    # N:N join: characters ↔ moves via character_moves
    moves = query("""
        SELECT m.move_name, m.move_type,
               cm.cm_id, cm.startup_frames, cm.active_frames,
               cm.total_frames, cm.damage, cm.shield_stun,
               cm.frame_advantage, cm.input_command
        FROM   character_moves cm
        JOIN   moves m ON cm.move_id = m.move_id
        WHERE  cm.char_id = ?
        ORDER  BY m.move_type, m.move_name
    """, (char_id,))

    return jsonify({"character": char[0], "moves": moves})


# ─────────────────────────────────────────────────────────────────────────────
# API — Move Comparison  (R2)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/compare")
def api_compare():
    """
    R2: Compare a move type across all characters.
    ?move_name=Forward+Smash   (or any move_name from the moves table)
    """
    move_name = request.args.get("move_name", "")
    if not move_name:
        return jsonify([])

    rows = query("""
        SELECT c.char_name, c.tier, m.move_type,
               cm.startup_frames, cm.active_frames, cm.total_frames,
               cm.damage, cm.shield_stun, cm.frame_advantage,
               cm.input_command
        FROM   character_moves cm
        JOIN   characters c ON cm.char_id  = c.char_id
        JOIN   moves      m ON cm.move_id  = m.move_id
        WHERE  m.move_name = ?
        ORDER  BY cm.startup_frames ASC
    """, (move_name,))
    return jsonify(rows)


@app.route("/api/move_names")
def api_move_names():
    """Return distinct move names for the comparison dropdown."""
    rows = query("SELECT DISTINCT move_name FROM moves ORDER BY move_type, move_name")
    return jsonify([r["move_name"] for r in rows])


# ─────────────────────────────────────────────────────────────────────────────
# API — Frame Advantage / Filtering  (R3, R5)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/filter")
def api_filter():
    """
    R3 / R5: Filter moves by frame or damage criteria.
    Query params (all optional):
      max_startup   — startup_frames <= X
      min_damage    — damage >= X
      safe_only     — frame_advantage >= 0  (safe on shield)
      move_type     — ground / aerial / special / grab
    """
    conditions = []
    params = []

    max_startup = request.args.get("max_startup")
    min_damage  = request.args.get("min_damage")
    safe_only   = request.args.get("safe_only")
    move_type   = request.args.get("move_type")

    if max_startup:
        conditions.append("cm.startup_frames <= ?")
        params.append(int(max_startup))
    if min_damage:
        conditions.append("cm.damage >= ?")
        params.append(float(min_damage))
    if safe_only == "1":
        conditions.append("cm.frame_advantage >= 0")
    if move_type and move_type in ("ground", "aerial", "special", "grab"):
        conditions.append("m.move_type = ?")
        params.append(move_type)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = query(f"""
        SELECT c.char_name, m.move_name, m.move_type,
               cm.startup_frames, cm.active_frames, cm.total_frames,
               cm.damage, cm.shield_stun, cm.frame_advantage,
               cm.input_command, cm.cm_id
        FROM   character_moves cm
        JOIN   characters c ON cm.char_id = c.char_id
        JOIN   moves      m ON cm.move_id = m.move_id
        {where}
        ORDER  BY cm.startup_frames ASC, cm.damage DESC
    """, params)
    return jsonify(rows)


# ─────────────────────────────────────────────────────────────────────────────
# API — Matchups  (R4)  — demonstrates N:N self-referencing relationship
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/matchups")
def api_matchups():
    """
    R4: All matchups. Optional ?char_id=X to filter to one character.
    This query joins characters twice (self-referencing N:N).
    """
    char_id = request.args.get("char_id")

    if char_id:
        rows = query("""
            SELECT mu.matchup_id,
                   c1.char_id AS c1_id, c1.char_name AS char1,
                   c2.char_id AS c2_id, c2.char_name AS char2,
                   mu.advantage_score, mu.matchup_notes
            FROM   matchups mu
            JOIN   characters c1 ON mu.char_id_1 = c1.char_id
            JOIN   characters c2 ON mu.char_id_2 = c2.char_id
            WHERE  c1.char_id = ? OR c2.char_id = ?
            ORDER  BY ABS(mu.advantage_score) DESC
        """, (char_id, char_id))
    else:
        rows = query("""
            SELECT mu.matchup_id,
                   c1.char_id AS c1_id, c1.char_name AS char1,
                   c2.char_id AS c2_id, c2.char_name AS char2,
                   mu.advantage_score, mu.matchup_notes
            FROM   matchups mu
            JOIN   characters c1 ON mu.char_id_1 = c1.char_id
            JOIN   characters c2 ON mu.char_id_2 = c2.char_id
            ORDER  BY c1.char_name, c2.char_name
        """)
    return jsonify(rows)


@app.route("/api/matchups/<int:matchup_id>")
def api_matchup_detail(matchup_id):
    """
    R3.6 secondary query: click a matchup → load its community notes.
    Demonstrates: first query (matchup list) → secondary query (notes for that matchup).
    """
    matchup = query("""
        SELECT mu.matchup_id,
               c1.char_name AS char1, c2.char_name AS char2,
               mu.advantage_score, mu.matchup_notes
        FROM   matchups mu
        JOIN   characters c1 ON mu.char_id_1 = c1.char_id
        JOIN   characters c2 ON mu.char_id_2 = c2.char_id
        WHERE  mu.matchup_id = ?
    """, (matchup_id,))
    if not matchup:
        abort(404)

    notes = query("""
        SELECT note_id, note_text, note_author, note_date
        FROM   notes
        WHERE  note_matchup_id = ?
        ORDER  BY note_date DESC
    """, (matchup_id,))

    return jsonify({"matchup": matchup[0], "notes": notes})


# ─────────────────────────────────────────────────────────────────────────────
# API — Move Notes  (secondary refinement on a character's move)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/move_notes/<int:cm_id>")
def api_move_notes(cm_id):
    """
    R3.6 secondary query: click a move → load community notes for it.
    """
    move_info = query("""
        SELECT c.char_name, m.move_name, cm.damage, cm.startup_frames,
               cm.frame_advantage
        FROM   character_moves cm
        JOIN   characters c ON cm.char_id = c.char_id
        JOIN   moves      m ON cm.move_id = m.move_id
        WHERE  cm.cm_id = ?
    """, (cm_id,))
    if not move_info:
        abort(404)

    notes = query("""
        SELECT note_id, note_text, note_author, note_date
        FROM   notes
        WHERE  note_cm_id = ?
        ORDER  BY note_date DESC
    """, (cm_id,))

    return jsonify({"move": move_info[0], "notes": notes})


# ─────────────────────────────────────────────────────────────────────────────
# API — Add Note  (R6 community annotations)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/notes", methods=["POST"])
def api_add_note():
    """R6: Add a community annotation to a move or matchup."""
    data = request.get_json()
    cm_id      = data.get("note_cm_id")
    mu_id      = data.get("note_matchup_id")
    text       = (data.get("note_text") or "").strip()
    author     = (data.get("note_author") or "Anonymous").strip()

    if not text:
        return jsonify({"error": "note_text is required"}), 400
    if not cm_id and not mu_id:
        return jsonify({"error": "Must supply note_cm_id or note_matchup_id"}), 400

    new_id = execute(
        "INSERT INTO notes(note_cm_id,note_matchup_id,note_text,note_author) VALUES(?,?,?,?)",
        (cm_id, mu_id, text, author),
    )
    return jsonify({"note_id": new_id}), 201


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
