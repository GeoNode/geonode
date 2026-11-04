from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Concat, Trim


def add_openid_scope(apps, schema_editor):
    AccessToken = apps.get_model("oauth2_provider", "AccessToken")
    updated = AccessToken.objects.exclude(scope__contains="openid").update(
        scope=Trim(Concat("scope", Value(" openid")))
    )
    if updated:
        print(f"\nAdded 'openid' scope to {updated} access token(s).")


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0101_remove_source_type_copyremote"),
        ("oauth2_provider", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_openid_scope, migrations.RunPython.noop),
    ]