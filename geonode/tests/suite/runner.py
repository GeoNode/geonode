from contextlib import contextmanager
import faulthandler
import io
import os
import sys
import time
import logging
import multiprocessing

from multiprocessing import Process, Queue, Event
from queue import Empty
from typing import Collection

from django.conf import settings

from django.test.runner import DiscoverRunner
from django.db import connections, DEFAULT_DB_ALIAS
from django.core.exceptions import ImproperlyConfigured


# "auto" - one worker per Django application
# "cpu" - one worker per process core
WORKER_MAX = getattr(settings, "TEST_RUNNER_WORKER_MAX", 3)
WORKER_COUNT = getattr(settings, "TEST_RUNNER_WORKER_COUNT", "auto")
NOT_THREAD_SAFE = getattr(settings, "TEST_RUNNER_NOT_THREAD_SAFE", None)
PARENT_TIMEOUT = getattr(settings, "TEST_RUNNER_PARENT_TIMEOUT", 10)
WORKER_TIMEOUT = getattr(settings, "TEST_RUNNER_WORKER_TIMEOUT", 10)

# amqplib spits out a lot of log messages which just add a lot of noise.
logger = logging.getLogger(__name__)

null_file = open("/dev/null", "w")


class GeoNodeBaseSuiteDiscoverRunner(DiscoverRunner):
    def __init__(
        self,
        pattern=None,
        top_level=None,
        verbosity=1,
        interactive=True,
        failfast=True,
        keepdb=False,
        reverse=False,
        debug_mode=False,
        debug_sql=False,
        parallel=0,
        tags=None,
        exclude_tags=None,
        test_name_patterns=None,
        pdb=False,
        buffer=False,
        enable_faulthandler=True,
        timing=False,
        **kwargs,
    ):
        self.pattern = pattern
        self.top_level = top_level
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.keepdb = keepdb
        self.reverse = reverse
        self.debug_mode = debug_mode
        self.debug_sql = debug_sql
        self.parallel = parallel
        self.tags = set(tags or [])
        self.exclude_tags = set(exclude_tags or [])
        if not faulthandler.is_enabled() and enable_faulthandler:
            try:
                faulthandler.enable(file=sys.stderr.fileno())
            except (AttributeError, io.UnsupportedOperation):
                faulthandler.enable(file=sys.__stderr__.fileno())
        self.pdb = pdb
        if self.pdb and self.parallel > 1:
            raise ValueError("You cannot use --pdb with parallel tests; pass --parallel=1 to use it.")
        self.buffer = buffer
        if self.buffer and self.parallel > 1:
            raise ValueError("You cannot use -b/--buffer with parallel tests; pass " "--parallel=1 to use it.")
        self.test_name_patterns = None
        self.time_keeper = TimeKeeper() if timing else NullTimeKeeper()
        if test_name_patterns:
            # unittest does not export the _convert_select_pattern function
            # that converts command-line arguments to patterns.
            self.test_name_patterns = {pattern if "*" in pattern else f"*{pattern}*" for pattern in test_name_patterns}


class BufferWritesDevice:
    def __init__(self):
        self._data = []

    def write(self, string):
        self._data.append(string)

    def read(self):
        return "".join(self._data)

    def flush(self, *args, **kwargs):
        pass

    def isatty(self):
        return False


# Redirect stdout to /dev/null because we don't want to see all the repeated
# "database creation" logging statements from all the workers.
# All the test output is printed to stderr to this is not problematic.
sys.stdout = null_file


