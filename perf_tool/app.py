"""
perf_tool — a small, self-contained webapp for measuring GeoNode performance
the same trustworthy way it was done by hand during the investigation this
tool grew out of: time an HTTP action end to end, and diff Postgres's own
pg_stat_database / pg_stat_user_tables counters around it instead of guessing.

Deliberately not fancy: Flask, server-rendered HTML, SQLite for run history.
See PERF_TOOL.md for how to use it.
"""
import json
import os
import statistics
import time

from flask import Flask, jsonify, redirect, render_template, request, url_for
from fpdf import FPDF
from werkzeug.middleware.proxy_fix import ProxyFix

import db_stats
import storage
from geonode_client import GeoNodeClient, LoginError
from scenarios import SCENARIOS, lookup_resources

app = Flask(__name__)
# Trust nginx's X-Forwarded-* headers (needed when this sits behind
# nginx at a path like /performance/, not just on its own port).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.template_filter("datetime")
def _format_datetime(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

DEFAULT_BASE_URL = os.environ.get("GEONODE_BASE_URL", "http://nginx")
DEFAULT_HOST_HEADER = os.environ.get("GEONODE_HOST_HEADER", "localhost")


def _run_once(client, conn, scenario_key, params):
    scenario_fn = SCENARIOS[scenario_key]["fn"]
    client.reset_query_stats()
    before = db_stats.snapshot(conn)
    t0 = time.time()
    try:
        result = scenario_fn(client, params)
    except Exception as e:
        result = {"ok": False, "http_status": None, "detail": f"{type(e).__name__}: {e}"}
    wall_time = time.time() - t0
    after = db_stats.snapshot(conn)
    delta = db_stats.diff(before, after)
    return {
        "wall_time": round(wall_time, 3),
        "ok": result.get("ok", False),
        "http_status": result.get("http_status"),
        "detail": result.get("detail", ""),
        "db": delta,
        # request-scoped, zero-noise — see geonode.base.middleware.
        # RequestQueryStatsMiddleware. {"count": 0, "time_ms": 0} when the
        # target instance doesn't have EXPOSE_DB_QUERY_STATS_HEADER on.
        "request_db": client.query_stats(),
    }


def _aggregate(iterations):
    times = [it["wall_time"] for it in iterations]
    commits = [it["db"]["db"].get("xact_commit", 0) for it in iterations]
    # .get() with a default: runs saved before this field existed won't have it
    req_counts = [it.get("request_db", {}).get("count", 0) for it in iterations]
    req_times = [it.get("request_db", {}).get("time_ms", 0) for it in iterations]
    return {
        "count": len(iterations),
        "ok_count": sum(1 for it in iterations if it["ok"]),
        "wall_time": {
            "min": round(min(times), 3),
            "avg": round(statistics.mean(times), 3),
            "median": round(statistics.median(times), 3),
            "max": round(max(times), 3),
        },
        "xact_commit": {
            "min": min(commits),
            "avg": round(statistics.mean(commits), 1),
            "median": round(statistics.median(commits), 1),
            "max": max(commits),
        },
        "request_query_count": {
            "min": min(req_counts),
            "avg": round(statistics.mean(req_counts), 1),
            "median": round(statistics.median(req_counts), 1),
            "max": max(req_counts),
        },
        "request_query_time_ms": {
            "min": round(min(req_times), 2),
            "avg": round(statistics.mean(req_times), 2),
            "median": round(statistics.median(req_times), 2),
            "max": round(max(req_times), 2),
        },
    }


@app.route("/api/lookup/resources", methods=["POST"])
def api_lookup_resources():
    """Real resources already in the target instance, for the picker in the
    UI — so scenarios like "copy" or "view metadata" exercise something real
    instead of only ever creating fresh synthetic ones."""
    data = request.get_json(force=True)
    base_url = data.get("base_url") or DEFAULT_BASE_URL
    host_header = data.get("host_header", DEFAULT_HOST_HEADER)
    client = GeoNodeClient(base_url, host_header=host_header)
    try:
        client.login(data["username"], data["password"])
        resources = lookup_resources(client, limit=int(data.get("limit", 50)))
    except LoginError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 502
    return jsonify({"resources": resources})


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/")
def index():
    return render_template(
        "index.html",
        scenarios=SCENARIOS,
        default_base_url=DEFAULT_BASE_URL,
        default_host_header=DEFAULT_HOST_HEADER,
    )


@app.route("/run", methods=["POST"])
def run():
    scenario_key = request.form["scenario"]
    if scenario_key not in SCENARIOS:
        return f"Unknown scenario: {scenario_key}", 400

    base_url = request.form.get("base_url") or DEFAULT_BASE_URL
    host_header = request.form.get("host_header", DEFAULT_HOST_HEADER)
    username = request.form["username"]
    password = request.form["password"]
    iterations_n = max(1, min(int(request.form.get("iterations", 1)), 50))
    label = request.form.get("label", "")

    params = {}
    for key, value in request.form.items():
        if key.startswith("param_") and value != "":
            params[key[len("param_") :]] = value
    if params.get("body"):
        try:
            params["body"] = json.loads(params["body"])
        except json.JSONDecodeError as e:
            return f"Invalid JSON in body field: {e}", 400

    uploaded_file = request.files.get("file")
    tmp_upload_path = None
    if uploaded_file and uploaded_file.filename:
        tmp_upload_path = f"/tmp/perftool_upload_{int(time.time())}_{uploaded_file.filename}"
        uploaded_file.save(tmp_upload_path)
        params["uploaded_file_path"] = tmp_upload_path

    client = GeoNodeClient(base_url, host_header=host_header)
    try:
        client.login(username, password)
    except LoginError as e:
        return render_template("error.html", message=str(e)), 400

    conn = db_stats.get_connection()
    try:
        iterations = [_run_once(client, conn, scenario_key, params) for _ in range(iterations_n)]
    finally:
        conn.close()
        if tmp_upload_path and os.path.exists(tmp_upload_path):
            os.unlink(tmp_upload_path)

    saved_params = {k: v for k, v in params.items() if k != "uploaded_file_path"}
    run_id = storage.save_run(scenario_key, saved_params, iterations, label=label)
    return redirect(url_for("show_run", run_id=run_id))


def _table_totals(iterations):
    """Sum per-table deltas across every iteration of a run."""
    totals = {}
    for it in iterations:
        for table, delta in it["db"]["tables"].items():
            bucket = totals.setdefault(table, {"seq_scan": 0, "idx_scan": 0, "n_tup_ins": 0, "n_tup_upd": 0, "n_tup_del": 0})
            for key, value in delta.items():
                bucket[key] += value
    return dict(sorted(totals.items(), key=lambda kv: sum(kv[1].values()), reverse=True))


def _run_context(run_id):
    run_data = storage.get_run(run_id)
    if not run_data:
        return None
    aggregate = _aggregate(run_data["iterations"])
    last_stat_statements = None
    for it in reversed(run_data["iterations"]):
        if it["db"].get("stat_statements"):
            last_stat_statements = it["db"]["stat_statements"]
            break
    return {
        "run": run_data,
        "aggregate": aggregate,
        "table_totals": _table_totals(run_data["iterations"]),
        "stat_statements": last_stat_statements,
        "scenario_label": SCENARIOS.get(run_data["scenario"], {}).get("label", run_data["scenario"]),
    }


@app.route("/run/<int:run_id>")
def show_run(run_id):
    ctx = _run_context(run_id)
    if not ctx:
        return "Run not found", 404
    return render_template("result.html", **ctx)


def _build_report_text(ctx):
    run = ctx["run"]
    agg = ctx["aggregate"]
    lines = []
    w = lines.append
    w(f"perf_tool report — run #{run['id']}")
    w("=" * 60)
    w(f"Scenario:   {ctx['scenario_label']}")
    w(f"Label:      {run['label'] or '(none)'}")
    w(f"When:       {_format_datetime(run['created_at'])}")
    w(f"Params:     {run['params']}")
    w(f"Iterations: {len(run['iterations'])}")
    w("")
    w("HOW THESE NUMBERS ARE CALCULATED")
    w("-" * 60)
    w(
        "Wall time: measured in the tool itself, wrapped directly around the\n"
        "HTTP call(s) that make up the scenario (for an upload, this includes\n"
        "polling /api/v2/resource-service/execution-status/<id> until the\n"
        "async pipeline reports finished/failed — the clock doesn't stop at\n"
        "the initial 201 Accepted)."
    )
    w("")
    w(
        "DB statements (xact_commit delta): a snapshot of Postgres's own\n"
        "pg_stat_database.xact_commit counter is taken immediately before and\n"
        "immediately after the action, on the same connection with autocommit\n"
        "on (so each snapshot is fresh, not reused from a cached transaction\n"
        "view). The delta is the number of transactions Postgres committed\n"
        "while the action ran. This is a whole-database counter, not scoped to\n"
        "this one request — if anything else was hitting this Postgres\n"
        "instance at the same time (another user, a celery beat tick), it's\n"
        "included in the delta too. That's why this report shows min/avg/\n"
        "median/max across iterations rather than a single number: one\n"
        "iteration can be noise, several iterations are a measurement."
    )
    w("")
    w(
        f"This report shows averages only. The full per-iteration detail,\n"
        f"per-table read/write breakdown, and (if pg_stat_statements is\n"
        f"available) exact top-query text live on the web page for this run:\n"
        f"/run/{run['id']}"
    )
    w("")
    w("AVERAGE RESULTS")
    w("-" * 60)
    w(f"Average wall time:       {agg['wall_time']['avg']} s   (over {agg['count']} run(s))")
    w(f"Average xact_commit Δ:   {agg['xact_commit']['avg']}   (over {agg['count']} run(s))  [whole-database]")
    if agg["request_query_count"]["max"] > 0:
        w(
            f"Average DB queries:      {agg['request_query_count']['avg']}   "
            f"({agg['request_query_time_ms']['avg']} ms)   [this request only, no noise]"
        )
    w("")
    w(
        f"For context — min {agg['wall_time']['min']}s / median {agg['wall_time']['median']}s / "
        f"max {agg['wall_time']['max']}s wall time,"
    )
    w(
        f"min {agg['xact_commit']['min']} / median {agg['xact_commit']['median']} / "
        f"max {agg['xact_commit']['max']} xact_commit delta."
    )
    w(f"Success rate: {agg['ok_count']} / {agg['count']}")
    return "\n".join(lines) + "\n"


def _build_report_pdf(ctx):
    """Same report content as _build_report_text, laid out as a PDF.
    Monospace throughout (it's a data report, not a document) with section
    headers bolded — no need for more design than that."""
    text = _build_report_text(ctx)
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    for line in text.split("\n"):
        # core PDF fonts (Courier included) are latin-1 only — the report
        # text uses a few unicode punctuation marks (em dashes), swap them
        # for plain-ASCII equivalents rather than bundling a unicode font
        # just for this
        line = line.replace("—", "-").encode("latin-1", "replace").decode("latin-1")
        # raw SQL text from pg_stat_statements can run to hundreds of chars
        # (wide column lists) — full text belongs in the DB, not a page-per-
        # query PDF, so cap what's shown here
        if len(line) > 220:
            line = line[:220] + " ..."
        is_rule = set(line) <= {"=", "-"} and len(line) > 10
        is_header = line.isupper() and line.strip() and not is_rule
        if is_rule:
            continue
        pdf.set_font("Courier", "B" if is_header else "", 14 if line.startswith("perf_tool report") else 9)
        pdf.multi_cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


@app.route("/run/<int:run_id>/report")
def download_report(run_id):
    ctx = _run_context(run_id)
    if not ctx:
        return "Run not found", 404
    pdf_bytes = _build_report_pdf(ctx)
    return app.response_class(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=perftool_run_{run_id}_report.pdf"},
    )


@app.route("/history")
def history():
    runs = storage.list_runs()
    for r in runs:
        r["aggregate"] = _aggregate(r["iterations"])
        r["scenario_label"] = SCENARIOS.get(r["scenario"], {}).get("label", r["scenario"])
    return render_template("history.html", runs=runs)


@app.route("/compare")
def compare():
    a_id = request.args.get("a", type=int)
    b_id = request.args.get("b", type=int)
    if not a_id or not b_id:
        return redirect(url_for("history"))
    run_a = storage.get_run(a_id)
    run_b = storage.get_run(b_id)
    if not run_a or not run_b:
        return "Run not found", 404
    agg_a = _aggregate(run_a["iterations"])
    agg_b = _aggregate(run_b["iterations"])
    return render_template(
        "compare.html",
        run_a=run_a,
        run_b=run_b,
        agg_a=agg_a,
        agg_b=agg_b,
        totals_a=_table_totals(run_a["iterations"]),
        totals_b=_table_totals(run_b["iterations"]),
        scenario_label_a=SCENARIOS.get(run_a["scenario"], {}).get("label", run_a["scenario"]),
        scenario_label_b=SCENARIOS.get(run_b["scenario"], {}).get("label", run_b["scenario"]),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
