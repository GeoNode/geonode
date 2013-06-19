#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.core.management.base import BaseCommand

from geonode.base.models import TopicCategory

class Command(BaseCommand):
    help = ("Updates the layers, maps and documents counts for Topic Categories"
            "based on the resources available in the database")

    def handle(self, *args, **options):
        
        for cat in TopicCategory.objects.all():
            counts = {
                'layers': 0,
                'maps': 0,
                'documents': 0
                }
            for rbase in cat.resourcebase_set.all():
                try:
                    rbase.layer
                    counts['layers'] += 1
                except:
                    pass
                try: 
                    rbase.map
                    counts['maps'] += 1
                except:
                    pass
                try:
                    rbase.document
                    counts['documents'] += 1
                except: 
                    pass

            cat.layers_count = counts['layers']
            cat.maps_count = counts['maps']
            cat.documents_count = counts['documents']
            cat.save()
            print 'Processed category: %s' % cat
            print '    layers: %s' %  counts['layers']
            print '    maps: %s' %  counts['maps']
            print '    documents: %s' %  counts['documents']