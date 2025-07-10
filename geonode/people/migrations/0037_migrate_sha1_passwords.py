from django.db import migrations

from geonode.people.hashers import PBKDF2SHA1WrappedSHA1PasswordHasher


def forwards_func(apps, schema_editor):
    User = apps.get_model("people", "Profile")
    users = User.objects.filter(password__startswith="sha1$")
    hasher = PBKDF2SHA1WrappedSHA1PasswordHasher()
    for user in users:
        algorithm, salt, sha1_hash = user.password.split("$", 2)
        user.password = hasher.encode_sha1_hash(sha1_hash, salt)
        user.save(update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0036_merge_20210706_0951"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
