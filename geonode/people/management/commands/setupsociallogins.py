import os


from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = (
        "Setup login via social providers - You need to add the relevant apps "
        "to ``INSTALLED_APPS`` in order to be able to use this command (e.g. "
        "add ``allauth.socialaccount.providers.facebook`` in order to "
        "configure logins with facebook credentials)"
    )

    @staticmethod
    def _get_client_id_arg(provider):
        return f"{provider}-client-id"

    @staticmethod
    def _get_client_secret_arg(provider):
        return f"{provider}-secret-key"

    @staticmethod
    def _get_client_id_env(provider):
        return f"{provider.upper()}_OAUTH2_CLIENT_ID"

    @staticmethod
    def _get_client_secret_env(provider):
        return f"{provider.upper()}_OAUTH2_SECRET_KEY"

    @staticmethod
    def get_social_providers():
        providers = []
        for app_info in settings.INSTALLED_APPS:
            if isinstance(app_info, str):
                if app_info.startswith("allauth.socialaccount.providers"):
                    provider_module = app_info.rpartition(".")[-1]
                    provider_name = provider_module.partition("_")[0]
                    providers.append((provider_name, provider_module))
        return providers

    def add_arguments(self, parser):
        for provider_name, provider_id in self.get_social_providers():
            client_id_arg = self._get_client_id_arg(provider_name)
            parser.add_argument(
                f"--{client_id_arg}",
                help=(
                    f"Specify the client id for {provider_name}. You may also specify "
                    f"the {self._get_client_id_env(provider_name)} environment variable instead"
                )
            )
            client_secret_arg = self._get_client_secret_arg(provider_name)
            parser.add_argument(
                f"--{client_secret_arg}",
                help=(
                    f"Specify the secret key for {provider_name}. You may also specify "
                    f"the {self._get_client_secret_env(provider_name)} environment variable instead"
                )
            )

    def handle(self, *args, **options):
        social_providers = self.get_social_providers()
        if len(social_providers) > 0:
            for provider_name, provider_id in social_providers:
                client_id_arg = self._get_client_id_arg(
                    provider_name).replace("-", "_")
                client_secret_arg = self._get_client_secret_arg(
                    provider_name).replace("-", "_")
                client_id = (
                    options.get(client_id_arg) or
                    os.getenv(self._get_client_id_env(provider_name))
                )
                client_secret = (
                    options.get(client_secret_arg) or
                    os.getenv(self._get_client_secret_env(provider_name))
                )
                if all((client_id, client_secret)):
                    self.stdout.write(
                        f"Configuring provider {provider_name}...")
                    self._handle_provider(
                        provider_name, provider_id, client_id, client_secret)
                else:
                    self.stdout.write(
                        f"Provider {provider_name} not all params were specified, "
                        "skipping..."
                    )
        else:
            self.stdout.write(
                "No social providers are currently in use, skipping...")
            self.stdout.write(
                "Add the relevant apps to the SETTINGS.INSTALLED_APPS and "
                "rerun this command."
            )

    def _handle_provider(self, name, id_, client_id, secret_key):
        provider, created = SocialApp.objects.get_or_create(
            name=name.lower(),
            client_id=client_id,
            secret=secret_key,
            provider=id_
        )
        if created:
            # associate with the first site
            provider.sites.add(Site.objects.get_current())
            provider.save()
        else:
            self.stdout.write(
                f"Provider {name} already exists, skipping...")
