"""
Postgres-side measurement: the same approach used manually throughout the
GeoNode performance investigation this tool grew out of — snapshot
pg_stat_database / pg_stat_user_tables before and after an action, diff them.

No superuser, no ALTER SYSTEM, no docker log scraping required — this works
against the DB role GeoNode itself uses. If pg_stat_statements happens to be
installed and readable, we use it too for an exact per-query breakdown;
otherwise we fall back to the table-level counters alone and say so.
"""
import os

import psycopg2
import psycopg2.extras

# Tables worth watching, based on what actually moved during the manual
# investigation (upload pipeline, map/geoapp creation, permission writes).
# Add to this list if you're chasing something not covered here.
TRACKED_TABLES = [
    "base_resourcebase",
    "base_contactrole",
    "base_link",
    "base_hierarchicalkeyword",
    "resource_executionrequest",
    "layers_dataset",
    "layers_attribute",
    "maps_map",
    "maps_maplayer",
    "geoapps_geoapp",
    "documents_document",
    "guardian_userobjectpermission",
    "guardian_groupobjectpermission",
    "auth_permission",
    "people_profile",
    "harvesting_harvester",
]


def get_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "db"),
        port=os.environ.get("DATABASE_PORT", "5432"),
        dbname=os.environ.get("GEONODE_DATABASE", "geonode"),
        user=os.environ.get("GEONODE_DATABASE_USER", "geonode"),
        password=os.environ.get("GEONODE_DATABASE_PASSWORD", ""),
        connect_timeout=5,
    )
    # pg_stat_* views are cached for the lifetime of a transaction (PG15's
    # stats_fetch_consistency defaults to "cache") — without autocommit, a
    # before/after snapshot pair taken on the same connection would silently
    # read the *same* cached view twice and always diff to zero.
    conn.autocommit = True
    return conn


def pg_stat_statements_available(conn):
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'")
            if cur.fetchone() is None:
                return False
            cur.execute("SELECT 1 FROM pg_stat_statements LIMIT 1")
            return True
        except Exception:
            conn.rollback()
            return False


def snapshot(conn):
    """One point-in-time read of the counters we diff around an action."""
    dbname = os.environ.get("GEONODE_DATABASE", "geonode")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT xact_commit, xact_rollback, tup_returned, tup_fetched, "
            "tup_inserted, tup_updated, tup_deleted "
            "FROM pg_stat_database WHERE datname = %s",
            (dbname,),
        )
        db_row = dict(cur.fetchone() or {})

        cur.execute(
            "SELECT relname, seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del "
            "FROM pg_stat_user_tables WHERE relname = ANY(%s)",
            (TRACKED_TABLES,),
        )
        tables = {row["relname"]: dict(row) for row in cur.fetchall()}

    stat_statements = None
    if pg_stat_statements_available(conn):
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # queries touching this database only, skip the tool's own bookkeeping
            cur.execute(
                "SELECT queryid, query, calls, total_exec_time "
                "FROM pg_stat_statements pss "
                "JOIN pg_database d ON d.oid = pss.dbid "
                "WHERE d.datname = %s AND query NOT ILIKE '%%pg_stat_statements%%'",
                (dbname,),
            )
            stat_statements = {row["queryid"]: dict(row) for row in cur.fetchall()}

    return {"db": db_row, "tables": tables, "stat_statements": stat_statements}


def _diff_dict(before, after, keys):
    return {k: (after.get(k) or 0) - (before.get(k) or 0) for k in keys}


def diff(before, after):
    """Delta between two snapshot() results."""
    db_keys = [
        "xact_commit",
        "xact_rollback",
        "tup_returned",
        "tup_fetched",
        "tup_inserted",
        "tup_updated",
        "tup_deleted",
    ]
    result = {
        "db": _diff_dict(before["db"], after["db"], db_keys),
        "tables": {},
        "stat_statements": None,
    }

    table_keys = ["seq_scan", "idx_scan", "n_tup_ins", "n_tup_upd", "n_tup_del"]
    for table in TRACKED_TABLES:
        b = before["tables"].get(table, {})
        a = after["tables"].get(table, {})
        if not b and not a:
            continue
        delta = _diff_dict(b, a, table_keys)
        if any(delta.values()):
            result["tables"][table] = delta

    if before.get("stat_statements") is not None and after.get("stat_statements") is not None:
        rows = []
        for queryid, a_row in after["stat_statements"].items():
            b_row = before["stat_statements"].get(queryid)
            calls_before = b_row["calls"] if b_row else 0
            calls_delta = a_row["calls"] - calls_before
            if calls_delta > 0:
                time_before = b_row["total_exec_time"] if b_row else 0
                rows.append(
                    {
                        "query": a_row["query"],
                        "calls": calls_delta,
                        "total_time_ms": round(a_row["total_exec_time"] - time_before, 2),
                    }
                )
        rows.sort(key=lambda r: r["calls"], reverse=True)
        result["stat_statements"] = rows[:30]  # top offenders, not a full dump

    return result
