from django.db import migrations, models

# The old default, with a stray apostrophe that matches none of the field's own
# GROUP_CHOICES. Every GroupProfile created without an explicit access — which is
# what geonode_ldap's group mirroring does — was stored with this value.
BAD_DEFAULT = "public'"


def repair_access(apps, schema_editor):
    GroupProfile = apps.get_model("groups", "GroupProfile")
    GroupProfile.objects.filter(access=BAD_DEFAULT).update(access="public")


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0035_remove_modeltranslation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="groupprofile",
            name="access",
            field=models.CharField(
                choices=[
                    ("public", "Public"),
                    ("public-invite", "Public (invite-only)"),
                    ("private", "Private"),
                ],
                default="public",
                help_text="Public: Any registered user can view and join a public group.<br>Public (invite-only):Any registered user can view the group.  Only invited users can join.<br>Private: Registered users cannot see any details about the group, including membership.  Only invited users can join.",
                max_length=15,
                verbose_name="Access",
            ),
        ),
        # Reversing would mean writing the invalid value back, so this only goes
        # forward; the AlterField above is reversible on its own.
        migrations.RunPython(repair_access, migrations.RunPython.noop),
    ]
