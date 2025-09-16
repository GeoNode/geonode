from django.db import migrations

from geonode.people.hashers import PBKDF2SHA1WrappedSHA1PasswordHasher


def forwards_func(apps, schema_editor):
    User = apps.get_model("people", "Profile")
    users = User.objects.filter(password__startswith="sha1$").iterator()
    hasher = PBKDF2SHA1WrappedSHA1PasswordHasher()
    for user in users:
        algorithm, salt, sha1_hash = user.password.split("$", 2)
        user.password = hasher.encode_sha1_hash(sha1_hash, salt)
        user.save(update_fields=["password"])
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0037_alter_profile_keywords"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
