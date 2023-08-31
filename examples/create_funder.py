# create funder example

import sys, os, django
sys.path.append("/") #here store is root folder(means parent).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "store.settings")
django.setup()

from geonode.base.models import FundingReference, Funder, ResourceBase

fr = FundingReference.objects.all()[0]
f = Funder( funding_reference=fr,
        award_number="25132", 
        award_uri="http://cordis.europa.eu/project/rcn/100180_en.html", 
        award_title="The human readable title of the award (grant). (e.g. MOTivational strength of ecosystem service)")

r = ResourceBase.objects.all()[0]
r.funders.add(f)
r.save()

