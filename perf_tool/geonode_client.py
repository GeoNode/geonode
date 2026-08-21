"""
Thin HTTP client for a running GeoNode instance — same login/CSRF dance and
execution-status polling done by hand (curl) throughout the manual
investigation, wrapped so scenarios.py can call it directly.

Network quirks this works around (all discovered by the tool failing loudly
against this instance, not guessed):

1. nginx's plain-HTTP vhost only matches `server_name localhost 127.0.0.1` —
   a bare service-name Host header (e.g. "nginx") hits its default_server
   catch-all and gets the connection dropped. So requests here always send
   an explicit `Host: localhost` header, independent of which hostname the
   URL itself uses to resolve nginx on the docker network.
2. GeoNode marks its session/csrf cookies Secure (correct for production,
   where nginx terminates TLS). This tool talks over plain HTTP inside the
   compose network, so requests correctly refuses to send Secure cookies
   back — every GET looked fine (anonymous read is allowed) while anything
   requiring auth (uploads, creates) silently failed with 401. Fixed by
   stripping the Secure flag right after the cookie is set; the traffic
   never leaves the docker network either way.
3. Some endpoints (e.g. PUT /api/v2/resources/<pk>/copy) 302-redirect to an
   i18n-prefixed URL (/en-us/...). `requests` follows redirects by default
   but downgrades the method in the process, turning a PUT into a GET and
   landing on "Method GET not allowed". Real semantics don't change here —
   it's a cosmetic locale-prefix redirect — so this client follows exactly
   one redirect itself, preserving the original method and body, instead of
   letting requests silently reinterpret the request.
"""
import re
import time
from urllib.parse import urljoin

import requests

CSRF_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')
REDIRECT_CODES = (301, 302, 307, 308)


class LoginError(RuntimeError):
    pass


class GeoNodeClient:
    def __init__(self, base_url, timeout=30, host_header="localhost"):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.host_header = host_header
        self.session = requests.Session()
        self._query_count = 0
        self._query_time_ms = 0.0

    def _headers(self, extra=None):
        headers = {"Referer": f"{self.base_url}/"}
        if self.host_header:
            headers["Host"] = self.host_header
        token = self.session.cookies.get("csrftoken")
        if token:
            headers["X-CSRFToken"] = token
        if extra:
            headers.update(extra)
        return headers

    def _unsecure_cookies(self):
        for cookie in self.session.cookies:
            cookie.secure = False

    def reset_query_stats(self):
        """Call before a scenario so query_stats() below reflects only the
        requests made since, not everything this client has ever sent (it's
        reused across iterations)."""
        self._query_count = 0
        self._query_time_ms = 0.0

    def query_stats(self):
        """Sum of X-DB-Query-Count / X-DB-Query-Time-Ms across every request
        made since the last reset_query_stats() — the request-scoped,
        zero-noise companion to the Postgres-side pg_stat_* numbers. Only
        populated if the target GeoNode has
        EXPOSE_DB_QUERY_STATS_HEADER=True (see geonode.base.middleware.
        RequestQueryStatsMiddleware); stays at 0 otherwise."""
        return {"count": self._query_count, "time_ms": round(self._query_time_ms, 2)}

    def _record_query_stats(self, response):
        count = response.headers.get("X-DB-Query-Count")
        time_ms = response.headers.get("X-DB-Query-Time-Ms")
        if count is not None:
            self._query_count += int(count)
        if time_ms is not None:
            self._query_time_ms += float(time_ms)

    def _request(self, method, url, **kwargs):
        """One HTTP call, following at most one redirect with the method and
        body intact (see quirk #3 above) instead of trusting requests'
        default redirect handling."""
        r = self.session.request(method, url, allow_redirects=False, timeout=self.timeout, **kwargs)
        self._record_query_stats(r)
        if r.status_code in REDIRECT_CODES and "Location" in r.headers:
            next_url = urljoin(url, r.headers["Location"])
            r = self.session.request(method, next_url, allow_redirects=False, timeout=self.timeout, **kwargs)
            self._record_query_stats(r)
        return r

    def login(self, username, password):
        r = self._request("GET", f"{self.base_url}/account/login/", headers=self._headers())
        r.raise_for_status()
        # the GET above already set a Secure csrftoken cookie — strip it now,
        # before the POST, or the CSRF cookie never makes it back over plain
        # HTTP and Django 403s the login with "requires a CSRF cookie"
        self._unsecure_cookies()
        m = CSRF_RE.search(r.text)
        if not m:
            raise LoginError("Could not find a CSRF token on the login page — is base_url correct?")
        csrf = m.group(1)
        # Deliberately not following the redirect further than _request
        # already does: with a spoofed Host header, Django's post-login
        # redirect is an absolute URL built from that header — chasing it
        # would try to connect to "localhost" itself instead of nginx. A 302
        # here is all "login succeeded" needs; matches the plain-curl
        # approach used by hand throughout the investigation this tool is
        # based on.
        r = self.session.post(
            f"{self.base_url}/account/login/",
            data={"login": username, "password": password, "csrfmiddlewaretoken": csrf},
            headers=self._headers(),
            timeout=self.timeout,
            allow_redirects=False,
        )
        self._unsecure_cookies()
        if r.status_code != 302 or "sessionid" not in self.session.cookies.get_dict():
            raise LoginError(f"Login failed for user '{username}' (status {r.status_code}) — check credentials")

    def get(self, path, **kwargs):
        return self._request("GET", f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    def post_json(self, path, payload):
        headers = self._headers({"Content-Type": "application/json"})
        return self._request("POST", f"{self.base_url}{path}", json=payload, headers=headers)

    def patch_json(self, path, payload):
        headers = self._headers({"Content-Type": "application/json"})
        return self._request("PATCH", f"{self.base_url}{path}", json=payload, headers=headers)

    def put_json(self, path, payload):
        headers = self._headers({"Content-Type": "application/json"})
        return self._request("PUT", f"{self.base_url}{path}", json=payload, headers=headers)

    def upload_file(self, path, file_path, field_name="base_file"):
        with open(file_path, "rb") as fh:
            return self._request(
                "POST",
                f"{self.base_url}{path}",
                files={field_name: fh},
                headers=self._headers(),
            )

    def poll_execution(self, execution_id, timeout=180, interval=2):
        """Poll /api/v2/resource-service/execution-status/<id> until terminal."""
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            r = self.get(f"/api/v2/resource-service/execution-status/{execution_id}")
            r.raise_for_status()
            last = r.json()
            if last.get("status") in ("finished", "failed"):
                return last
            time.sleep(interval)
        raise TimeoutError(f"execution {execution_id} did not finish within {timeout}s (last status: {last})")
