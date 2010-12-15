from itertools import cycle, izip
import logging
import re
from django.db import transaction
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from geonode.maps.models import Map, Layer, MapLayer, Contact, ContactRole,Role, get_csw
import geoserver
from geoserver.resource import FeatureType, Coverage
import uuid

logger = logging.getLogger("geonode.maps.gs_helpers")

_punc = re.compile(r"[\.:]") #regex for punctuation that confuses restconfig
_foregrounds = ["#ffbbbb", "#bbffbb", "#bbbbff", "#ffffbb", "#bbffff", "#ffbbff"]
_backgrounds = ["#880000", "#008800", "#000088", "#888800", "#008888", "#880088"]
_marks = ["square", "circle", "star", "cross", "x", "triangle"]
_style_contexts = izip(cycle(_foregrounds), cycle(_backgrounds), cycle(_marks))

def _add_sld_boilerplate(symbolizer):
    """
    Wrap an XML snippet representing a single symbolizer in the approperiate
    elements to make it a valid SLD which applies that symbolizer to all features,
    including format strings to allow interpolating a "name" variable in.
    """
    return """
<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>%(name)s</Name>
    <UserStyle>
    <Name>%(name)s</Name>
      <FeatureTypeStyle>
        <Rule>
""" + symbolizer + """
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
"""

_raster_template = """
<RasterSymbolizer>
    <Opacity>1.0</Opacity>
</RasterSymbolizer>
"""

_polygon_template = """
<PolygonSymbolizer>
  <Fill>
    <CssParameter name="fill">%(bg)s</CssParameter>
  </Fill>
  <Stroke>
    <CssParameter name="stroke">%(fg)s</CssParameter>
  </Stroke>
</PolygonSymbolizer>
"""

_line_template = """
<LineSymbolizer>
  <Stroke>
    <CssParameter name="stroke">%(bg)s</CssParameter>
  </Stroke>
</LineSymbolizer>
<LineSymbolizer>
  <Stroke>
    <CssParameter name="stroke">%(fg)s</CssParameter>
    <CssParameter name="stroke-dasharray">2 2</CssParameter>
  </Stroke>
</LineSymbolizer>
"""

_point_template = """
<PointSymbolizer>
  <Graphic>
    <Mark>
      <WellKnownName>%(mark)s</WellKnownName>
      <Fill>
        <CssParameter name="fill">%(bg)s</CssParameter>
      </Fill>
      <Stroke>
        <CssParameter name="stroke">%(fg)s</CssParameter>
      </Stroke>
    </Mark>
    <Size>10</Size>
  </Graphic>
</PointSymbolizer>
"""

_style_templates = dict(
    raster = _add_sld_boilerplate(_raster_template),
    polygon = _add_sld_boilerplate(_polygon_template),
    line = _add_sld_boilerplate(_line_template),
    point = _add_sld_boilerplate(_point_template)
)

def _style_name(resource):
    return _punc.sub("_", resource.store.workspace.name + ":" + resource.name)

def fixup_style(cat, resource):
    logger.debug("Creating styles for layers associated with [%s]", resource)
    layers = cat.get_layers(resource=resource)
    logger.info("Found %d layers associated with [%s]", resource)
    for lyr in layers:
        if lyr.default_style.name in _style_templates:
            logger.info("%s uses a default style, generating a new one", lyr)
            name = _style_name(resource)
            fg, bg, mark = _style_contexts.next()
            sld = _style_templates[lyr.default_style.name] % dict(name=name, fg=fg, bg=bg, mark=mark)
            logger.info("Creating style [%s]", name)
            style = cat.create_style(name, sld)
            lyr.default_style = cat.get_style(name)
            logger.info("Saving changes to %s", lyr)
            cat.save(lyr)
            logger.info("Successfully updated %s", lyr)

GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

