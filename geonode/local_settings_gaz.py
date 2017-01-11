# additional settings for RDF triplestore.

# needs SITEURL defined
# how best to pick this up?
# but leave it free to have a separate server for RDF!
SITEURL='http://cfdev.intersect.org.au/'

RDFSERVER="".join((SITEURL[:-1],":8080"))
    
GAZ_APPS = (
   
    # gazetteer and linked data elements
    'rdf_io',
    'skosxl',
    'gazetteer',
    'uriredirect',

    # Django d3 example
    'd3ex',
    'play',

    # polls tutorial
    'polls',
)

from settings import INSTALLED_APPS
# print 'After import in local_settings_gaz, INSTALLED_APPS:', INSTALLED_APPS
INSTALLED_APPS += GAZ_APPS
# print 'At end of local_settings_gaz, INSTALLED_APPS:', INSTALLED_APPS

# RDF triplestore settings
RDFSTORE_RDF4J = {
    'default' : {
        'server' : "".join((RDFSERVER,"/rdf4j-server/repositories/gaz" )),
        'server_api' : "RDF4JREST",
        # model and slug are special - slug will revert to id if not present
        'target' : "/statements?context=<{model}>",
        # this should be pulled from settings
        'sparql' : "".join((RDFSERVER,"/rdf4j-server/repositories/gaz" ))
        },
    'scheme' : {
        'target' : "/statements?context=<{uri}>",
#        'headers' : { 'Slug' : "{slug}" }
        },
    'concept' : {
        'target' : "/statements?context=<{scheme__uri}/{term}>",
#        'headers' : { 'Slug' : "{term}" }
        }
}

RDFSTORE = RDFSTORE_RDF4J
