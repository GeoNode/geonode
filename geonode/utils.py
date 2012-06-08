import datetime
import os
import subprocess
import httplib2
import base64
import re
import math

from urlparse import urlparse
from UserDict import DictMixin
from ConfigParser import ConfigParser, NoOptionError

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils import simplejson as json
from owslib.wms import WebMapService
from owslib.csw import CatalogueServiceWeb

from geonode import GeoNodeException
#from geonode.layers.models import Layer
#from geonode.maps.models import Map
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.security.models import INVALID_PERMISSION_MESSAGE

_wms = None
_csw = None
_user, _password = settings.GEOSERVER_CREDENTIALS

http_client = httplib2.Http()
http_client.add_credentials(_user, _password)
http_client.add_credentials(_user, _password)
_netloc = urlparse(settings.GEOSERVER_BASE_URL).netloc
http_client.authorizations.append(
    httplib2.BasicAuthentication(
        (_user, _password),
        _netloc,
        settings.GEOSERVER_BASE_URL,
        {},
        None,
        None,
        http_client
    )
)

DEFAULT_TITLE=""
DEFAULT_ABSTRACT=""


def get_version(version=None):
    "Returns a PEP 386-compliant version number from VERSION."
    if version is None:
        from geonode import __version__ as version
    else:
        assert len(version) == 5
        assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        git_changeset = get_git_changeset()
        if git_changeset:
            sub = '.dev%s' % git_changeset

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub


def get_git_changeset():
    """Returns a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.
    """
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git_show = subprocess.Popen('git show --pretty=format:%ct --quiet HEAD',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=repo_dir, universal_newlines=True)
    timestamp = git_show.communicate()[0].partition('\n')[0]
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
    except ValueError:
        return None
    return timestamp.strftime('%Y%m%d%H%M%S')


def check_geonode_is_up():
    """Verifies all of geonetwork, geoserver and the django server are running,
       this is needed to be able to upload.
    """

    # try:
    #     Layer.objects.gs_catalog.get_workspaces()
    # except:
    #     msg = ('Cannot connect to the GeoServer at %s\nPlease make sure you '
    #            'have started GeoNode.' % settings.GEOSERVER_BASE_URL)
    #     raise GeoNodeException(msg)

    # try:
    #     Layer.objects.gn_catalog.login()
    # except:
    #     msg = ('Cannot connect to the GeoNetwork at %s\n'
    #            'Please make sure you have started '
    #            'GeoNetwork.' % settings.GEONETWORK_BASE_URL)
    #     raise GeoNodeException(msg)
    pass


def get_wms():
    global _wms
    wms_url = settings.GEOSERVER_BASE_URL + "wms?request=GetCapabilities&version=1.1.0"
    netloc = urlparse(wms_url).netloc
    http = httplib2.Http()
    http.add_credentials(_user, _password)
    http.authorizations.append(
        httplib2.BasicAuthentication(
            (_user, _password),
                netloc,
                wms_url,
                {},
                None,
                None,
                http
            )
        )
    body = http.request(wms_url)[1]
    _wms = WebMapService(wms_url, xml=body)
    return _wms

def get_csw():
    global _csw
    csw_url = "%ssrv/en/csw" % settings.GEONETWORK_BASE_URL
    _csw = CatalogueServiceWeb(csw_url)
    return _csw


def _get_basic_auth_info(request):
    """
    grab basic auth info
    """
    meth, auth = request.META['HTTP_AUTHORIZATION'].split()
    if meth.lower() != 'basic':
        raise ValueError
    username, password = base64.b64decode(auth).split(':')
    return username, password