class ParallelTestSuiteRunner:
    def __init__(
        self,
        pattern=None,
        top_level=None,
        verbosity=1,
        interactive=True,
        failfast=True,
        keepdb=False,
        reverse=False,
        debug_mode=False,
        debug_sql=False,
        parallel=0,
        tags=None,
        exclude_tags=None,
        **kwargs,
    ):
        self.pattern = pattern
        self.top_level = top_level
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.keepdb = keepdb
        self.reverse = reverse
        self.debug_mode = debug_mode
        self.debug_sql = debug_sql
        self.parallel = parallel
        self.tags = set(tags or [])
        self.exclude_tags = set(exclude_tags or [])
        self._keyboard_interrupt_intercepted = False

        self._worker_max = kwargs.get("worker_max", WORKER_MAX)
        self._worker_count = kwargs.get("worker_count", WORKER_COUNT)
        self._not_thread_safe = kwargs.get("not_thread_safe", NOT_THREAD_SAFE) or []
        self._parent_timeout = kwargs.get("parent_timeout", PARENT_TIMEOUT)
        self._worker_timeout = kwargs.get("worker_timeout", WORKER_TIMEOUT)
        self._database_names = self._get_database_names()

    def _get_database_names(self):
        database_names = {}
        for alias in connections:
            connection = connections[alias]
            database_name = connection.settings_dict["NAME"]
            database_names[alias] = database_name
        return database_names

    def run_tests(self, test_labels, **kwargs):
        return self._run_tests(tests=test_labels)

    def _run_tests(self, tests, **kwargs):
        # tests = dict where the key is a test group name and the value are
        # the tests to run
        tests_queue = Queue()
        results_queue = Queue()
        stop_event = Event()

        pending_tests = {}
        pending_not_thread_safe_tests = {}
        completed_tests = {}
        failures = 0
        errors = 0

        start_time = time.time()
        # First tun tests which are not thread safe in the main process
        for group in self._not_thread_safe:
            if group not in tests.keys():
                continue

            group_tests = tests[group]
            del tests[group]

            logger.debug(f"Running tests in a main process: {group_tests}")
            pending_not_thread_safe_tests[group] = group_tests
            result = self._tests_func(tests=group_tests, worker_index=None)
            results_queue.put((group, result), block=False)

        for group, tests in tests.items():
            tests_queue.put((group, tests), block=False)
            pending_tests[group] = tests

        worker_count = self._worker_count
        if worker_count == "auto":
            worker_count = len(pending_tests)
        elif worker_count == "cpu":
            worker_count = multiprocessing.cpu_count()

        if worker_count > len(pending_tests):
            # No need to spawn more workers then there are tests.
            worker_count = len(pending_tests)

        worker_max = self._worker_max
        if worker_max == "auto":
            worker_max = len(pending_tests)
        elif worker_max == "cpu":
            worker_max = multiprocessing.cpu_count()

        if worker_count > worker_max:
            # No need to spawn more workers then there are tests.
            worker_count = worker_max

        worker_args = (tests_queue, results_queue, stop_event)
        logger.debug(f"Number of workers {worker_count} ")
        workers = self._create_worker_pool(
            pool_size=worker_count, target_func=self._run_tests_worker, worker_args=worker_args
        )

        for index, worker in enumerate(workers):
            logger.debug(f"Staring worker {index}")
            worker.start()

        if workers:
            while pending_tests:
                try:
                    try:
                        group, result = results_queue.get(timeout=self._parent_timeout, block=True)
                    except Exception:
                        raise Empty

                    try:
                        if group not in pending_not_thread_safe_tests:
                            pending_tests.pop(group)
                        else:
                            pending_not_thread_safe_tests.pop(group)
                    except KeyError:
                        logger.debug(f"Got a result for unknown group: {group}")
                    else:
                        completed_tests[group] = result
                        self._print_result(result)

                        if result.failures or result.errors:
                            failures += len(result.failures)
                            errors += len(result.errors)

                            if self.failfast:
                                # failfast is enabled, kill all the active workers
                                # and stop
                                for worker in workers:
                                    if worker.is_alive():
                                        worker.terminate()
                                break
                except Empty:
                    worker_left = False

                    for worker in workers:
                        if worker.is_alive():
                            worker_left = True
                            break

                    if not worker_left:
                        break

        # We are done, signalize all the workers to stop
        stop_event.set()

        end_time = time.time()
        self._exit(start_time, end_time, failures, errors)

    def _run_tests_worker(self, index, tests_queue, results_queue, stop_event):
        def pop_item():
            group, tests = tests_queue.get(timeout=self._worker_timeout)
            return group, tests

        try:
            try:
                for group, tests in iter(pop_item, None):
                    if stop_event.is_set():
                        # We should stop
                        break
                    try:
                        logger.debug(f"Worker {index} is running tests {tests}")
                        result = self._tests_func(tests=tests, worker_index=index)
                        results_queue.put((group, result))
                        logger.debug(f"Worker {index} has finished running tests {tests}")
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except Exception as e:
                        logger.debug(f"Running tests failed, reason: {e}")
                        result = TestResult().from_exception(e)
                        results_queue.put((group, result))
            except Empty:
                logger.debug(f"Worker {index} timed out while waiting for tests to run")
        finally:
            tests_queue.close()
            results_queue.close()
        logger.debug(f"Worker {index} is stopping")

    def _pre_tests_func(self):
        # This method gets called before _tests_func is called
        pass

    def _post_tests_func(self):
        # This method gets called after _tests_func has completed and _print_result
        # function is called
        pass

    def _tests_func(self, worker_index):
        raise Exception("_tests_func not implements")

    def _print_result(self, result):
        print(result.output, file=sys.stderr)

    def _exit(self, start_time, end_time, failure_count, error_count):
        time_difference = end_time - start_time

        print(f"Total run time: {time_difference} seconds", file=sys.stderr)
        try:
            sys.exit(failure_count + error_count)
        except Exception:
            pass

    def _group_by_app(self, test_labels):
        """
        Groups tests by an app. This helps to partition tests so they can be run
        in separate worker processes.

        @TODO: Better partitioning of tests based on the previous runs - measure
        test suite run time and partition tests so we can spawn as much workers as
        it makes sense to get the maximum performance benefits.
        """
        tests = {}

        for test_label in test_labels:
            if not test_label.find("."):
                app = test_label
            else:
                app = test_label.split(".")[0] + test_label.split(".")[1]

            if not tests.get(app):
                tests[app] = [test_label]
            else:
                tests[app].append(test_label)

        return tests

    def _group_by_file(self, test_names):
        tests = {}

        for test_name in test_names:
            tests[test_name] = test_name

        return tests

    def _create_worker_pool(self, pool_size, target_func, worker_args):
        workers = []
        for index in range(0, pool_size):
            args = (index,) + worker_args
            worker = Process(target=target_func, args=args)
            workers.append(worker)
        return workers

    def log(self, string):
        if self.verbosity >= 3:
            print(string)


