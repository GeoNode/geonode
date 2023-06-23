
import sys, os, django
sys.path.append("/") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store.settings")
django.setup()

from geonode.base.models import RelationType, RelatedIdentifier, ResourceBase, RelatedIdentifierType

rt = RelationType.objects.all()[0]
rit = RelatedIdentifierType.objects.all()[0]
ri = RelatedIdentifier.objects.create(related_identifier="test",
                                 related_identifier_type=rit,
                                 relation_type=rt
                                 )
rb = ResourceBase.objects.all()[0]
rb.related_identifier.add(ri)