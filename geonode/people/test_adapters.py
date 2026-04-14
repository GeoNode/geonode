"""unit tests for geonode.people.adapters"""

from unittest import TestCase

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from geonode.groups.models import GroupProfile
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.people import adapters

try:
    import unittest.mock as mock
except ImportError:
    from unittest import mock


class GetDataExtractorTestCase(TestCase):
    @mock.patch("geonode.people.adapters.settings", autospec=True)
    @mock.patch("geonode.people.adapters.import_string", autospec=True)
    def test_get_data_extractor_valid_provider(self, mock_import_string, mock_settings):
        provider_name = "phony_name"
        provider_python_path = "phony.package.module.FakeExtractor"
        fake_extractor_class = mock.MagicMock()
        mock_settings.SOCIALACCOUNT_PROFILE_EXTRACTORS = {provider_name: provider_python_path}
        mock_import_string.return_value = fake_extractor_class
        adapters.get_data_extractor(provider_name)
        self.assertTrue(fake_extractor_class.called)

    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_get_data_extractor_invalid_provider(self, mock_settings):
        provider_name = "inexistent_provider"
        mock_settings.SOCIALACCOUNT_PROFILE_EXTRACTORS = {}
        result = adapters.get_data_extractor(provider_name)
        self.assertIsNone(result)


class UpdateProfileTestCase(TestCase):
    def setUp(self):
        self.fake_user = "phony_user"
        self.fake_area = "phony_area"
        self.fake_city = "phony_city"
        self.fake_country = "phony_country"
        self.fake_delivery = "phony_delivery"
        self.fake_fax = "phony_fax"
        self.fake_first_name = "phony_first_name"
        self.fake_last_name = "phony_last_name"
        self.fake_organization = "phony_organization"
        self.fake_position = "phony_position"
        self.fake_profile = "phony_profile"
        self.fake_voice = "phony_voice"
        self.fake_zipcode = "phony_zipcode"
        mock_social_login_class = mock.MagicMock(spec="allauth.socialaccount.models.SocialLogin")
        self.mock_social_login = mock_social_login_class.return_value
        self.mock_social_login.user = self.fake_user
        self.mock_social_login.account.provider = "phony_provider"
        mock_extractor_class = mock.MagicMock(spec="geonode.people.profileextractors.BaseExtractor")
        self.mock_extractor = mock_extractor_class.return_value
        self.mock_extractor.extract_area.return_value = self.fake_area
        self.mock_extractor.extract_city.return_value = self.fake_city
        self.mock_extractor.extract_country.return_value = self.fake_country
        self.mock_extractor.extract_delivery.return_value = self.fake_delivery
        self.mock_extractor.extract_fax.return_value = self.fake_fax
        self.mock_extractor.extract_first_name.return_value = self.fake_first_name
        self.mock_extractor.extract_last_name.return_value = self.fake_last_name
        self.mock_extractor.extract_organization.return_value = self.fake_organization
        self.mock_extractor.extract_position.return_value = self.fake_position
        self.mock_extractor.extract_profile.return_value = self.fake_profile
        self.mock_extractor.extract_voice.return_value = self.fake_voice
        self.mock_extractor.extract_zipcode.return_value = self.fake_zipcode

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_area_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_area.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "area", self.fake_area)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_city_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_city.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "city", self.fake_city)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_country_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_country.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "country", self.fake_country)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_delivery_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_delivery.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "delivery", self.fake_delivery)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_fax_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_fax.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "fax", self.fake_fax)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_first_name_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_first_name.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "first_name", self.fake_first_name)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_last_name_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_last_name.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "last_name", self.fake_last_name)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_organization_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_organization.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "organization", self.fake_organization)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_position_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_position.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "position", self.fake_position)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_profile_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_profile.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "profile", self.fake_profile)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_voice_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_voice.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "voice", self.fake_voice)
        self.assertIn(expected_call, args_list)

    @mock.patch.object(adapters, "get_data_extractor")
    @mock.patch("geonode.people.adapters.user_field", autospec=True)
    def test_update_profile_covers_zipcode_field(self, mock_user_field, mock_get_extractor):
        mock_get_extractor.return_value = self.mock_extractor
        adapters.update_profile(self.mock_social_login)
        self.assertTrue(self.mock_extractor.extract_zipcode.called)
        args_list = mock_user_field.call_args_list
        expected_call = mock.call(self.fake_user, "zipcode", self.fake_zipcode)
        self.assertIn(expected_call, args_list)


