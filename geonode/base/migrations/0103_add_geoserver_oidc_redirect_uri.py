from django.conf import settings
from django.db import migrations


def add_oidc_redirect_uri(apps, schema_editor):
    Application = apps.get_model("oauth2_provider", "Application")
    uri = f"{settings.GEOSERVER_PUBLIC_LOCATION}web/login/oauth2/code/geonode-oidc__oidc"
    for app in Application.objects.filter(name="GeoServer").exclude(redirect_uris__contains=uri):
        app.redirect_uris = f"{app.redirect_uris}\n{uri}".strip()
        app.save(update_fields=["redirect_uris"])
        print(f"\nAdded GeoServer OIDC redirect URI {uri} to OAuth application '{app.name}'.")


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0102_add_openid_scope_to_access_tokens"),
        ("oauth2_provider", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_oidc_redirect_uri, migrations.RunPython.noop),
    ]