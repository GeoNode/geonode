"""
Run history — a flat SQLite file so successive runs (baseline vs. after a
fix) can be pulled up side by side later. Nothing fancier is needed for a
single-operator internal tool.
"""
import json
import os
import sqlite3
import time

DB_PATH = os.environ.get("PERFTOOL_DB_PATH", "/data/perftool.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    label TEXT,
    scenario TEXT NOT NULL,
    params TEXT NOT NULL,
    iterations TEXT NOT NULL
)
"""


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def save_run(scenario, params, iterations, label=None):
    conn = _connect()
    with conn:
        cur = conn.execute(
            "INSERT INTO runs (created_at, label, scenario, params, iterations) VALUES (?, ?, ?, ?, ?)",
            (time.time(), label or "", scenario, json.dumps(params), json.dumps(iterations)),
        )
        return cur.lastrowid


def get_run(run_id):
    conn = _connect()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def list_runs(limit=50):
    conn = _connect()
    rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row):
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "label": row["label"],
        "scenario": row["scenario"],
        "params": json.loads(row["params"]),
        "iterations": json.loads(row["iterations"]),
    }