class SiteAllowsSignupTestCase(TestCase):
    def setUp(self):
        django_request_class = mock.MagicMock(spec="django.http.request.HttpRequest")
        self.django_request = django_request_class.return_value

    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_signup_allowed_when_setting_true(self, mock_settings):
        mock_settings.ACCOUNT_OPEN_SIGNUP = True
        result = adapters._site_allows_signup(self.django_request)
        self.assertTrue(result)

    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_signup_allowed_when_setting_false_and_verified_email(self, mock_settings):
        self.django_request.session = {"account_verified_email": True}
        mock_settings.ACCOUNT_OPEN_SIGNUP = False
        result = adapters._site_allows_signup(self.django_request)
        self.assertTrue(result)

    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_signup_not_allowed_when_setting_false_not_verified_email(self, mock_settings):
        self.django_request.session = {}
        mock_settings.ACCOUNT_OPEN_SIGNUP = False
        result = adapters._site_allows_signup(self.django_request)
        self.assertFalse(result)


class RespondInactiveUserTestCase(TestCase):
    @mock.patch("geonode.people.adapters.reverse", autospec=True)
    @mock.patch("geonode.people.adapters.HttpResponseRedirect", autospec=True)
    def test_respond_inactive_user(self, mock_http_response_redirect_class, mock_reverse):
        phony_reverse = "phony"
        fake_id = "fake_id"
        phony_user_class = mock.MagicMock(spec="geonode.people.models.Profile")
        phony_user = phony_user_class.return_value
        phony_user.id = fake_id
        mock_reverse.return_value = phony_reverse
        adapters._respond_inactive_user(phony_user)
        mock_reverse.assert_called_with("moderator_contacted", kwargs={"inactive_user": fake_id})
        mock_http_response_redirect_class.assert_called_with(phony_reverse)


class RespondInvalidEmailUserTestCase(TestCase):
    @mock.patch("geonode.people.adapters.reverse", autospec=True)
    @mock.patch("geonode.people.adapters.HttpResponseRedirect", autospec=True)
    def test_respond_invalid_email_user(self, mock_http_response_redirect_class, mock_reverse):
        phony_reverse = "phony"
        fake_email = "fake_email"
        phony_user_class = mock.MagicMock(spec="geonode.people.models.Profile")
        phony_user = phony_user_class.return_value
        phony_user.email = fake_email
        mock_reverse.return_value = phony_reverse
        adapters.handle_user_invalid_email(phony_user)
        mock_reverse.assert_called_with("moderator_needed")
        mock_http_response_redirect_class.assert_called_with(phony_reverse)

    @mock.patch("geonode.people.adapters.reverse", autospec=True)
    @mock.patch("geonode.people.adapters.HttpResponseRedirect", autospec=True)
    def test_respond_valid_email_user(self, mock_http_response_redirect_class, mock_reverse):
        phony_reverse = "phony"
        fake_id = "fake_id"
        fake_email = "valid_email@mail.com"
        fake_username = "fake_username"
        phony_user_class = mock.MagicMock(spec="geonode.people.models.Profile")
        phony_user = phony_user_class.return_value
        phony_user.id = fake_id
        phony_user.email = fake_email
        phony_user.username = fake_username
        mock_reverse.return_value = phony_reverse
        adapters.handle_user_invalid_email(phony_user)
        mock_reverse.assert_not_called()
        mock_http_response_redirect_class.assert_not_called()


class LocalAccountAdapterTestCase(TestCase):
    def setUp(self):
        self.extractor = adapters.LocalAccountAdapter()
        django_request_class = mock.MagicMock(spec="django.http.request.HttpRequest")
        self.django_request = django_request_class.return_value

    @mock.patch.object(adapters, "_site_allows_signup")
    def test_is_open_for_signup(self, mock_func):
        dummy_return = "dummy"
        mock_func.return_value = dummy_return
        result = self.extractor.is_open_for_signup(self.django_request)
        mock_func.assert_called_with(self.django_request)
        self.assertEqual(result, dummy_return)

    @mock.patch("geonode.people.adapters.reverse", autospec=True)
    def test_get_login_redirect_url(self, mock_reverse):
        dummy_reverse = "dummy"
        dummy_username = "dummy_username"
        self.django_request.user.username = dummy_username
        mock_reverse.return_value = dummy_reverse
        result = self.extractor.get_login_redirect_url(self.django_request)
        mock_reverse.assert_called_with("profile_detail", kwargs={"username": dummy_username})
        self.assertEqual(result, dummy_reverse)

    @mock.patch.object(adapters.DefaultAccountAdapter, "save_user")
    def test_save_user_no_approval_required(self, mock_settings, mock_base_save_user):
        mock_user_class = mock.MagicMock(spec="geonde.people.models.Profile")
        mock_user = mock_user_class.return_value
        mock_user.is_active = True
        phony_form = "phony_form"
        phony_commit = "phony_commit"
        mock_settings.ACCOUNT_APPROVAL_REQUIRED = False
        result = self.extractor.save_user(self.django_request, mock_user, phony_form, commit=phony_commit)
        mock_base_save_user.assert_called_with(self.django_request, mock_user, phony_form, commit=phony_commit)
        self.assertTrue(result.is_active)

    @mock.patch.object(adapters.DefaultAccountAdapter, "save_user")
    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_save_user_with_approval_required(self, mock_settings, mock_base_save_user):
        mock_user_class = mock.MagicMock(spec="geonde.people.models.Profile")
        mock_user = mock_user_class.return_value
        mock_user.is_active = True
        phony_form = "phony_form"
        phony_commit = "phony_commit"
        mock_settings.ACCOUNT_APPROVAL_REQUIRED = True
        mock_base_save_user.return_value = mock_user
        result = self.extractor.save_user(self.django_request, mock_user, phony_form, commit=phony_commit)
        mock_base_save_user.assert_called_with(self.django_request, mock_user, phony_form, commit=phony_commit)
        self.assertFalse(result.is_active)
        self.assertTrue(mock_user.save.called)

    @mock.patch.object(adapters, "_respond_inactive_user")
    def test_respond_user_inactive(self, mock_func):
        dummy_return = "dummy"
        dummy_user = "dummy_user"
        mock_func.return_value = dummy_return
        result = self.extractor.respond_user_inactive(self.django_request, dummy_user)
        mock_func.assert_called_with(dummy_user)
        self.assertEqual(result, dummy_return)


