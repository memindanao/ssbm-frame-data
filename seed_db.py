"""
seed_db.py
----------
Creates and seeds the SSBM Frame Data SQLite3 database.
Run once: python seed_db.py
"""

import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "ssbm_framedata.db")

# ── DDL ──────────────────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS characters (
    char_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    char_name  TEXT    NOT NULL UNIQUE,
    weight     REAL    NOT NULL,
    gravity    REAL    NOT NULL,
    fall_speed REAL    NOT NULL,
    air_speed  REAL    NOT NULL,
    run_speed  REAL    NOT NULL,
    tier       TEXT
);

CREATE TABLE IF NOT EXISTS moves (
    move_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    move_name TEXT    NOT NULL,
    move_type TEXT    NOT NULL CHECK(move_type IN ('ground','aerial','special','grab'))
);

CREATE TABLE IF NOT EXISTS character_moves (
    cm_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    char_id          INTEGER NOT NULL REFERENCES characters(char_id) ON DELETE CASCADE,
    move_id          INTEGER NOT NULL REFERENCES moves(move_id)      ON DELETE CASCADE,
    startup_frames   INTEGER NOT NULL,
    active_frames    INTEGER NOT NULL,
    total_frames     INTEGER NOT NULL,
    damage           REAL    NOT NULL,
    shield_stun      INTEGER,
    frame_advantage  INTEGER,
    input_command    TEXT,
    UNIQUE(char_id, move_id)
);

CREATE TABLE IF NOT EXISTS matchups (
    matchup_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    char_id_1       INTEGER NOT NULL REFERENCES characters(char_id) ON DELETE CASCADE,
    char_id_2       INTEGER NOT NULL REFERENCES characters(char_id) ON DELETE CASCADE,
    advantage_score REAL,
    matchup_notes   TEXT,
    UNIQUE(char_id_1, char_id_2),
    CHECK(char_id_1 < char_id_2)
);