def batch_permissions(request):
    """
    if not request.user.is_authenticated:
        return HttpResponse("You must log in to change permissions", status=401) 

    if request.method != "POST":
        return HttpResponse("Permissions API requires POST requests", status=405)

    spec = json.loads(request.raw_post_data)
    
    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        for lyr in lyrs:
            if not request.user.has_perm("maps.change_layer_permissions", obj=lyr):
                return HttpResponse("User not authorized to change layer permissions", status=403)

    if "maps" in spec:
        map_query = Map.objects.filter(pk__in = spec['maps'])
        for m in map_query:
            if not request.user.has_perm("maps.change_map_permissions", obj=m):
                return HttpResponse("User not authorized to change map permissions", status=403)

    anon_level = spec['permissions'].get("anonymous")
    auth_level = spec['permissions'].get("authenticated")
    users = spec['permissions'].get('users', [])
    user_names = [x[0] for x in users]

    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        valid_perms = ['layer_readwrite', 'layer_readonly']
        if anon_level not in valid_perms:
            anon_level = "_none"
        if auth_level not in valid_perms:
            auth_level = "_none"
        for lyr in lyrs:
            lyr.get_user_levels().exclude(user__username__in = user_names + [lyr.owner.username]).delete()
            lyr.set_gen_level(ANONYMOUS_USERS, anon_level)
            lyr.set_gen_level(AUTHENTICATED_USERS, auth_level)
            for user, user_level in users:
                if user_level not in valid_perms:
                    user_level = "_none"
                lyr.set_user_level(user, user_level)

    if "maps" in spec:
        map_query = Map.objects.filter(pk__in = spec['maps'])
        valid_perms = ['layer_readwrite', 'layer_readonly']
        if anon_level not in valid_perms:
            anon_level = "_none"
        if auth_level not in valid_perms:
            auth_level = "_none"
        anon_level = anon_level.replace("layer", "map")
        auth_level = auth_level.replace("layer", "map")

        for m in map_query:
            m.get_user_levels().exclude(user__username__in = user_names + [m.owner.username]).delete()
            m.set_gen_level(ANONYMOUS_USERS, anon_level)
            m.set_gen_level(AUTHENTICATED_USERS, auth_level)
            for user, user_level in spec['permissions'].get("users", []):
                user_level = user_level.replace("layer", "map")
                m.set_user_level(user, valid_perms.get(user_level, "_none"))

    return HttpResponse("Not implemented yet")
    """
    pass

def batch_delete(request):
    """
    if not request.user.is_authenticated:
        return HttpResponse("You must log in to delete layers", status=401) 

    if request.method != "POST":
        return HttpResponse("Delete API requires POST requests", status=405)

    spec = json.loads(request.raw_post_data)

    if "layers" in spec:
        lyrs = Layer.objects.filter(pk__in = spec['layers'])
        for lyr in lyrs:
            if not request.user.has_perm("maps.delete_layer", obj=lyr):
                return HttpResponse("User not authorized to delete layer", status=403)

    if "maps" in spec:
        map_query = Map.objects.filter(pk__in = spec['maps'])
        for m in map_query:
            if not request.user.has_perm("maps.delete_map", obj=m):
                return HttpResponse("User not authorized to delete map", status=403)

    if "layers" in spec:
        Layer.objects.filter(pk__in = spec["layers"]).delete()

    if "maps" in spec:
        Map.objects.filter(pk__in = spec["maps"]).delete()

    nlayers = len(spec.get('layers', []))
    nmaps = len(spec.get('maps', []))

    return HttpResponse("Deleted %d layers and %d maps" % (nlayers, nmaps))
    """
    pass

def _handle_perms_edit(request, obj):
    errors = []
    params = request.POST
    valid_pl = obj.permission_levels

    anon_level = params[ANONYMOUS_USERS]
    # validate anonymous level, disallow admin level
    if not anon_level in valid_pl or anon_level == obj.LEVEL_ADMIN:
        errors.append(_("Anonymous Users") + ": " + INVALID_PERMISSION_MESSAGE)

    all_auth_level = params[AUTHENTICATED_USERS]
    if not all_auth_level in valid_pl:
        errors.append(_("Registered Users") + ": " + INVALID_PERMISSION_MESSAGE)

    kpat = re.compile("^u_(.*)_level$")
    ulevs = {}
    for k, level in params.items():
        m = kpat.match(k)
        if m:
            username = m.groups()[0]
            if not level in valid_pl:
                errors.append(_("User") + " " + username + ": " + INVALID_PERMISSION_MESSAGE)
            else:
                ulevs[username] = level

    if len(errors) == 0:
        obj.set_gen_level(ANONYMOUS_USERS, anon_level)
        obj.set_gen_level(AUTHENTICATED_USERS, all_auth_level)

        for username, level in ulevs.items():
            user = User.objects.get(username=username)
            obj.set_user_level(user, level)

    return errors


