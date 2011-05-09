from django_nose import NoseTestSuiteRunner
from django.test.simple import reorder_suite, build_suite
from django.test.simple import build_test as please_build_test
from django.db.models import get_app, get_apps
from geonode.maps.utils import check_geonode_is_up


class GeoNodeTestRunner(NoseTestSuiteRunner):
    """ This test runner allows the exclusion of some
        of the apps from the test suite
    """
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
        # Django's auth module passes in objects that aren't model instances
        # and asks for their permissions.
                     'django.contrib.auth.models',
                     'django_nose',
    ]

    def __init__(self, *args, **kwargs):
        check_geonode_is_up()
        super(GeoNodeTestRunner, self).__init__(*args, **kwargs)

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = unittest.TestSuite()

        if test_labels:
            for label in test_labels:
                if '.' in label:
                    suite.addTest(please_build_test(label))
                else:
                    app = get_app(label)
                    suite.addTest(please_build_suite(app))
        else:
            for app in get_apps():
                if app.__name__ not in self.EXCLUDED_APPS:
                    print app.__name__
                    suite.addTest(build_suite(app))

        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)

        return reorder_suite(suite, (TestCase,))

    # Override this method so we *dont* create a test database (use the normal one)
    def setup_databases(self, **kwargs):
        pass

    # Override this method so we dont drop the normal database
    def teardown_databases(self, old_config, **kwargs):
        pass
