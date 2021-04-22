from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse
from selenium import webdriver
# from selenium.webdriver.chrome.webdriver import WebDriver
# from webdriver_manager.chrome import ChromeDriverManager
from . import enumerations, forms


class WmsServiceHarvestingTestCase(StaticLiveServerTestCase):
    selenium = None

    @classmethod
    def setUpClass(cls):
        super(WmsServiceHarvestingTestCase, cls).setUpClass()

        try:
            cls.client = Client()
            UserModel = get_user_model()
            cls.user = UserModel.objects.create_user(username='test', password='test@123', first_name='ather',
                                                     last_name='ashraf', is_staff=True,
                                                     is_active=True, is_superuser=False)
            cls.user.save()
            cls.client.login(username='test', password='test@123')
            cls.cookie = cls.client.cookies['sessionid']
            cls.selenium = webdriver.Firefox()
            cls.selenium.implicitly_wait(10)
            cls.selenium.get(f"{cls.live_server_url}/")
            cls.selenium.add_cookie({'name': 'sessionid', 'value': cls.cookie.value, 'secure': False, 'path': '/'})
            cls.selenium.refresh()
            reg_url = reverse('register_service')
            cls.client.get(reg_url)

            url = 'https://demo.geo-solutions.it/geoserver/ows?service=wms&version=1.3.0&request=GetCapabilities'
            service_type = enumerations.WMS
            form_data = {
                'url': url,
                'type': service_type
            }
            forms.CreateServiceForm(form_data)

            response = cls.client.post(reverse('register_service'), data=form_data)
            cls.selenium.get(cls.live_server_url + response.url)
            cls.selenium.refresh()
        except Exception as e:
            msg = str(e)
            print(msg)

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
            super(WmsServiceHarvestingTestCase, cls).tearDownClass()

    def test_harvest_resources(self):
        if self.selenium:
            table = self.selenium.find_element_by_id('resource_table')
            self.test_resource_table_status(table, False)

            self.selenium.find_element_by_id('id-filter').send_keys('atlantis:roads')
            self.selenium.find_element_by_id('btn-id-filter').click()
            self.test_resource_table_status(table, True)

            self.selenium.find_element_by_id('name-filter').send_keys('landmarks')
            self.selenium.find_element_by_id('btn-name-filter').click()
            self.test_resource_table_status(table, True)

            self.selenium.find_element_by_id('desc-filter').send_keys('None')
            self.selenium.find_element_by_id('btn-desc-filter').click()
            self.test_resource_table_status(table, True)

            self.selenium.find_element_by_id('desc-filter').send_keys('')
            self.selenium.find_element_by_id('btn-desc-filter').click()
            self.test_resource_table_status(table, True)

            self.selenium.find_element_by_id('btnClearFilter').click()
            self.test_resource_table_status(table, False)
            self.selenium.find_element_by_id('id-filter').send_keys('atlantis:tiger_roads_tiger_roads')

            # self.selenium.find_element_by_id('btn-id-filter').click()
            # self.selenium.find_element_by_id('option_atlantis:tiger_roads_tiger_roads').click()
            # self.selenium.find_element_by_tag_name('form').submit()

    def test_resource_table_status(self, table, is_row_filtered):
        tbody = table.find_elements_by_tag_name('tbody')
        rows = tbody[0].find_elements_by_tag_name('tr')
        visible_rows_count = 0
        filter_row_count = 0
        hidden_row_count = 0
        for row in rows:
            attr_name = row.get_attribute('name')
            val = row.value_of_css_property('display')

            if attr_name == "filter_row":
                filter_row_count = filter_row_count + 1
            if val == "none":
                hidden_row_count = hidden_row_count + 1
            else:
                visible_rows_count = visible_rows_count + 1
        result = {"filter_row_count": filter_row_count,
                  "visible_rows_count": visible_rows_count,
                  "hidden_row_count": hidden_row_count}

        if is_row_filtered:
            self.assertTrue(result["filter_row_count"] > 0)
            self.assertEqual(result["visible_rows_count"], result["filter_row_count"])
            self.assertEqual(result["hidden_row_count"], 20)
        else:
            self.assertEqual(result["filter_row_count"], 0)
            self.assertEqual(result["visible_rows_count"], 20)
            self.assertEqual(result["hidden_row_count"], 0)
