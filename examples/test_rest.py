import sys, os, django
sys.path.append("/") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store.settings")
django.setup()

import io
from rest_framework.renderers import JSONRenderer
from geonode.base.models import ResourceBase
from geonode.base.api.serializers import ResourceBaseSerializer
from rest_framework.parsers import JSONParser

r = ResourceBase.objects.all()[0]
s = ResourceBaseSerializer(r)
json = JSONRenderer().render(s.data)
stream = io.BytesIO(json)
data = JSONParser().parse(stream)
se = ResourceBaseSerializer(data=data)
se.is_valid()