class DjangoParallelTestSuiteRunner(ParallelTestSuiteRunner, DiscoverRunner):
    def __init__(
        self,
        pattern=None,
        top_level=None,
        verbosity=1,
        interactive=True,
        failfast=True,
        keepdb=False,
        reverse=False,
        debug_mode=False,
        debug_sql=False,
        parallel=0,
        tags=None,
        exclude_tags=None,
        **kwargs,
    ):
        self.pattern = pattern
        self.top_level = top_level
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.keepdb = keepdb
        self.reverse = reverse
        self.debug_mode = debug_mode
        self.debug_sql = debug_sql
        self.parallel = parallel
        self.tags = set(tags or [])
        self.exclude_tags = set(exclude_tags or [])
        self._keyboard_interrupt_intercepted = False
        self._worker_max = kwargs.get("worker_max", WORKER_MAX)
        self._worker_count = kwargs.get("worker_count", WORKER_COUNT)
        self._not_thread_safe = kwargs.get("not_thread_safe", NOT_THREAD_SAFE) or []
        self._parent_timeout = kwargs.get("parent_timeout", PARENT_TIMEOUT)
        self._worker_timeout = kwargs.get("worker_timeout", WORKER_TIMEOUT)
        self._database_names = self._get_database_names()

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        app_tests = self._group_by_app(test_labels)
        return self._run_tests(tests=app_tests)

    def run_suite(self, suite, **kwargs):
        return DjangoParallelTestRunner(verbosity=self.verbosity, failfast=self.failfast).run_suite(suite)

    def setup_databases(self, **kwargs):
        return self.setup_databases_18(**kwargs)

    def dependency_ordered(self, test_databases, dependencies):
        """
        Reorder test_databases into an order that honors the dependencies
        described in TEST[DEPENDENCIES].
        """
        ordered_test_databases = []
        resolved_databases = set()

        # Maps db signature to dependencies of all its aliases
        dependencies_map = {}

        # Check that no database depends on its own alias
        for sig, (_, aliases) in test_databases:
            all_deps = set()
            for alias in aliases:
                all_deps.update(dependencies.get(alias, []))
            if not all_deps.isdisjoint(aliases):
                raise ImproperlyConfigured(
                    f"Circular dependency: databases {aliases!r} depend on each other, but are aliases."
                )
            dependencies_map[sig] = all_deps

        while test_databases:
            changed = False

            deferred = []

            # Try to find a DB that has all its dependencies met
            for signature, (db_name, aliases) in test_databases:
                if dependencies_map[signature].issubset(resolved_databases):
                    resolved_databases.update(aliases)
                    ordered_test_databases.append((signature, (db_name, aliases)))
                    changed = True
                else:
                    deferred.append((signature, (db_name, aliases)))

            if not changed:
                raise ImproperlyConfigured("Circular dependency in TEST[DEPENDENCIES]")
            test_databases = deferred
        return ordered_test_databases

    def setup_databases_18(self, **kwargs):
        mirrored_aliases = {}
        test_databases = {}
        dependencies = {}

        worker_index = kwargs.get("worker_index", None)
        for alias in connections:
            connection = connections[alias]
            database_name = f"test_{worker_index}_{connection.settings_dict['NAME']}"
            connection.settings_dict["TEST_NAME"] = database_name

            item = test_databases.setdefault(
                connection.creation.test_db_signature(), (connection.settings_dict["NAME"], [])
            )
            item[1].append(alias)
            if alias != DEFAULT_DB_ALIAS:
                dependencies[alias] = connection.settings_dict.get("TEST_DEPENDENCIES", [DEFAULT_DB_ALIAS])

        old_names = []
        mirrors = []
        for signature, (db_name, aliases) in self.dependency_ordered(list(test_databases.items()), dependencies):
            connection = connections[aliases[0]]
            old_names.append((connection, db_name, True))
            test_db_name = connection.creation.create_test_db(verbosity=0, autoclobber=not self.interactive)
            for alias in aliases[1:]:
                connection = connections[alias]
                if db_name:
                    old_names.append((connection, db_name, False))
                    connection.settings_dict["NAME"] = test_db_name
                else:
                    old_names.append((connection, db_name, True))
                    connection.creation.create_test_db(verbosity=0, autoclobber=not self.interactive)

        for alias, mirror_alias in mirrored_aliases.items():
            mirrors.append((alias, connections[alias].settings_dict["NAME"]))
            connections[alias].settings_dict["NAME"] = connections[mirror_alias].settings_dict["NAME"]

        return old_names, mirrors

    def _tests_func(self, tests, worker_index):
        self.setup_test_environment()
        suite = self.build_suite(tests, [])
        old_config = self.setup_databases(worker_index=worker_index)
        result = self.run_suite(suite)
        self.teardown_databases(old_config)
        self.teardown_test_environment()

        result = TestResult().from_django_result(result)
        return result


