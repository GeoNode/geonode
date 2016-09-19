import random
from django.http import HttpResponse
from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlsplit
import httplib2
import urllib
from django.utils import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
import logging
from urlparse import urlparse
from geonode.maps.models import LayerStats, Layer
from xml.etree.ElementTree import XML, ParseError
import re

logger = logging.getLogger("geonode.proxy.views")

HGL_URL = 'http://hgl.harvard.edu:8080/HGL'

_valid_tags = "\{http\:\/\/www\.opengis\.net\/wms\}WMS_Capabilities|\
WMT_MS_Capabilities|WMS_DescribeLayerResponse|\
\{http\:\/\/www\.opengis\.net\/gml\}FeatureCollection|msGMLOutput|\
\{http\:\/\/www.opengis\.net\/wfs\}FeatureCollection|\
rss|{http://www.w3.org/2005/Atom}feed|\
\{http\:\/\/www\.w3\.org\/2001\/XMLSchema\}schema|\
{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF"

_user, _password = settings.GEOSERVER_CREDENTIALS
h = httplib2.Http()
h.add_credentials(_user, _password)
_netloc = urlparse(settings.GEOSERVER_BASE_URL).netloc
h.authorizations.append(
    httplib2.BasicAuthentication(
        (_user, _password),
        _netloc,
        settings.GEOSERVER_BASE_URL,
            {},
        None,
        None,
        h
    )
)

@csrf_exempt
def proxy(request):
    if 'url' not in request.GET:
        return HttpResponse(
                "The proxy service requires a URL-encoded URL as a parameter.",
                status=400,
                content_type="text/plain"
                )

    url = urlsplit(request.GET['url'])

    # Don't allow localhost connections unless in DEBUG mode
    if not settings.DEBUG and re.search('localhost|127.0.0.1', url.hostname):
        return HttpResponse(status=403)

    locator = url.path
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    # Strip all headers and cookie info
    headers = {}


    conn = HTTPConnection(url.hostname, url.port) if url.scheme == "http" else HTTPSConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.raw_post_data, headers)
    result = conn.getresponse()

    response = HttpResponse(
            valid_response(result.read()),
            status=result.status,
            content_type=result.getheader("Content-Type", "text/plain")
            )

    return response


def valid_response(responseContent):
    #Proxy should only be used when expecting an XML or JSON response

    #ArcGIS Server GetFeatureInfo xml response
    if re.match("<FeatureInfoResponse", responseContent):
        return responseContent

    # ows exceptions
    if "<ows:ExceptionReport" in responseContent:
        return responseContent

    if responseContent[0] == "<":
        try:
            from defusedxml.ElementTree import fromstring
            et = fromstring(responseContent)
            if re.match(_valid_tags, et.tag):
                return responseContent
        except ParseError:
            return None
    elif re.match('\[|\{', responseContent):
        try:
            json.loads(responseContent)
            return responseContent
        except:
            return None
    return None



@csrf_exempt
def geoserver_rest_proxy(request, proxy_path, downstream_path):
    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            mimetype="text/plain",
            status=401)

    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)
    url = "".join([settings.GEOSERVER_BASE_URL, downstream_path, path])

    http = httplib2.Http()
    http.add_credentials(*settings.GEOSERVER_CREDENTIALS)
    headers = dict()

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    response, content = http.request(
        url, request.method,
        body=request.raw_post_data or None,
        headers=headers)

    return HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))


def picasa(request):
    url = "http://picasaweb.google.com/data/feed/base/all?thumbsize=160c&"
    kind = request.GET['kind'] if request.method == 'GET' else request.POST['kind']
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    coords = bbox.split(",")
    coords[0] = -180 if float(coords[0]) <= -180 else coords[0]
    coords[2] = 180 if float(coords[2])  >= 180 else coords[2]
    coords[1] = coords[1] if float(coords[1]) > -90 else -90
    coords[3] = coords[3] if float(coords[3])  < 90 else 90
    newbbox = str(coords[0]) + ',' + str(coords[1]) + ',' + str(coords[2]) + ',' + str(coords[3])
    url = url + "kind=" + kind + "&max-results=" + maxResults + "&bbox=" + newbbox + "&q=" + urllib.quote(query.encode('utf-8'))  #+ "&alt=json"

    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")


def flickr(request):
    url = "http://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=%s" % settings.FLICKR_API_KEY
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    coords = bbox.split(",")
    coords[0] = -180 if float(coords[0]) <= -180 else coords[0]
    coords[2] = 180 if float(coords[2])  >= 180 else coords[2]
    coords[1] = coords[1] if float(coords[1]) > -90 else -90
    coords[3] = coords[3] if float(coords[3])  < 90 else 90
    newbbox = str(coords[0]) + ',' + str(coords[1]) + ',' + str(coords[2]) + ',' + str(coords[3])
    url = url + "&tags=%s&per_page=%s&has_geo=1&bbox=%s&format=json&extras=geo,url_q&accuracy=1&nojsoncallback=1" % (query,maxResults,newbbox)
    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")