class SocialAccountAdapterTestCase(TestCase):
    def setUp(self):
        self.extractor = adapters.SocialAccountAdapter()
        django_request_class = mock.MagicMock(spec="django.http.request.HttpRequest")
        self.django_request = django_request_class.return_value

    @mock.patch.object(adapters, "_site_allows_signup")
    def test_is_open_for_signup(self, mock_func):
        dummy_return = "dummy"
        fake_sociallogin = "phony_sociallogin"
        mock_func.return_value = dummy_return
        result = self.extractor.is_open_for_signup(self.django_request, fake_sociallogin)
        mock_func.assert_called_with(self.django_request)
        self.assertEqual(result, dummy_return)

    @mock.patch.object(adapters.DefaultSocialAccountAdapter, "populate_user")
    @mock.patch.object(adapters, "update_profile")
    def test_populate_user(self, mock_update_profile, mock_base_populate_user):
        fake_sociallogin = "phony_sociallogin"
        fake_data = "phony_data"
        fake_user = "phony_user"
        mock_base_populate_user.return_value = fake_user
        result = self.extractor.populate_user(self.django_request, fake_sociallogin, fake_data)
        mock_base_populate_user.assert_called_with(self.django_request, fake_sociallogin, fake_data)
        self.assertEqual(result, fake_user)

    @mock.patch.object(adapters.DefaultSocialAccountAdapter, "save_user")
    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_save_user_no_approval_required(self, mock_settings, mock_base_save_user):
        fake_sociallogin = "phony_sociallogin"
        mock_user_class = mock.MagicMock(spec="geonde.people.models.Profile")
        mock_user = mock_user_class.return_value
        mock_user.is_active = True
        phony_form = "phony_form"
        mock_base_save_user.return_value = mock_user
        mock_settings.ACCOUNT_APPROVAL_REQUIRED = False
        result = self.extractor.save_user(self.django_request, fake_sociallogin, phony_form)
        mock_base_save_user.assert_called_with(self.django_request, fake_sociallogin, form=phony_form)
        self.assertTrue(result.is_active)

    @mock.patch.object(adapters.DefaultSocialAccountAdapter, "save_user")
    @mock.patch("geonode.people.adapters.settings", autospec=True)
    def test_save_user_with_approval_required(self, mock_settings, mock_base_save_user):
        fake_sociallogin = "phony_sociallogin"
        mock_user_class = mock.MagicMock(spec="geonde.people.models.Profile")
        mock_user = mock_user_class.return_value
        mock_user.is_active = True
        phony_form = "phony_form"
        mock_settings.ACCOUNT_APPROVAL_REQUIRED = True
        mock_base_save_user.return_value = mock_user
        result = self.extractor.save_user(self.django_request, fake_sociallogin, phony_form)
        mock_base_save_user.assert_called_with(self.django_request, fake_sociallogin, form=phony_form)
        self.assertFalse(result.is_active)
        self.assertTrue(mock_user.save.called)

    @mock.patch.object(adapters, "_respond_inactive_user")
    def test_respond_user_inactive(self, mock_func):
        dummy_return = "dummy"
        dummy_user = "dummy_user"
        mock_func.return_value = dummy_return
        result = self.extractor.respond_user_inactive(self.django_request, dummy_user)
        mock_func.assert_called_with(dummy_user)
        self.assertEqual(result, dummy_return)