CREATE TABLE IF NOT EXISTS notes (
    note_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    note_cm_id      INTEGER REFERENCES character_moves(cm_id) ON DELETE SET NULL,
    note_matchup_id INTEGER REFERENCES matchups(matchup_id)   ON DELETE SET NULL,
    note_text       TEXT    NOT NULL,
    note_author     TEXT    NOT NULL,
    note_date       TEXT    DEFAULT (date('now')),
    CHECK(note_cm_id IS NOT NULL OR note_matchup_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_cm_char   ON character_moves(char_id);
CREATE INDEX IF NOT EXISTS idx_cm_move   ON character_moves(move_id);
CREATE INDEX IF NOT EXISTS idx_mu_c1     ON matchups(char_id_1);
CREATE INDEX IF NOT EXISTS idx_mu_c2     ON matchups(char_id_2);
CREATE INDEX IF NOT EXISTS idx_note_cm   ON notes(note_cm_id);
CREATE INDEX IF NOT EXISTS idx_note_mu   ON notes(note_matchup_id);
"""

# ── Seed Data ─────────────────────────────────────────────────────────────────

CHARACTERS = [
    # name,            weight, gravity, fall_speed, air_speed, run_speed, tier
    ("Fox",            77,     0.23,    3.10,       0.83,      2.20,      "S"),
    ("Falco",          80,     0.17,    3.10,       0.68,      1.87,      "S"),
    ("Marth",          87,     0.10,    1.90,       0.90,      1.80,      "S"),
    ("Jigglypuff",     60,     0.06,    1.30,       0.97,      1.50,      "S"),
    ("Captain Falcon", 104,    0.13,    2.90,       1.12,      2.31,      "A"),
]

# Generic move types shared across characters
MOVE_TYPES = [
    # move_name,            move_type
    ("Jab",                 "ground"),
    ("Down Tilt",           "ground"),
    ("Up Tilt",             "ground"),
    ("Forward Tilt",        "ground"),
    ("Dash Attack",         "ground"),
    ("Forward Smash",       "ground"),
    ("Up Smash",            "ground"),
    ("Down Smash",          "ground"),
    ("Neutral Air",         "aerial"),
    ("Forward Air",         "aerial"),
    ("Back Air",            "aerial"),
    ("Up Air",              "aerial"),
    ("Down Air",            "aerial"),
    ("Neutral Special",     "special"),
    ("Side Special",        "special"),
    ("Up Special",          "special"),
    ("Down Special",        "special"),
    ("Grab",                "grab"),
]

# character_moves: (char_name, move_name, startup, active, total, damage, shield_stun, frame_adv, input)
# Sources: meleeframedata.com community data
CHARACTER_MOVES = [
    # ── FOX ──────────────────────────────────────────────────────────────────
    ("Fox", "Jab",             1,  2,  15,  2.0,   2,   4,  "A"),
    ("Fox", "Down Tilt",       4,  4,  18,  6.0,   5,   1,  "↓+A"),
    ("Fox", "Up Tilt",         4,  4,  23,  8.0,   6,   0,  "↑+A"),
    ("Fox", "Forward Tilt",    6,  3,  22,  9.0,   6,   1,  "→+A"),
    ("Fox", "Dash Attack",     5,  2,  28,  7.0,   5,  -6,  "Dash+A"),
    ("Fox", "Forward Smash",   9,  3,  38, 15.0,  10,  -4,  "→+A (smash)"),
    ("Fox", "Up Smash",        5,  3,  47, 13.0,   9,  -9,  "↑+A (smash)"),
    ("Fox", "Down Smash",      4,  2,  35, 12.0,   8, -10,  "↓+A (smash)"),
    ("Fox", "Neutral Air",     3,  3,  26,  6.0,   5,   2,  "A (air)"),
    ("Fox", "Forward Air",    10,  3,  38, 12.0,   8,  -4,  "→+A (air)"),
    ("Fox", "Back Air",        5,  4,  30, 11.0,   7,   2,  "←+A (air)"),
    ("Fox", "Up Air",          5,  5,  26,  9.0,   6,   4,  "↑+A (air)"),
    ("Fox", "Down Air",        9, 14,  42,  2.0,   2, -10,  "↓+A (air)"),
    ("Fox", "Neutral Special", 1,  1,  16,  3.5,   3,   3,  "B"),
    ("Fox", "Side Special",    3,  2,  30, 10.0,   7,  -4,  "→+B"),
    ("Fox", "Up Special",      3, 20,  46,  3.0,   3, -20,  "↑+B"),
    ("Fox", "Down Special",   19,  1,  30,  0.0,   0,   0,  "↓+B"),
    ("Fox", "Grab",            6,  1,  30,  0.0,   0,   0,  "Z / L+A"),

    # ── FALCO ────────────────────────────────────────────────────────────────
    ("Falco", "Jab",             2,  2,  17,  3.0,   2,   2,  "A"),
    ("Falco", "Down Tilt",       7,  3,  29, 13.0,   7,  -5,  "↓+A"),
    ("Falco", "Up Tilt",         5,  4,  24,  8.0,   6,  -2,  "↑+A"),
    ("Falco", "Forward Tilt",    7,  4,  27, 10.0,   7,  -3,  "→+A"),
    ("Falco", "Dash Attack",     4,  2,  32,  8.0,   6,  -9,  "Dash+A"),
    ("Falco", "Forward Smash",   6,  3,  39, 13.0,   8,  -4,  "→+A (smash)"),
    ("Falco", "Up Smash",        5,  3,  43, 14.0,   9,  -7,  "↑+A (smash)"),
    ("Falco", "Down Smash",      4,  4,  37, 12.0,   8, -12,  "↓+A (smash)"),
    ("Falco", "Neutral Air",     4,  4,  31,  8.0,   6,  -2,  "A (air)"),
    ("Falco", "Forward Air",     7,  3,  36, 15.0,  10,  -3,  "→+A (air)"),
    ("Falco", "Back Air",        4, 16,  35, 13.0,   7,   1,  "←+A (air)"),
    ("Falco", "Up Air",          6,  4,  31,  7.0,   6,  -2,  "↑+A (air)"),
    ("Falco", "Down Air",        9, 13,  45,  2.0,   2, -12,  "↓+A (air)"),
    ("Falco", "Neutral Special", 4,  1,  34,  3.5,   3,  -2,  "B"),
    ("Falco", "Side Special",    3,  2,  30, 10.0,   7,  -4,  "→+B"),
    ("Falco", "Up Special",      3, 20,  46,  3.0,   3, -20,  "↑+B"),
    ("Falco", "Down Special",   19,  1,  30,  0.0,   0,   0,  "↓+B"),
    ("Falco", "Grab",            7,  1,  32,  0.0,   0,   0,  "Z / L+A"),

    # ── MARTH ────────────────────────────────────────────────────────────────
    ("Marth", "Jab",             5,  2,  24,  4.0,   4,   1,  "A"),
    ("Marth", "Down Tilt",       4,  3,  22,  8.0,   6,   7,  "↓+A"),
    ("Marth", "Up Tilt",         6,  5,  30,  9.0,   7,   2,  "↑+A"),
    ("Marth", "Forward Tilt",    7,  4,  30, 12.0,   8,  -1,  "→+A"),
    ("Marth", "Dash Attack",     8,  3,  35, 10.0,   7,  -8,  "Dash+A"),
    ("Marth", "Forward Smash",  13,  4,  45, 17.0,  11,  -5,  "→+A (smash)"),
    ("Marth", "Up Smash",        8,  5,  44, 14.0,   9,  -8,  "↑+A (smash)"),
    ("Marth", "Down Smash",      6,  4,  40, 14.0,   9, -12,  "↓+A (smash)"),
    ("Marth", "Neutral Air",     4,  5,  32,  9.0,   6,   2,  "A (air)"),
    ("Marth", "Forward Air",     8,  3,  39, 12.0,   8,  -3,  "→+A (air)"),
    ("Marth", "Back Air",        6,  3,  35, 11.0,   7,   2,  "←+A (air)"),
    ("Marth", "Up Air",          6,  4,  34, 10.0,   7,   0,  "↑+A (air)"),
    ("Marth", "Down Air",       11,  4,  44, 15.0,  10,  -8,  "↓+A (air)"),
    ("Marth", "Neutral Special", 5,  1,  60,  8.0,   6, -30,  "B"),
    ("Marth", "Side Special",    9,  3,  36, 12.0,   8,  -5,  "→+B"),
    ("Marth", "Up Special",      3, 10,  50, 10.0,   7, -30,  "↑+B"),
    ("Marth", "Down Special",    4,  3,  34,  8.0,   6,  -4,  "↓+B"),
    ("Marth", "Grab",            7,  1,  35,  0.0,   0,   0,  "Z / L+A"),

    # ── JIGGLYPUFF ───────────────────────────────────────────────────────────
    ("Jigglypuff", "Jab",             4,  2,  16,  2.0,   2,   4,  "A"),
    ("Jigglypuff", "Down Tilt",       4,  3,  20,  9.0,   6,   8,  "↓+A"),
    ("Jigglypuff", "Forward Smash",  10,  4,  46, 21.0,  14,  -8,  "→+A (smash)"),
    ("Jigglypuff", "Neutral Air",     4,  5,  26,  8.0,   6,   4,  "A (air)"),
    ("Jigglypuff", "Forward Air",     9,  3,  31, 12.0,   8,  -1,  "→+A (air)"),
    ("Jigglypuff", "Back Air",        7,  3,  30, 12.0,   8,   1,  "←+A (air)"),
    ("Jigglypuff", "Up Air",          6,  5,  27,  9.0,   6,   4,  "↑+A (air)"),
    ("Jigglypuff", "Down Air",        9,  3,  35, 12.0,   8,  -3,  "↓+A (air)"),
    ("Jigglypuff", "Neutral Special", 9,  1,  50,  0.0,   0,   0,  "B"),
    ("Jigglypuff", "Up Special",      3, 30,  46,  2.0,   2, -20,  "↑+B"),

    # ── CAPTAIN FALCON ───────────────────────────────────────────────────────
    ("Captain Falcon", "Jab",             3,  2,  18,  5.0,   4,   2,  "A"),
    ("Captain Falcon", "Down Tilt",       5,  3,  25,  9.0,   6,   2,  "↓+A"),
    ("Captain Falcon", "Forward Smash",  10,  4,  48, 21.0,  14,  -9,  "→+A (smash)"),
    ("Captain Falcon", "Neutral Air",     4,  4,  28,  8.0,   6,   2,  "A (air)"),
    ("Captain Falcon", "Forward Air",     8,  3,  37, 10.0,   7,  -3,  "→+A (air)"),
    ("Captain Falcon", "Back Air",        7,  3,  35, 13.0,   9,  -1,  "←+A (air)"),
    ("Captain Falcon", "Up Air",          5,  4,  29,  9.0,   6,   3,  "↑+A (air)"),
    ("Captain Falcon", "Down Air",        9,  5,  49, 15.0,  10, -15,  "↓+A (air)"),
    ("Captain Falcon", "Neutral Special", 4,  1,  55, 12.0,   8, -40,  "B (Falcon Punch)"),
    ("Captain Falcon", "Up Special",      3, 10,  50,  5.0,   4, -30,  "↑+B"),
]

# matchups: (char1, char2, advantage_score, notes)
# Positive score = char1 has advantage; convention: char1 name < char2 name alphabetically by char_id
MATCHUPS = [
    ("Captain Falcon", "Falco",        -1.5, "Falco's lasers limit Falcon's approach badly. Falcon wins off CG punishes."),
    ("Captain Falcon", "Fox",          -1.0, "Fox's speed and shine pressure trouble Falcon. Falcon punishes hard off grabs."),
    ("Captain Falcon", "Jigglypuff",   -0.5, "Even-ish. Falcon can rest bait; Puff struggles vs Falcon's aerial speed."),
    ("Captain Falcon", "Marth",        -1.0, "Marth tipper range keeps Falcon out. Falcon needs to get inside."),
    ("Falco",          "Fox",           0.5, "Falco's lasers force Fox approaches. Fox can shine spike and has better movement."),
    ("Falco",          "Jigglypuff",    1.0, "Lasers destroy Puff's approach. Falco wins neutral heavily."),
    ("Falco",          "Marth",         0.5, "Falco's CG on Marth is devastating. Marth's range is a challenge in neutral."),
    ("Fox",            "Jigglypuff",    1.0, "Fox's shine and speed overwhelm Puff. Puff needs one rest to swing it."),
    ("Fox",            "Marth",         0.0, "Even matchup. Fox's speed vs Marth's range and disjoints."),
    ("Jigglypuff",     "Marth",         0.0, "Marth tipper combos hurt Puff badly. Rest punish keeps Puff in it."),
]

NOTES = [
    # (note_cm reference as (char, move), note_matchup as (c1,c2), text, author)
    # We resolve to IDs after insert
    {
        "cm": ("Fox", "Neutral Special"),
        "mu": None,
        "text": "Fox's laser comes out frame 1 — fastest projectile in the game. Short-hop laser (SHL) is the core neutral tool.",
        "author": "Westballz",
    },
    {
        "cm": ("Falco", "Back Air"),
        "mu": None,
        "text": "Falco bair has a very long active window (frames 4-19). Great for covering landings and edgeguarding.",
        "author": "aMSa",
    },
    {
        "cm": ("Marth", "Forward Smash"),
        "mu": None,
        "text": "Tipper fsmash deals 17% and sends at a kill angle. Non-tipper is significantly weaker — spacing is everything.",
        "author": "Mango",
    },
    {
        "cm": None,
        "mu": ("Fox", "Marth"),
        "text": "Fox must avoid getting grabbed by Marth. A single grab leads to Marth dancing blade combos at low % and tipper kill setups at high %.",
        "author": "Armada",
    },
    {
        "cm": None,
        "mu": ("Falco", "Fox"),
        "text": "Falco's laser forces Fox to approach from above. Fox's reflector can be baited — Falco should vary laser timing.",
        "author": "PPMD",
    },
    {
        "cm": ("Captain Falcon", "Down Air"),
        "mu": None,
        "text": "Stomp (dair) is Falcon's primary spike and combo starter. Hits on frame 9. Key to Falcon's edgeguard game.",
        "author": "Taj",
    },
]


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database at {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # Create schema
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            cur.execute(s)

    # Insert characters
    cur.executemany(
        "INSERT INTO characters(char_name,weight,gravity,fall_speed,air_speed,run_speed,tier) "
        "VALUES(?,?,?,?,?,?,?)",
        CHARACTERS,
    )

    # Insert move types (deduplicated)
    cur.executemany(
        "INSERT INTO moves(move_name,move_type) VALUES(?,?)",
        MOVE_TYPES,
    )

    # Build lookup dicts
    cur.execute("SELECT char_id, char_name FROM characters")
    char_map = {name: cid for cid, name in cur.fetchall()}

    cur.execute("SELECT move_id, move_name FROM moves")
    move_map = {name: mid for mid, name in cur.fetchall()}

    # Insert character_moves
    cm_rows = []
    for char, move, startup, active, total, damage, sstun, fadv, inp in CHARACTER_MOVES:
        cm_rows.append((
            char_map[char], move_map[move],
            startup, active, total, damage, sstun, fadv, inp,
        ))
    cur.executemany(
        "INSERT INTO character_moves"
        "(char_id,move_id,startup_frames,active_frames,total_frames,damage,shield_stun,frame_advantage,input_command)"
        " VALUES(?,?,?,?,?,?,?,?,?)",
        cm_rows,
    )

    # Build cm lookup  (char_id, move_id) -> cm_id
    cur.execute("SELECT cm_id, char_id, move_id FROM character_moves")
    cm_map = {(cid, mid): cmid for cmid, cid, mid in cur.fetchall()}

    # Insert matchups (enforce char_id_1 < char_id_2)
    mu_rows = []
    for c1, c2, score, mnotes in MATCHUPS:
        id1, id2 = char_map[c1], char_map[c2]
        if id1 > id2:
            id1, id2 = id2, id1
            score = -score
        mu_rows.append((id1, id2, score, mnotes))
    cur.executemany(
        "INSERT INTO matchups(char_id_1,char_id_2,advantage_score,matchup_notes) VALUES(?,?,?,?)",
        mu_rows,
    )

    # Build matchup lookup
    cur.execute("SELECT matchup_id, char_id_1, char_id_2 FROM matchups")
    mu_map = {(c1, c2): mid for mid, c1, c2 in cur.fetchall()}

    # Insert notes
    for n in NOTES:
        cm_id = None
        mu_id = None
        if n["cm"]:
            char, move = n["cm"]
            cm_id = cm_map[(char_map[char], move_map[move])]
        if n["mu"]:
            c1, c2 = n["mu"]
            id1, id2 = char_map[c1], char_map[c2]
            if id1 > id2:
                id1, id2 = id2, id1
            mu_id = mu_map[(id1, id2)]
        cur.execute(
            "INSERT INTO notes(note_cm_id,note_matchup_id,note_text,note_author) VALUES(?,?,?,?)",
            (cm_id, mu_id, n["text"], n["author"]),
        )

    con.commit()
    con.close()

    # Verify
    con2 = sqlite3.connect(DB_PATH)
    for tbl in ["characters","moves","character_moves","matchups","notes"]:
        cnt = con2.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl}: {cnt} rows")
    con2.close()
    print(f"\nDatabase ready at: {DB_PATH}")


if __name__ == "__main__":
    seed()