def hglpoints (request):
    from xml.dom import minidom
    import re
    url = HGL_URL + "/HGLGeoRSS?GeometryType=point"
    bbox = ["-180","-90","180","90"]
    max_results = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    if max_results is None:
        max_results = "100"
    try:
        bbox = request.GET['bbox'].split(",") if request.method == 'GET' else request.POST['bbox'].split(",")
    except:
        pass
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    url = url + "&UserQuery=" + urllib.quote(query.encode('utf-8')) #+ \
        #"&BBSearchOption=1&minx=" + bbox[0] + "&miny=" + bbox[1] + "&maxx=" + bbox[2] + "&maxy=" + bbox[3]
    dom = minidom.parse(urllib.urlopen(url))
    iterator = 1
    for node in dom.getElementsByTagName('item'):
        if iterator <= int(max_results):
            description = node.getElementsByTagName('description')[0]
            guid = node.getElementsByTagName('guid')[0]
            title = node.getElementsByTagName('title')[0]
            if guid.firstChild.data != 'OWNER.TABLE_NAME':
                description.firstChild.data = description.firstChild.data + '<br/><br/><p><a href=\'javascript:void(0);\' onClick=\'app.addHGL("' \
                    + escape(title.firstChild.data) + '","' + re.sub("SDE\d?\.","", guid.firstChild.data)  + '");\'>Add to Map</a></p>'
            iterator +=1
        else:
            node.parentNode.removeChild(node)

    return HttpResponse(dom.toxml(), mimetype="text/xml")


def hglServiceStarter (request, layer):
    #Check if the layer is accessible to public, if not return 403
    accessUrl = HGL_URL + "/ogpHglLayerInfo.jsp?ValidationKey=" + settings.HGL_VALIDATION_KEY +"&layers=" + layer
    accessJSON = json.loads(urllib.urlopen(accessUrl).read())
    if accessJSON[layer]['access'] == 'R':
        return HttpResponse(status=403)

    #Call the RemoteServiceStarter to load the layer into HGL's Geoserver in case it's not already there
    startUrl = HGL_URL + "/RemoteServiceStarter?ValidationKey=" + settings.HGL_VALIDATION_KEY + "&AddLayer=" + layer
    return HttpResponse(urllib.urlopen(startUrl).read())

def tweetServerProxy(request,geopsip):
    url = urlsplit(request.get_full_path())
    if geopsip == "standard":
        geopsip = settings.GEOPS_IP
    tweet_url = "http://" + geopsip + "?" + url.query

    identifyQuery = re.search("QUERY_LAYERS", tweet_url)

    if identifyQuery is not None:
        if re.search("%20limit%2010&", tweet_url)is None:
            return HttpResponse(status=403)

    step1 = urllib.urlopen(tweet_url)
    step2 = step1.read()
    if 'content-type' in step1.info().dict:
        response = HttpResponse(step2, mimetype= step1.info().dict['content-type'])
    else:
        response = HttpResponse(step2)
    try :
        cookie = step1.info().dict['set-cookie'].split(";")[0].split("=")[1]
        response.set_cookie("tweet_count", cookie)
    except:
        pass
    return response


def tweetDownload (request):

    if (not request.user.is_authenticated() or  not request.user.get_profile().is_org_member):
        return HttpResponse(status=403)

    proxy_url = urlsplit(request.get_full_path())
    download_url = "http://" + settings.GEOPS_IP + "?" + proxy_url.query  + settings.GEOPS_DOWNLOAD

    http = httplib2.Http()
    response, content = http.request(
        download_url, request.method)

    response =  HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))

    response['Content-Disposition'] = response.get('Content-Disposition', 'attachment; filename="tweets"' + request.user.username + '.csv');
    return response



def tweetTrendProxy (request):

    tweetUrl = "http://" + settings.AWS_INSTANCE_IP + "/?agg=trend&bounds=" + request.POST["bounds"] + "&dateStart=" + request.POST["dateStart"] + "&dateEnd=" + request.POST["dateEnd"];
    resultJSON =""