def _split_query(query):
    """
    split and strip keywords, preserve space 
    separated quoted blocks.
    """

    qq = query.split(' ')
    keywords = []
    accum = None
    for kw in qq:
        if accum is None:
            if kw.startswith('"'):
                accum = kw[1:]
            elif kw:
                keywords.append(kw)
        else:
            accum += ' ' + kw
            if kw.endswith('"'):
                keywords.append(accum[0:-1])
                accum = None
    if accum is not None:
        keywords.append(accum)
    return [kw.strip() for kw in keywords if kw.strip()]


def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID=%s;POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))' % (srid,
                            x0, y0, x0, y1, x1, y1, x1, y0, x0, y0)


def forward_mercator(lonlat):
    """
        Given geographic coordinates, return a x,y tuple in spherical mercator.
        
        If the lat value is out of range, -inf will be returned as the y value
    """
    x = lonlat[0] * 20037508.34 / 180
    n = math.tan((90 + lonlat[1]) * math.pi / 360)
    if n <= 0:
        y = float("-inf")
    else:
        y = math.log(n) / math.pi * 20037508.34
    return (x, y)


def inverse_mercator(xy):
    """
        Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / 20037508.34) * 180
    lat = (xy[1] / 20037508.34) * 180
    lat = 180/math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return (lon, lat)


def layer_from_viewer_config(model, layer, source, ordering):
    """
    Parse an object out of a parsed layer configuration from a GXP
    viewer.

    ``model`` is the type to instantiate
    ``layer`` is the parsed dict for the layer
    ``source`` is the parsed dict for the layer's source
    ``ordering`` is the index of the layer within the map's layer list
    """
    layer_cfg = dict(layer)
    for k in ["format", "name", "opacity", "styles", "transparent",
                "fixed", "group", "visibility", "title", "source"]:
        if k in layer_cfg: del layer_cfg[k]

    source_cfg = dict(source)
    for k in ["url", "projection"]:
        if k in source_cfg: del source_cfg[k]

    return model(
        stack_order = ordering,
        format = layer.get("format", None),
        name = layer.get("name", None),
        opacity = layer.get("opacity", 1),
        styles = layer.get("styles", None),
        transparent = layer.get("transparent", False),
        fixed = layer.get("fixed", False),
        group = layer.get('group', None),
        visibility = layer.get("visibility", True),
        ows_url = source.get("url", None),
        layer_params = json.dumps(layer_cfg),
        source_params = json.dumps(source_cfg)
    )


class GXPMapBase(object):
    
    def viewer_json(self, *added_layers):
        """
        Convert this map to a nested dictionary structure matching the JSON
        configuration for GXP Viewers.

        The ``added_layers`` parameter list allows a list of extra MapLayer
        instances to append to the Map's layer list when generating the
        configuration. These are not persisted; if you want to add layers you
        should use ``.layer_set.create()``.
        """
        
        layers = list(self.layers)
        layers.extend(added_layers)
        
        server_lookup = {}
        sources = {'local': settings.DEFAULT_LAYER_SOURCE }

        def uniqify(seq):
            """
            get a list of unique items from the input sequence.
            
            This relies only on equality tests, so you can use it on most
            things.  If you have a sequence of hashables, list(set(seq)) is
            better.
            """
            results = []
            for x in seq:
                if x not in results: results.append(x)
            return results

        configs = [l.source_config() for l in layers]

        i = 0
        for source in uniqify(configs):
            while str(i) in sources: i = i + 1
            sources[str(i)] = source 
            server_lookup[json.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source: return k
            return None

        def layer_config(l):
            cfg = l.layer_config()
            src_cfg = l.source_config()
            source = source_lookup(src_cfg)
            if source: cfg["source"] = source
            return cfg
        
        config = {
            'id': self.id,
            'about': {
                'title':    self.title,
                'abstract': self.abstract
            },
            'defaultSourceType': "gxp_wmscsource",
            'sources': sources,
            'map': {
                'layers': [layer_config(l) for l in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom
            }
        }

        # Mark the last added layer as selected - important for data page
        config["map"]["layers"][len(layers)-1]["selected"] = True

        config["map"].update(_get_viewer_projection_info(self.projection))

        return config
    
    
class GXPMap(GXPMapBase):
    
    def __init__(self, projection=None, title=None, abstract=None, 
                 center_x = None, center_y = None, zoom = None):
        self.id = 0
        self.projection = projection
        self.title = title or DEFAULT_TITLE
        self.abstract = abstract or DEFAULT_ABSTRACT
        _DEFAULT_MAP_CENTER = forward_mercator(settings.DEFAULT_MAP_CENTER)
        self.center_x = center_x if center_x is not None else _DEFAULT_MAP_CENTER[0]
        self.center_y = center_y if center_y is not None else _DEFAULT_MAP_CENTER[1]
        self.zoom = zoom if zoom is not None else settings.DEFAULT_MAP_ZOOM
        self.layers = []


class GXPLayerBase(object):
    
    def source_config(self):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = json.loads(self.source_params)
        except Exception:
            cfg = dict(ptype="gxp_wmscsource", restUrl="/gs/rest")

        if self.ows_url: cfg["url"] = self.ows_url

        return cfg

    def layer_config(self):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """
        try:
            cfg = json.loads(self.layer_params)
        except Exception: 
            cfg = dict()

        if self.format: cfg['format'] = self.format
        if self.name: cfg["name"] = self.name
        if self.opacity: cfg['opacity'] = self.opacity
        if self.styles: cfg['styles'] = self.styles
        if self.transparent: cfg['transparent'] = True

        cfg["fixed"] = self.fixed
        if self.group: cfg["group"] = self.group
        cfg["visibility"] = self.visibility

        return cfg
    