class GenericOpenIDConnectAdapterTestCase(GeoNodeBaseTestSupport):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username="test_user")
        self.group_bar = GroupProfile.objects.get(slug="bar")

        # Ensure a clean state: put user in 'bar' to start
        if not self.user.groups.filter(pk=self.group_bar.pk).exists():
            self.group_bar.join(self.user)

        # Mock the SocialLogin
        self.mock_sociallogin = mock.MagicMock()
        self.mock_sociallogin.account.provider = "openid_connect"
        self.mock_sociallogin.user = self.user

    @mock.patch("geonode.people.adapters.get_data_extractor")
    @override_settings(SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN="SAFE_SYNC")
    def test_safe_sync_skips_on_missing_key(self, mock_get_extractor):
        """Verify SAFE_SYNC preserves 'bar' if group data is missing."""
        # Setup mock extractor to return "" (missing key signal)
        mock_ext = mock.MagicMock()
        mock_ext.extract_groups.return_value = None
        mock_ext.extract_roles.return_value = None
        mock_get_extractor.return_value = mock_ext

        # Run logic with no groups in extra_data
        self.mock_sociallogin.account.extra_data = {"id": "123"}
        adapters._update_user_groups_from_social(self.mock_sociallogin, self.user)

        # Assert: User is still in 'bar'
        self.assertTrue(self.user.groups.filter(groupprofile__slug="bar").exists())

    @mock.patch("geonode.people.adapters.get_data_extractor")
    @override_settings(SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN="SAFE_SYNC")
    def test_safe_sync_wipes_on_empty_list(self, mock_get_extractor):
        """Verify SAFE_SYNC wipes 'bar' if provider explicitly sends empty list."""
        mock_ext = mock.MagicMock()
        mock_ext.extract_groups.return_value = []
        mock_get_extractor.return_value = mock_ext

        self.mock_sociallogin.account.extra_data = {"groups": []}
        adapters._update_user_groups_from_social(self.mock_sociallogin, self.user)

        # Assert: User is removed from everything
        self.assertEqual(self.user.groups.count(), 0)

    @mock.patch("geonode.people.adapters.get_data_extractor")
    @override_settings(SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN="SAFE_SYNC")
    def test_safe_sync_performs_correct_update(self, mock_get_extractor):
        """Verify SAFE_SYNC acts like FULL_SYNC when valid data is present."""
        azure_uuid = "4b7e2db3-2bd2-4c8e-aa71-7d6d2714e603"

        # Create the base Django Group first
        dj_group, _ = Group.objects.get_or_create(name="Azure Group")

        GroupProfile.objects.get_or_create(slug=azure_uuid, defaults={"group": dj_group, "title": "Azure Group"})

        mock_ext = mock.MagicMock()
        mock_ext.extract_groups.return_value = [azure_uuid]
        mock_get_extractor.return_value = mock_ext

        self.mock_sociallogin.account.extra_data = {"groups": [azure_uuid]}
        adapters._update_user_groups_from_social(self.mock_sociallogin, self.user)

        # User should have left 'bar' and joined the Azure group
        self.assertFalse(self.user.groups.filter(groupprofile__slug="bar").exists())
        self.assertTrue(self.user.groups.filter(groupprofile__slug=azure_uuid).exists())

    @mock.patch("geonode.people.adapters.get_data_extractor")
    @override_settings(SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN="FULL_SYNC")
    def test_full_sync_wipes_on_missing_key(self, mock_get_extractor):
        """Verify FULL_SYNC (default) wipes groups even if the key is missing."""
        # Mock extractor to return "" (missing key signal)
        mock_ext = mock.MagicMock()
        mock_ext.extract_groups.return_value = ""
        mock_ext.extract_roles.return_value = ""
        mock_get_extractor.return_value = mock_ext

        # Simulate Azure response with NO groups key
        self.mock_sociallogin.account.extra_data = {"id": "123"}
        adapters._update_user_groups_from_social(self.mock_sociallogin, self.user)

        # In FULL_SYNC, the user should be removed from 'bar'
        self.assertFalse(self.user.groups.filter(groupprofile__slug="bar").exists())

    @mock.patch("geonode.people.adapters.get_data_extractor")
    @override_settings(SOCIALACCOUNT_SYNC_USER_GROUPS_ON_LOGIN="NO_SYNC")
    def test_no_sync_ignores_provider_data(self, mock_get_extractor):
        """Verify NO_SYNC does not touch local groups regardless of provider data."""
        mock_ext = mock.MagicMock()
        # Even if provider says the user belongs to 'bar'
        mock_ext.extract_groups.return_value = ["bar"]
        mock_get_extractor.return_value = mock_ext

        # and we simulate an empty list in the token
        self.mock_sociallogin.account.extra_data = {"groups": []}
        adapters._update_user_groups_from_social(self.mock_sociallogin, self.user)

        # User should STILL be in 'bar' because we are not syncing
        self.assertTrue(self.user.groups.filter(groupprofile__slug="bar").exists())