#    resultJSON = urllib.urlopen(tweetUrl).read()
#    import datetime
#
#
#    startDate = datetime.datetime.strptime(request.POST["dateStart"], "%Y-%b-%d")
#    endDate = datetime.datetime.strptime(request.POST["dateEnd"], "%Y-%b-%d")
#
#    recString = "record: ["
#
#    while startDate <= endDate:
#            recString += "{'date': '$date', 'Ebola$rnd5' : $rnd6, 'Malaria$rnd4' : $rnd7, 'Influenza$rnd3': $rnd8, 'Plague$rnd3': $rnd9, 'Lyme_Disease$rnd1': $rnd10},"
#            recString = recString.replace("$rnd6", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd7", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd8", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd9", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd10", str(random.randrange(50,500,1)))
#            recString = recString.replace("$date", datetime.datetime.strftime(startDate, '%b-%d-%Y'))
#            startDate = startDate + datetime.timedelta(days=1)
#
#    recString += "]"
#
#    resultJSON = """
#    {
#    metaData: {
#        root: "record",
#        fields: [
#            {name: 'date'},
#            {name: 'Ebola$rnd5'},
#            {name: 'Malaria$rnd4'},
#            {name: 'Influenza$rnd3'},
#            {name: 'Plague$rnd3'},
#            {name: 'Lyme_Disease$rnd1'}
#        ],
#    },
#    // Reader's configured root
#    $recString
#}
#"""
#
#    resultJSON = resultJSON.replace("$recString", recString)
#
#
#
#    resultJSON = resultJSON.replace("$rnd1", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd2", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd3", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd4", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd5", str(random.randrange(50,500,1)))

#    resultJSON = '{"metaData":{"fields":[{"name":"Tuberculosis"},{"name":"STD"},{"name":"Gastroenteritis"},{"name":"Influenza"},{"name":"Common_Cold"},{"name":"date"}],"root":"record"},"record":[{"Common_Cold":18,"Gastroenteritis":104,"Influenza":76,"STD":121,"Tuberculosis":236,"date":"2012-01-26"},{"Common_Cold":19,"Gastroenteritis":115,"Influenza":114,"STD":146,"Tuberculosis":397,"date":"2012-01-27"},{"Common_Cold":26,"Gastroenteritis":104,"Influenza":83,"STD":137,"Tuberculosis":402,"date":"2012-01-28"},{"Common_Cold":25,"Gastroenteritis":96,"Influenza":76,"STD":141,"Tuberculosis":358,"date":"2012-01-29"},{"Common_Cold":30,"Gastroenteritis":106,"Influenza":87,"STD":158,"Tuberculosis":372,"date":"2012-01-30"},{"Common_Cold":12,"Gastroenteritis":74,"Influenza":44,"STD":116,"Tuberculosis":222,"date":"2012-01-31"}]}'

    return HttpResponse(resultJSON, mimetype="application/json")


def youtube(request):
    url = "http://gdata.youtube.com/feeds/api/videos?v=2&prettyprint=true&"
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    coords = bbox.split(",")
    coords[0] = coords[0] if float(coords[0]) > -180 else -180
    coords[2] = coords[2] if float(coords[2])  < 180 else 180
    coords[1] = coords[1] if float(coords[1]) > -90 else -90
    coords[3] = coords[3] if float(coords[3])  < 90 else 90
    #location would be the center of the map.
    location = str((float(coords[3]) + float(coords[1]))/2)  + "," + str((float(coords[2]) + float(coords[0]))/2);

    #calculating the location-readius
    R = 6378.1370;
    PI = 3.1415926;
    left = R*float(coords[0])/180.0/PI;
    right = R*float(coords[2])/180.0/PI;
    radius = (right - left)/2*2;
    radius = 1000 if (radius > 1000) else radius;
    url = url + "location=" + location + "&max-results=" + maxResults + "&location-radius=" + str(radius) + "km&q=" + urllib.quote(query.encode('utf-8'))

    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")

def download(request, service, layer, format):
    params = request.GET
    #mimetype = params.get("outputFormat") if service == "wfs" else params.get("format")

    service=service.replace("_","/")
    url = settings.GEOSERVER_BASE_URL + service + "?" + params.urlencode()

    layerObj = Layer.objects.get(pk=layer)

    if layerObj.downloadable and request.user.has_perm('maps.view_layer', obj=layerObj):

        layerstats,created = LayerStats.objects.get_or_create(layer=layer)
        layerstats.downloads += 1
        layerstats.save()

        download_response, content = h.request(
            url, request.method,
            body=None,
            headers=dict())
        content_disposition = None
        if 'content_disposition' in download_response:
            content_disposition = download_response['content-disposition']
        mimetype = download_response['content-type']
        response = HttpResponse(content, mimetype = mimetype)
        if content_disposition is not None:
            response['Content-Disposition'] = content_disposition
        else:
            response['Content-Disposition'] = "attachment; filename=" + layerObj.name + "." + format
        return response
    else:
        return HttpResponse(status=403)
