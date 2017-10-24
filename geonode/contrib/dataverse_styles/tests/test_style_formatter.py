from __future__ import print_function

from os.path import abspath, dirname, isfile, join, isdir, realpath
from unittest import skip

from django.utils import unittest
from django.conf import settings

#from lxml import etree

from geonode.contrib.dataverse_styles.style_rules_formatter import StyleRulesFormatter
from geonode.contrib.msg_util import msg, msgt



class StyleFormatterTestCase(unittest.TestCase):
    """Test style formatting for Points vs Polygons"""

    def setUp(self):
        settings.DEBUG = True
        self.test_file_dir = join(dirname(realpath(__file__)), 'input')
        assert isdir(self.test_file_dir),\
            'Input directory not found: %s' % self.test_file_dir

    def get_input_file(self, fname):
        """Convenience method for opening a test input file"""
        full_fname = join(self.test_file_dir, fname)

        msg('open input file: %s' % full_fname)
        assert isfile(full_fname),\
            "Test input directory not found: %s" % full_fname

        fh = open(full_fname, 'r')
        content = fh.read()
        fh.close()
        return content


    def test_01_style_formatter(self):
        """Style lat/lng SLD on a string attribute"""
        msgt(self.test_01_style_formatter.__doc__)
        extra_kwargs = dict(\
                is_point_layer=True,
                current_sld=self.get_input_file('t1_01_current_sld.xml'),
                predefined_id='abc1234')

        msg('Load current SLD')
        sld_formatter = StyleRulesFormatter('boston_pub_f43_abc1234',
                                            **extra_kwargs)


        # Format rule data
        msg('Apply rule data')
        sld_rule_data = self.get_input_file('t1_02_sld_rules.xml')
        sld_formatter.format_sld_xml(sld_rule_data)

        # Should be no errors
        self.assertEqual(sld_formatter.err_found, False)

        new_sld_xml = sld_formatter.formatted_sld_xml
        self.assertTrue(new_sld_xml is not None)


        expected_sld = self.get_input_file('t1_03_full_sld.xml')
        self.assertEqual(new_sld_xml.strip(), expected_sld.strip())

    def test_02_style_formatter(self):
        """Style lat/lng SLD on a numeric attribute"""
        msgt(self.test_02_style_formatter.__doc__)

        extra_kwargs = dict(\
                is_point_layer=True,
                current_sld=self.get_input_file('t2_01_current_sld.xml'),
                predefined_id='abc1234')

        msg('Load current SLD')
        sld_formatter = StyleRulesFormatter('starbucks_u_gl_abc1234',
                                            **extra_kwargs)

        # Format rule data
        msg('Apply rule data')
        sld_rule_data = self.get_input_file('t2_02_sld_rules.xml')
        sld_formatter.format_sld_xml(sld_rule_data)

        # Should be no errors
        self.assertEqual(sld_formatter.err_found, False)

        new_sld_xml = sld_formatter.formatted_sld_xml
        self.assertTrue(new_sld_xml is not None)

        expected_sld = self.get_input_file('t2_03_full_sld.xml')
        self.assertEqual(new_sld_xml.strip(), expected_sld.strip())