@transaction.commit_manually
def _handle_layer_upload(layer_name=None, base_file=None, dbf_file=None, shx_file=None, prj_file=None, user=None, layer=None):
    """
    handle upload of layer data. if specified, the layer given is 
    overwritten, otherwise a new layer is created.
    """

    logger.info("Uploaded layer: [%s], base filename: [%s]", layer_name, base_file)

    try:
        user = User.objects.get(username=user)
    except Exception:
        logger.warn("Invalid User")
        return None, [_("You must specify a valid user to upload.")]

    if not base_file:
        logger.warn("Failed upload: no basefile provided")
        return None, [_("You must specify a layer data file to upload.")]
    
    if layer is None:
        overwrite = False
        # XXX Give feedback instead of just replacing name
        xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")
        name = xml_unsafe.sub("_", layer_name)
        proposed_name = name
        count = 1
        while Layer.objects.filter(name=proposed_name).count() > 0:
            proposed_name = "%s_%d" % (name, count)
            count = count + 1
        name = proposed_name
        logger.info("Requested name already used; adjusting name [%s] => [%s]", layer_name, name)
    else:
        overwrite = True
        name = layer.name
        logger.info("Using name as requested")

    errors = []
    cat = Layer.objects.gs_catalog
    
    if not name:
        logger.error("Unexpected error: Layer name passed validation but is falsy: %s", name)
        return None, [_("Unable to determine layer name.")]

    # shapefile upload
    elif base_file.name.lower().endswith('.shp'):
        logger.info("Upload [%s] appears to be a Shapefile", base_file)
        # check that we are uploading the same resource 
        # type as the existing resource.
        if layer is not None:
            logger.info("Checking whether layer being replaced is a raster layer")
            info = cat.get_resource(name, store=cat.get_store(name))
            if info.resource_type != FeatureType.resource_type:
                logger.info("User tried to replace raster layer [%s] with Shapefile (vector) data", name)
                return None, [_("This resource may only be replaced with raster data.")]
        
        create_store = cat.create_featurestore
        
        if not dbf_file: 
            logger.info("User tried to upload [%s] without a .dbf file", base_file)
            errors.append(_("You must specify a .dbf file when uploading a shapefile."))
        if not shx_file: 
            logger.info("User tried to upload [%s] without a .shx file", base_file)
            errors.append(_("You must specify a .shx file when uploading a shapefile."))

        if not prj_file:
            logger.info("User tried to upload [%s] without a .prj file", base_file)

        if errors:
            return None, errors
        
        # ... bundle the files together and send them along
        cfg = {
            'shp': base_file,
            'dbf': dbf_file,
            'shx': shx_file
        }
        if prj_file:
            cfg['prj'] = prj_file
    
    # any other type of upload
    else:
        logger.info("Upload [%s] appears not to be a Shapefile", base_file)
        if layer is not None:
            logger.info("Checking whether replacement data for [%s] is raster", name)
            info = cat.get_resource(name, store=cat.get_store(name))
            if info.resource_type != Coverage.resource_type:
                logger.warn("User tried to replace vector layer [%s] with raster data", name)
                return [_("This resource may only be replaced with shapefile data.")]

        # ... we attempt to let geoserver figure it out, guessing it is coverage 
        create_store = cat.create_coveragestore
        cfg = base_file
    
    logger.debug(cfg)

    try:
        logger.debug("Starting upload of [%s] to GeoServer...", name)
        create_store(name, cfg, overwrite=overwrite)
        logger.debug("Finished upload of [%s] to GeoServer...", name)
    except geoserver.catalog.UploadError, e:
        logger.warn("Upload failed with error: %s", str(e))
        errors.append(_("An error occurred while loading the data."))
        tmp = cat.get_store(name)
        if tmp:
            logger.info("Deleting store after failed import of [%s] into GeoServer", name)
            cat.delete(tmp)
            logger.info("Successful deletion after failed import of [%s] into GeoServer", name)
    except geoserver.catalog.ConflictingDataError:
        errors.append(_("There is already a layer with the given name."))


    # if we successfully created the store in geoserver...
    if len(errors) == 0 and layer is None:
        logger.info("Succesful import of [%s] to GeoServer. Generating metadata", name)
        gs_resource = None
        csw_record = None
        layer = None
        try:
            gs_resource = cat.get_resource(name=name, store=cat.get_store(name=name))

            if gs_resource.latlon_bbox is None:
                logger.warn("GeoServer failed to detect the projection for layer [%s]. Guessing EPSG:4326", name)
                # If GeoServer couldn't figure out the projection, we just
                # assume it's lat/lon to avoid a bad GeoServer configuration

                gs_resource.latlon_bbox = gs_resource.native_bbox
                gs_resource.projection = "EPSG:4326"
                cat.save(gs_resource)

            typename = gs_resource.store.workspace.name + ':' + gs_resource.name
            logger.info("Got GeoServer info for %s, creating Django record", typename)

            # if we created a new store, create a new layer
            layer = Layer.objects.create(name=gs_resource.name, 
                                         store=gs_resource.store.name,
                                         storeType=gs_resource.store.resource_type,
                                         typename=typename,
                                         workspace=gs_resource.store.workspace.name,
                                         title=gs_resource.title,
                                         uuid=str(uuid.uuid1()),
                                         owner=user
                                       )
            # A user without a profile might be uploading this
            poc_contact, __ = Contact.objects.get_or_create(user=user,
                                                   defaults={"name": user.username })
            author_contact, __ = Contact.objects.get_or_create(user=user,
                                                   defaults={"name": user.username })
            logger.info("poc and author set to %s", poc_contact)
            layer.poc = poc_contact
            layer.metadata_author = author_contact
            logger.debug("committing DB changes for %s", typename)
            layer.save()
            logger.debug("Setting default permissions for %s", typename)
            layer.set_default_permissions()
            logger.debug("Generating separate style for %s", typename)
            fixup_style(cat, gs_resource)
        except Exception, e:
            logger.exception("Import to Django and GeoNetwork failed: %s", str(e))
            transaction.rollback()
            # Something went wrong, let's try and back out any changes
            if gs_resource is not None:
                logger.warning("no explicit link from the resource to [%s], bah", name)
                gs_layer = cat.get_layer(gs_resource.name) 
                store = gs_resource.store
                try:
                    cat.delete(gs_layer)
                except:
                    pass

                try: 
                    cat.delete(gs_resource)
                except:
                    pass

                try: 
                    cat.delete(store)
                except:
                    pass
            if csw_record is not None:
                logger.warning("Deleting dangling GeoNetwork record for [%s] (no Django record to match)", name)
                try:
                    gn.delete(csw_record)
                except:
                    pass
            # set layer to None, but we'll rely on db transactions instead
            # of a manual delete to keep it out of the db
            layer = None
            logger.warning("Finished cleanup after failed GeoNetwork/Django import for layer: %s", name)
            errors.append(GENERIC_UPLOAD_ERROR)
        else:
            transaction.commit()

    return layer, errors
