from django.db import migrations
from geonode.base.models import RestrictionCodeType

def fix_otherrestrictions_codetype(apps, schema_editor):
    """
    Fixes the identifier, description and gn_description for the 'otherRestrictions' RestrictionCodeType.
    """
    try:
        obj = RestrictionCodeType.objects.get(identifier='limitation not listed')
        obj.identifier = 'otherRestrictions'
        obj.description = 'limitation not listed'
        obj.gn_description = 'limitation not listed'
        obj.save()
    except RestrictionCodeType.DoesNotExist:
        pass



class Migration(migrations.Migration):

    dependencies = [
        ('base', '0093_alter_thesaurus_slug'),
    ]

    operations = [
        migrations.RunPython(fix_otherrestrictions_codetype,migrations.RunPython.noop),
    ]
    