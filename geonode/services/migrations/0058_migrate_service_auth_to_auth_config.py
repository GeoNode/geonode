import base64
import hashlib
import json

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import migrations


SECRET_KEY = settings.SECRET_KEY
ENCRYPTION_KEY = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
cipher = Fernet(ENCRYPTION_KEY)


def migrate_service_auth_to_auth_config(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    AuthConfig = apps.get_model("security", "AuthConfig")

    legacy_services = Service.objects.filter(
        username__isnull=False,
        password__isnull=False,
    )

    for service in legacy_services.iterator():
        raw_password = cipher.decrypt(service.password.encode()).decode()
        payload = json.dumps({"username": service.username, "password": raw_password})
        encrypted_payload = cipher.encrypt(payload.encode()).decode()

        auth_config = AuthConfig.objects.create(type="basic", payload=encrypted_payload)
        Service.objects.filter(pk=service.pk).update(auth_config=auth_config)


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0099_resourcebase_auth_config"),
        ("security", "0001_initial"),
        ("services", "0057_remove_modeltranslation"),
    ]

    operations = [
        migrations.RunPython(migrate_service_auth_to_auth_config, migrations.RunPython.noop),
    ]
