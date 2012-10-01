from django.conf import settings
from django_nose import NoseTestSuiteRunner
from urllib2 import urlopen

class GeonodeTestSuiteRunner(NoseTestSuiteRunner):

    def run_tests(self, test_labels, extra_tests=None):
        """check if geoserver is currently running"""

        try:
            url_handle = urlopen(settings.GEOSERVER_BASE_URL)
        except:
            pass
        else:
            url_handle.close()
            print '*' * 80
            print 'Server already running on: %s' % settings.GEOSERVER_BASE_URL
            print 'Bailing early because tests will fail'
            print '*' * 80
            return

        return super(GeonodeTestSuiteRunner, self).run_tests(test_labels, extra_tests)
