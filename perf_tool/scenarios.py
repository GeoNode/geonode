"""
Built-in test scenarios — the same actions performed by hand with curl during
the manual investigation (list resources, upload a dataset, create a map,
create a geoapp). Each scenario is a plain function:

    scenario(client, params) -> dict(ok=bool, http_status=int, detail=str)

Timing and DB measurement happen in app.py around the call, not in here —
this module only knows how to talk to GeoNode.
"""
import os
import tempfile
import time

SAMPLE_CSV_TEMPLATE = "name,latitude,longitude,value1,value2,value3\n"


def _make_sample_csv(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w") as fh:
        fh.write(SAMPLE_CSV_TEMPLATE)
        for i in range(rows):
            fh.write(f"point{i},{45 + (i % 100) / 100},{9 + (i % 100) / 100},{i},{i * 2},{i * 3}\n")
    return path


def list_resources(client, params):
    page_size = int(params.get("page_size", 20))
    r = client.get(f"/api/v2/resources?page_size={page_size}")
    return {
        "ok": r.status_code == 200,
        "http_status": r.status_code,
        "detail": f"{len(r.json().get('resources', []))} resources returned" if r.status_code == 200 else r.text[:300],
    }


def list_maps(client, params):
    page_size = int(params.get("page_size", 20))
    r = client.get(f"/api/v2/maps?page_size={page_size}")
    return {
        "ok": r.status_code == 200,
        "http_status": r.status_code,
        "detail": f"{len(r.json().get('maps', []))} maps returned" if r.status_code == 200 else r.text[:300],
    }


def upload_csv(client, params):
    rows = int(params.get("rows", 5))
    uploaded_path = params.get("uploaded_file_path")
    tmp_path = None
    try:
        file_path = uploaded_path or _make_sample_csv(rows)
        if not uploaded_path:
            tmp_path = file_path
        r = client.upload_file("/uploads/upload", file_path)
        if r.status_code != 201:
            return {"ok": False, "http_status": r.status_code, "detail": r.text[:500]}
        execution_id = r.json().get("execution_id")
        result = client.poll_execution(execution_id, timeout=int(params.get("timeout", 180)))
        ok = result.get("status") == "finished"
        return {
            "ok": ok,
            "http_status": r.status_code,
            "detail": f"execution {execution_id}: {result.get('status')} — {result.get('output_params')}",
        }
    finally:
        if tmp_path:
            os.unlink(tmp_path)


def create_map(client, params):
    title = params.get("title") or f"perftool_map_{int(time.time())}"
    r = client.post_json("/api/v2/maps", {"title": title, "abstract": "created by perf_tool"})
    ok = r.status_code in (200, 201)
    return {
        "ok": ok,
        "http_status": r.status_code,
        "detail": f"map created: {r.json().get('map', {}).get('pk')}" if ok else r.text[:300],
    }


def lookup_geoapp_types(client, limit=100):
    """GeoNode doesn't expose a fixed list of valid GeoApp resource_type
    values anywhere (it's a free-text field on ResourceBase, not a choices
    field) — the closest thing to "what types exist" is what's already been
    created. Same approach as geonode.security.utils.get_geoapp_subtypes(),
    just via the API instead of a DB query."""
    r = client.get(f"/api/v2/geoapps?page_size={limit}")
    r.raise_for_status()
    types = {g.get("resource_type") for g in r.json().get("geoapps", []) if g.get("resource_type")}
    return sorted(types)


def create_geoapp(client, params):
    name = params.get("name") or f"perftool_geoapp_{int(time.time())}"
    requested_type = params.get("resource_type")

    if requested_type:
        types_to_try = [requested_type]
    else:
        # not told which type to use — don't assume one, try every type
        # already present on this instance instead
        types_to_try = lookup_geoapp_types(client)
        if not types_to_try:
            return {
                "ok": False,
                "http_status": None,
                "detail": (
                    "No resource_type given and none could be discovered (no GeoApps exist yet "
                    "on this instance to infer a type from). Set the 'resource_type' field explicitly."
                ),
            }

    results = []
    all_ok = True
    for resource_type in types_to_try:
        type_name = f"{name}_{resource_type}" if len(types_to_try) > 1 else name
        r = client.post_json(
            "/api/v2/geoapps",
            {"name": type_name, "title": type_name, "resource_type": resource_type},
        )
        ok = r.status_code in (200, 201)
        all_ok = all_ok and ok
        pk = r.json().get("geoapp", {}).get("pk") if ok else None
        results.append(f"{resource_type}: {'created #' + str(pk) if ok else f'HTTP {r.status_code}'}")

    return {
        "ok": all_ok,
        "http_status": None if len(types_to_try) > 1 else r.status_code,
        "detail": "; ".join(results),
    }


def lookup_resources(client, limit=50):
    """Real resources already in the instance, for the picker in the UI —
    not a scenario itself, called directly by app.py's /api/lookup route."""
    r = client.get(f"/api/v2/resources?page_size={limit}")
    r.raise_for_status()
    return [
        {"pk": res["pk"], "title": res["title"], "resource_type": res.get("resource_type")}
        for res in r.json().get("resources", [])
    ]


def resource_detail(client, params):
    pk = params.get("pk")
    if not pk:
        return {"ok": False, "http_status": None, "detail": "No resource selected — load and pick one first"}
    r = client.get(f"/api/v2/resources/{pk}")
    return {
        "ok": r.status_code == 200,
        "http_status": r.status_code,
        "detail": f"fetched resource {pk}" if r.status_code == 200 else r.text[:300],
    }


def copy_resource(client, params):
    pk = params.get("pk")
    if not pk:
        return {"ok": False, "http_status": None, "detail": "No resource selected — load and pick one first"}
    r = client.put_json(f"/api/v2/resources/{pk}/copy", {})
    ok = r.status_code in (200, 201)
    return {
        "ok": ok,
        "http_status": r.status_code,
        "detail": (f"copied resource {pk}: {r.text[:200]}") if ok else r.text[:300],
    }


def update_resource_metadata(client, params):
    pk = params.get("pk")
    if not pk:
        return {"ok": False, "http_status": None, "detail": "No resource selected — load and pick one first"}
    abstract = params.get("abstract") or f"perf_tool metadata edit {time.time()}"
    r = client.patch_json(f"/api/v2/resources/{pk}", {"abstract": abstract})
    return {
        "ok": r.status_code == 200,
        "http_status": r.status_code,
        "detail": f"updated resource {pk}" if r.status_code == 200 else r.text[:300],
    }


def custom_request(client, params):
    """Escape hatch for anything not covered by the built-ins above."""
    method = params.get("method", "GET").upper()
    path = params["path"]
    body = params.get("body")
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post_json(path, body or {})
    elif method == "PATCH":
        r = client.patch_json(path, body or {})
    elif method == "PUT":
        r = client.put_json(path, body or {})
    else:
        raise ValueError(f"Unsupported method: {method}")
    return {
        "ok": r.status_code < 400,
        "http_status": r.status_code,
        "detail": r.text[:500],
    }


SCENARIOS = {
    "list_resources": {
        "label": "List resources (GET /api/v2/resources)",
        "fn": list_resources,
        "fields": [("page_size", "Page size", "20")],
    },
    "list_maps": {
        "label": "List maps (GET /api/v2/maps)",
        "fn": list_maps,
        "fields": [("page_size", "Page size", "20")],
    },
    "upload_csv": {
        "label": "Upload a CSV dataset (full pipeline)",
        "fn": upload_csv,
        "fields": [("rows", "Rows in generated CSV (ignored if a file is uploaded below)", "5")],
        "accepts_file": True,
    },
    "create_map": {
        "label": "Create an empty map",
        "fn": create_map,
        "fields": [("title", "Title (optional)", "")],
    },
    "create_geoapp": {
        "label": "Create a GeoApp",
        "fn": create_geoapp,
        "fields": [
            ("name", "Name (optional)", ""),
            ("resource_type", "resource_type — e.g. geostory, dashboard (blank = try every type already on this instance)", ""),
        ],
    },
    "resource_detail": {
        "label": "View an existing resource (GET /api/v2/resources/<pk>)",
        "fn": resource_detail,
        "fields": [],
        "needs_resource_picker": True,
    },
    "copy_resource": {
        "label": "Copy an existing resource (PUT /api/v2/resources/<pk>/copy)",
        "fn": copy_resource,
        "fields": [],
        "needs_resource_picker": True,
    },
    "update_resource_metadata": {
        "label": "Edit an existing resource's metadata (PATCH /api/v2/resources/<pk>)",
        "fn": update_resource_metadata,
        "fields": [("abstract", "New abstract (optional)", "")],
        "needs_resource_picker": True,
    },
    "custom_request": {
        "label": "Custom request (advanced)",
        "fn": custom_request,
        "fields": [
            ("method", "Method (GET/POST/PATCH)", "GET"),
            ("path", "Path, e.g. /api/v2/resources/123", ""),
            ("body", "JSON body (POST/PATCH only)", ""),
        ],
    },
}
