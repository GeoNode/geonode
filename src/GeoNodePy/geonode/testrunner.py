from django.test.simple import DjangoTestSuiteRunner, TestCase
from django.test.simple import reorder_suite, build_test, build_suite
from django.db.models import get_app, get_apps
import unittest
import socket
import os

def isOpen(ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
     s.connect((ip, int(port)))
     s.shutdown(2)
     return True
    except:
     return False


class GeoNodeTestRunner(DjangoTestSuiteRunner):
    """ This test runner allows the exclusion of some
        of the apps from the test suite
    """
    def __init__(self, verbosity=1, interactive=True, failfast=True, **kwargs):
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        # Check if a server is running in port 8080 and set the GEOSERVER flag
        if "GEOSERVER" not in os.environ.keys():
            if isOpen('127.0.0.1', '8001'):
                os.environ["GEOSERVER"]="True"

    EXCLUDED_APPS = [
        # Registration complains about email
        # messages in spanish, ticket has been filled at:
        # http://bitbucket.org/ubernostrum/django-registration/issue/93
                     'registration.models',
        # Django extensions tries to import keyczar to test the encryption
        # that import failing aborts the test suite run.
        # Keyczar test problems issue is being tracked at:
        # http://github.com/django-extensions/django-extensions/issues#issue/17  
                     'django_extensions.models',
        # Django avatar requires PIL to be compiled with the libjpeg bindings
        # in some development systems (MacOSX) this is not done with the
        # default PIL install.
                     'avatar.models',
        ]

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = unittest.TestSuite()

        if test_labels:
            for label in test_labels:
                if '.' in label:
                    suite.addTest(build_test(label))
                else:
                    app = get_app(label)
                    suite.addTest(build_suite(app))
        else:
            for app in get_apps():
                if app.__name__ not in self.EXCLUDED_APPS:
                    print app.__name__
                    suite.addTest(build_suite(app))

        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)

        return reorder_suite(suite, (TestCase,))

