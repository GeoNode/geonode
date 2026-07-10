from django.db import migrations


def add_openid_scope(apps, schema_editor):
    AccessToken = apps.get_model("oauth2_provider", "AccessToken")
    updated = AccessToken.objects.all().update(scope="openid")
    if updated:
        print(f"\nUpdated {updated} access token(s) to include 'openid' scope.")


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0100_migrate_extrametadata_to_sparsefields"),
        ("oauth2_provider", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_openid_scope, migrations.RunPython.noop),
    ]
