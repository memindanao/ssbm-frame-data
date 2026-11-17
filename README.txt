
COMP 3005 Winter 2026 — Term Project
Student/Student No: Evan Mindanao, 101392044
Project: Super Smash Bros. Melee Frame Data Database


── DATABASE FILE LOCATION ──────────────────────────────────────
  ssbm_app/ssbm_framedata.db

  You can open this directly with the sqlite3 command-line tool:
    sqlite3 ssbm_app/ssbm_framedata.db

  Example manual queries:
    .tables
    SELECT char_name, tier FROM characters ORDER BY tier;
    SELECT c.char_name, m.move_name, cm.startup_frames, cm.frame_advantage
      FROM character_moves cm
      JOIN characters c ON cm.char_id = c.char_id
      JOIN moves      m ON cm.move_id = m.move_id
      WHERE cm.startup_frames <= 4
      ORDER BY cm.startup_frames;

── PROJECT STRUCTURE ────────────────────────────────────────────
  ssbm_app/
  ├── app.py              Flask backend (all SQL queries here)
  ├── seed_db.py          Creates + seeds the SQLite3 database
  ├── ssbm_framedata.db   The actual SQLite3 database file
  ├── templates/
  │   └── index.html      HTML/JS frontend
  └── readme.txt          This file

── HOW TO RUN ───────────────────────────────────────────────────
  Requirements: Python 3.9+, Flask

  1. Install Flask (if not already installed):
       pip install flask

  2. (Optional) Re-seed the database:
       cd ssbm_app
       python seed_db.py

  3. Start the web server:
       cd ssbm_app
       python app.py

  4. Open your browser at:
       http://localhost:5000

── FEATURES / USE-CASES DEMONSTRATED ───────────────────────────
  R1  Characters tab — select any character to view all frame data
      (N:N join: characters ↔ moves via character_moves)

  R2  Move Comparison tab — compare a move (e.g. Forward Smash)
      across all characters, sorted by startup frames

  R3  Frame Filter tab — filter by startup frames, damage,
      move type, safe-on-shield; click any row for secondary notes

  R4  Matchups tab — view all matchup advantage scores;
      filter by character (self-referencing N:N)

  R5  Frame Filter tab — find fastest or highest-damage moves

  R6  Click any move or matchup row → modal with community notes
      and ability to post new annotations (INSERT via API)

  R3.5  N:N demonstrated in Matchups tab (CHARACTERS ↔ CHARACTERS)
  R3.6  Secondary query: move list → click → load notes for that move
                         matchup list → click → load notes for matchup

── SQL LOCATION ─────────────────────────────────────────────────
  All SQL queries are in app.py using raw sqlite3 (no ORM).
  The database schema and seed SQL are in seed_db.py.

── YOUTUBE VIDEO LINK ───────────────────────────────────────────

https://youtu.be/LmItYwHhOuA