class GXPLayer(GXPLayerBase):
    '''GXPLayer represents an object to be included in a GXP map.
    '''
    def __init__(self, name=None, ows_url=None, **kw):
        self.format = None
        self.name = name
        self.opacity = 1.0
        self.styles = None
        self.transparent = False
        self.fixed = False
        self.group = None
        self.visibility = True
        self.ows_url = ows_url
        self.layer_params = ""
        self.source_params = ""
        for k in kw:
            setattr(self,k,kw[k])        


def default_map_config():
    _DEFAULT_MAP_CENTER = forward_mercator(settings.DEFAULT_MAP_CENTER)

    _default_map = GXPMap(
        title=DEFAULT_TITLE, 
        abstract=DEFAULT_ABSTRACT,
        projection="EPSG:900913",
        center_x=_DEFAULT_MAP_CENTER[0],
        center_y=_DEFAULT_MAP_CENTER[1],
        zoom=settings.DEFAULT_MAP_ZOOM
    )
    def _baselayer(lyr, order):
        return layer_from_viewer_config(
            GXPLayer,
            layer = lyr,
            source = lyr["source"],
            ordering = order
        )

    DEFAULT_BASE_LAYERS = [_baselayer(lyr, idx) for idx, lyr in enumerate(settings.MAP_BASELAYERS)]
    DEFAULT_MAP_CONFIG = _default_map.viewer_json(*DEFAULT_BASE_LAYERS)

    return DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS


_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.03390625,
        "units": "m",
        "maxExtent": [-20037508.34,-20037508.34,20037508.34,20037508.34],
    },
    "EPSG:4326": {
        "max_resolution": (180 - (-180)) / 256,
        "units": "degrees",
        "maxExtent": [-180, -90, 180, 90]
    }
}


def _get_viewer_projection_info(srid):
    # TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})
