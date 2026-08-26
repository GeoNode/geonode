#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################


# Geonode functionality

import cProfile
import io
import pstats
import time

from django.conf import settings
from django.db import connection
from django.shortcuts import render
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

from geonode.base.utils import configuration_session_cache
from geonode.people.utils import profile_to_runtime_lang


class RequestQueryStatsMiddleware:
    """
    Adds `X-DB-Query-Count` / `X-DB-Query-Time-Ms` response headers: exactly
    how many SQL statements this one request ran and how long they took,
    counted via connection.execute_wrapper() (works regardless of DEBUG,
    unlike connection.queries).

    Unlike pg_stat_database/pg_stat_user_tables counters (whole-database,
    picks up unrelated concurrent activity), this is scoped to precisely
    this request — nothing else can leak into it. Opt-in and off by default
    (env var EXPOSE_DB_QUERY_STATS_HEADER) since it reveals internal query
    volume to whoever can see response headers; perf_tool turns it on to
    get a noise-free companion number next to the Postgres-side ones.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "EXPOSE_DB_QUERY_STATS_HEADER", False):
            return self.get_response(request)

        queries = []

        def wrapper(execute, sql, params, many, context):
            start = time.monotonic()
            try:
                return execute(sql, params, many, context)
            finally:
                queries.append(time.monotonic() - start)

        with connection.execute_wrapper(wrapper):
            response = self.get_response(request)
        response["X-DB-Query-Count"] = str(len(queries))
        response["X-DB-Query-Time-Ms"] = str(round(sum(queries) * 1000, 2))
        return response


class RequestProfilingMiddleware:
    """
    Adds an `X-Profile-Top` response header: the N functions this request
    spent the most *self* time in (pstats "tottime" — time in that function
    alone, excluding sub-calls), straight from stdlib cProfile/pstats (one
    line per function, `|`-joined since header values can't carry
    newlines). Sorted by tottime rather than cumtime on purpose: cumtime on
    a request profile is dominated by the outer middleware/dispatch chain
    (every wrapper down to the view shows nearly the same cumulative time,
    which just retraces the call stack, not where time is actually spent).
    tottime goes straight to the leaf functions doing real work — DB
    driver calls, serialization, template rendering.

    Same opt-in pattern as RequestQueryStatsMiddleware, but
    noisier to run — cProfile instruments every function call, so this adds
    real per-request overhead. Off by default (env var
    EXPOSE_REQUEST_PROFILING); only ever turn it on for a perf-testing
    instance, never in production.
    """

    TOP_N = 15

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "EXPOSE_REQUEST_PROFILING", False):
            return self.get_response(request)

        profiler = cProfile.Profile()
        profiler.enable()
        try:
            response = self.get_response(request)
        finally:
            profiler.disable()

        buf = io.StringIO()
        pstats.Stats(profiler, stream=buf).strip_dirs().sort_stats("tottime").print_stats(self.TOP_N)
        # first 5 lines are the summary header pstats always prints
        # (call count, sort order, column titles) — the header only wants
        # the actual function rows
        lines = [ln.strip() for ln in buf.getvalue().splitlines()[5:] if ln.strip()]
        response["X-Profile-Top"] = " | ".join(lines)
        return response


class ReadOnlyMiddleware:
    """
    A Middleware disabling all content modifying requests, if read-only Configuration setting is True,
    with an exception for whitelisted url names.
    """

    FORBIDDEN_HTTP_METHODS = ["POST", "PUT", "DELETE"]

    WHITELISTED_URL_NAMES = [
        "login",
        "logout",
        "account_login",
        "account_logout",
        "ows_endpoint",
        # The  set_session_language view updates only session/cookie when read-only is enabled
        "set_language",
        # Django OAuth Toolkit token endpoint
        "token",
        "tokeninfo",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        session = request.session
        configuration_session_cache(session)

        # check if the Geonode instance is read-only
        if session.get("config").get("configuration").get("read_only"):
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser or not request.user.is_active:
                # check if the request's method is forbidden in read-only instance
                if request.method in self.FORBIDDEN_HTTP_METHODS:
                    # check if the request is not against whitelisted views (check by URL names)
                    if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                        # return HttpResponse('Error: Instance in read-only mode', status=405)
                        return render(request, "base/read_only_violation.html", status=405)


class MaintenanceMiddleware:
    """
    A Middleware redirecting all requests to maintenance info page, except:
        - admin panel login,
        - admin panel logout,
        - requests performed by superuser,
    if maintenance Configuration setting is True.
    """

    # URL's enabling superuser to login/logout to/from admin panel
    WHITELISTED_URL_NAMES = [
        "login",
        "logout",
        "index",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        session = request.session
        configuration_session_cache(session)

        # check if the Geonode instance is in maintenance mode
        if session.get("config").get("configuration").get("maintenance"):
            # allow superadmin users to do whatever they want
            if not request.user.is_superuser:
                # check if the request is not against whitelisted views (check by URL names)
                if request.resolver_match.url_name not in self.WHITELISTED_URL_NAMES:
                    return render(request, "base/maintenance.html", status=503)


SESSION_LANG_KEY = "language_override"


class ProfileLanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Get the configuration cache for the session, in order to retrieve the ready_only field
        configuration_session_cache(request.session)

        is_read_only = request.session.get("config", {}).get("configuration", {}).get("read_only", False)

        runtime_lang = None

        # In read-only mode >> try cookie first
        if is_read_only:
            runtime_lang = request.session.get(SESSION_LANG_KEY)

        if not runtime_lang:
            profile_lang = getattr(request.user, "language", None)
            runtime_lang = profile_to_runtime_lang(profile_lang)

        if runtime_lang:
            translation.activate(runtime_lang)
            request.LANGUAGE_CODE = runtime_lang

        return None