class DjangoParallelTestRunner(DiscoverRunner):
    def __init__(self, verbosity=2, failfast=True, **kwargs):
        stream = BufferWritesDevice()
        super().__init__(stream=stream, verbosity=verbosity, failfast=failfast)


class TestResult:
    dots = False
    errors = None
    failures = None
    exception = None
    output = None

    def from_django_result(self, result_obj):
        self.dots = result_obj.dots
        self.errors = result_obj.errors
        self.failures = self._format_failures(result_obj.failures)
        try:
            self.output = result_obj.stream.read()
        except Exception:
            pass
        return self

    def from_trial_result(self, result_obj):
        self.errors = self._format_failures(result_obj.errors)
        self.failures = self._format_failures(result_obj.failures)
        try:
            self.output = result_obj.stream.read()
        except Exception:
            pass
        return self

    def from_exception(self, exception):
        self.exception = str(exception)
        return self

    def _format_failures(self, failures):
        # errors and failures attributes by default contain values which are not
        # pickable (class instance)
        if not failures:
            return failures

        formatted = []
        for failure in failures:
            klass, message = failure
            formatted.append((str(klass), message))
        return formatted


class NullTimeKeeper:
    @contextmanager
    def timed(self, name):
        yield

    def print_results(self):
        pass


class TimeKeeper:
    def __init__(self):
        self.records = Collection.defaultdict(list)

    @contextmanager
    def timed(self, name):
        self.records[name]
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter() - start_time
            self.records[name].append(end_time)

    def print_results(self):
        for name, end_times in self.records.items():
            for record_time in end_times:
                record = f"{name} took {record_time:.3f}s"
                sys.stderr.write(record + os.linesep)
