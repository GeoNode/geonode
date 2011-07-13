package org.geonode.rest.coveragestats;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.apache.commons.io.IOUtils;
import org.geonode.geojson.GeoJSONParser;
import org.geonode.geojson.GeoJSONSerializer;
import org.geonode.process.coveragestats.HazardStatisticsFactory;
import org.geoserver.catalog.AttributeTypeInfo;
import org.geoserver.catalog.Catalog;
import org.geoserver.catalog.CoverageInfo;
import org.geoserver.catalog.FeatureTypeInfo;
import org.geoserver.catalog.LayerInfo;
import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.data.FeatureSource;
import org.geotools.factory.GeoTools;
import org.geotools.factory.Hints;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.util.NullProgressListener;
import org.geotools.util.logging.Logging;
import org.opengis.feature.Feature;
import org.opengis.feature.type.FeatureType;
import org.opengis.util.ProgressListener;
import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.Representation;
import org.restlet.resource.StringRepresentation;

import com.vividsolutions.jts.geom.Geometry;

/**
 * Handles a POST request containing a geometry, buffer radius, and data layers for which to create
 * and return a set of statistics in JSON format by intersecting the layers with a buffered geometry
 * out of the provided input geometry and radius.
 * <p>
 * Expects the following (Geo)JSON inputs:
 * <ul>
 * <li>{@code politicalLayer}: Optional, name of the layer to gather political intersection with the
 * provided input geometry (once buffered). If not provided then no political layer intersection
 * results will be returned
 * <li>{@code politicalLayerAttributes}: list of attribute names from the {@code politicalLayer} to
 * return. Mandatory iif politicalLayer is provided, ignored otherwise.
 * <li>{@code geometry}: the GeoJSON geometry to buffer around
 * <li>{@code radius}: Double indicating how much to buffer around the input {@code geometry}
 * <li>{@code datalayers}: List&lt;String&gt; containing the <strong>coverage</strong> layer names
 * to create statistics for
 * </ul>
 * </p>
 */
public class ProcessRestlet extends Restlet {

    public static final Logger LOGGER = Logging.getLogger("org.geonode.rest");

    static final String POLITICAL_LAYER_PARAM = "politicalLayer";

    static final String POLITICAL_LAYER_ATTRIBUTES_PARAM = "politicalLayerAttributes";

    static final String DATALAYERS_PARAM = "datalayers";

    static final String GEOMETRY_PARAM = "geometry";

    static final String RADIUS_PARAM = "radius";

    private final Catalog catalog;

    /**
     * 
     * @param catalog
     * @param politicalLayerName
     * @param politicalLayerAttribtues
     * @throws IllegalArgumentException
     *             if the political layer or its attributes to return are missconfigured
     */
    public ProcessRestlet(final Catalog catalog) {
        this.catalog = catalog;
    }

    @Override
    public void handle(Request request, Response response) {
        if (!request.getMethod().equals(Method.POST)) {
            response.setStatus(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED);
            return;
        }

        final String requestContent;
        try {
            final InputStream inStream = request.getEntity().getStream();
            requestContent = IOUtils.toString(inStream);
        } catch (IOException e) {
            final String message = "Process failed: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.SEVERE, message, e);
            return;
        }

        JSONObject jsonRequest = JSONObject.fromObject(requestContent);

        final JSONObject responseData;
        try {
            responseData = execute(jsonRequest);
        } catch (ProcessException e) {
            final String message = "Process failed: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.SEVERE, message, e);
            return;
        } catch (IllegalArgumentException e) {
            final String message = "Process can't be executed: " + e.getMessage();
            response.setStatus(Status.CLIENT_ERROR_EXPECTATION_FAILED, message);
            LOGGER.log(Level.INFO, message, e);
            return;
        } catch (RuntimeException e) {
            final String message = "Unexpected exception: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.SEVERE, message, e);
            return;
        }

        final String jsonStr = responseData.toString(0);
        final Representation representation = new StringRepresentation(jsonStr,
                MediaType.APPLICATION_JSON);

        response.setEntity(representation);
    }

    private JSONObject execute(final JSONObject jsonRequest) throws ProcessException {

        final Map<String, Object> processInputs = convertProcessInputs(jsonRequest);

        final Process process = new HazardStatisticsFactory().create();
        final ProgressListener monitor = new NullProgressListener();

        final Map<String, Object> processOutputs = process.execute(processInputs, monitor);

        final JSONObject convertedOutputs = convertProcessOutputs(jsonRequest, processOutputs);

        return convertedOutputs;
    }

    @SuppressWarnings("unchecked")
    private JSONObject convertProcessOutputs(final JSONObject jsonRequest,
            final Map<String, Object> processOutputs) {

        final Map<String, Map<String, double[]>> stats;
        final List<Map<String, Object>> political;

        {
            final List<Map<String, double[]>> perLayerStats;
            perLayerStats = (List<Map<String, double[]>>) processOutputs
                    .get(HazardStatisticsFactory.RESULT_STATISTICS.key);
            final List<String> layerNames = jsonRequest.getJSONArray(DATALAYERS_PARAM);

            stats = new HashMap<String, Map<String, double[]>>();
            for (int i = 0; i < layerNames.size(); i++) {
                stats.put(layerNames.get(i), perLayerStats.get(i));
            }
        }
        political = (List<Map<String, Object>>) processOutputs
                .get(HazardStatisticsFactory.RESULT_POLITICAL.key);

        final JSONObject buffer;
        {
            Geometry computedArea;
            computedArea = (Geometry) processOutputs.get(HazardStatisticsFactory.RESULT_BUFER.key);
            Writer w = new StringWriter();
            GeoJSONSerializer geoJSONSerializer = new GeoJSONSerializer(w);
            geoJSONSerializer.writeGeometry(computedArea);
            buffer = JSONObject.fromObject(w.toString());
        }

        final JSONObject convertedOutputs;
        {
            Map<String, Object> results = new HashMap<String, Object>();
            results.put("statistics", stats);
            results.put("political", political);
            results.put("buffer", buffer);
            results.put("position", processOutputs.get(HazardStatisticsFactory.RESULT_POSITION.key));
            results.put("length", processOutputs.get(HazardStatisticsFactory.RESULT_LENGTH.key));
            results.put("area", processOutputs.get(HazardStatisticsFactory.RESULT_AREA.key));
            convertedOutputs = GeoJSONParser.fromObject(results);
        }
        return convertedOutputs;
    }

    /**
     * Converts REST process inputs given as JSON objects to the actual
     * {@link HazardStatisticsFactory process} inputs.
     * 
     * @param attributes
     * @return
     */
    private Map<String, Object> convertProcessInputs(final JSONObject request)
            throws ProcessException {
        // might be null
        final FeatureSource<FeatureType, Feature> politicalLayer = parsePoliticalLayerName(request);
        // might be empty iif politicalLayerName is null
        final List<String> politicalLayerAtts = parsePoliticalLayerAtts(request);

        final Geometry geometry = parseGeometryParam(request);
        final Double radius = parseRadiusParam(request);
        final List<AbstractGridCoverage2DReader> datalayers = parseDataLayersParam(request);

        Map<String, Object> processInputs = new HashMap<String, Object>();

        if (politicalLayer != null) {
            processInputs.put(HazardStatisticsFactory.POLITICAL_LAYER.key, politicalLayer);
            processInputs.put(HazardStatisticsFactory.POLITICAL_LAYER_ATTRIBUTES.key,
                    politicalLayerAtts);
        }

        processInputs.put(HazardStatisticsFactory.GEOMERTY.key, geometry);
        processInputs.put(HazardStatisticsFactory.RADIUS.key, radius);
        processInputs.put(HazardStatisticsFactory.DATALAYER.key, datalayers);

        return processInputs;
    }

    /**
     * Parses the optional {@link #POLITICAL_LAYER_PARAM political layer} parameter.
     * <p>
     * If provided, the layer will be validated against the Catalog for existence
     * </p>
     * 
     * @param request
     * @return
     */
    @SuppressWarnings("unchecked")
    private FeatureSource<FeatureType, Feature> parsePoliticalLayerName(final JSONObject request) {
        final String politicalLayerName = (String) request.get(POLITICAL_LAYER_PARAM);

        if (politicalLayerName == null) {
            return null;
        }

        final LayerInfo politicalLayer = catalog.getLayerByName(politicalLayerName);
        if (politicalLayer == null) {
            throw new IllegalArgumentException("Political layer " + politicalLayerName
                    + " does not exist in the catalog");
        }
        if (!(politicalLayer.getResource() instanceof FeatureTypeInfo)) {
            throw new IllegalArgumentException("Political layer should be a vector layer");
        }

        final ProgressListener listener = new NullProgressListener();
        final Hints hints = GeoTools.getDefaultHints();
        FeatureSource<FeatureType, Feature> featureSource;
        try {
            FeatureTypeInfo resource = (FeatureTypeInfo) politicalLayer.getResource();
            featureSource = (FeatureSource<FeatureType, Feature>) resource.getFeatureSource(
                    listener, hints);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return featureSource;
    }

    @SuppressWarnings("unchecked")
    private List<String> parsePoliticalLayerAtts(final JSONObject request) throws ProcessException {

        final String politicalLayerName = (String) request.get(POLITICAL_LAYER_PARAM);

        if (politicalLayerName == null) {
            return Collections.emptyList();
        }

        if (!request.containsKey(POLITICAL_LAYER_ATTRIBUTES_PARAM)) {
            throw new IllegalArgumentException(POLITICAL_LAYER_PARAM
                    + " parameter was provided but " + POLITICAL_LAYER_ATTRIBUTES_PARAM
                    + " was not");
        }

        final List<String> politicalLayerAttribtues;
        {
            final JSONArray politicalLayerAttsParam;
            politicalLayerAttsParam = request.getJSONArray(POLITICAL_LAYER_ATTRIBUTES_PARAM);
            if (politicalLayerAttsParam.size() == 0) {
                throw new IllegalArgumentException(POLITICAL_LAYER_PARAM
                        + " parameter was provided but " + POLITICAL_LAYER_ATTRIBUTES_PARAM
                        + " was not");
            }
            Collection collection = JSONArray.toList(politicalLayerAttsParam);
            politicalLayerAttribtues = new ArrayList<String>(collection);
        }

        final LayerInfo politicalLayer = catalog.getLayerByName(politicalLayerName);

        final FeatureTypeInfo resource = (FeatureTypeInfo) politicalLayer.getResource();
        final List<AttributeTypeInfo> ftattributes;

        try {
            ftattributes = resource.attributes();
        } catch (IOException ioe) {
            throw new ProcessException(ioe);
        }

        Set<String> attnames = new HashSet<String>();
        for (AttributeTypeInfo att : ftattributes) {
            attnames.add(att.getName());
        }

        for (String attname : politicalLayerAttribtues) {
            if (!attnames.contains(attname)) {
                throw new IllegalArgumentException("Configured political layer attribute '"
                        + attname + "' does not exist: " + Arrays.toString(attnames.toArray()));
            }
        }
        return politicalLayerAttribtues;
    }

    @SuppressWarnings("unchecked")
    private List<AbstractGridCoverage2DReader> parseDataLayersParam(final JSONObject request) {

        final JSONArray datalayersParam = request.getJSONArray(DATALAYERS_PARAM);
        if (datalayersParam == null) {
            throw new IllegalArgumentException(DATALAYERS_PARAM + " parameter was not provided");
        }

        final Object datalayersObject = JSONSerializer.toJava(datalayersParam);
        if (!Collection.class.isAssignableFrom(datalayersObject.getClass())) {
            throw new IllegalArgumentException(DATALAYERS_PARAM + " is not a list of layer names: "
                    + datalayersParam);
        }

        List<AbstractGridCoverage2DReader> layers = new ArrayList<AbstractGridCoverage2DReader>();

        final ProgressListener listener = new NullProgressListener();
        final Hints hints = GeoTools.getDefaultHints();

        final Collection<String> layerNames = (Collection<String>) datalayersObject;
        if (layerNames.size() == 0) {
            throw new IllegalArgumentException("No data layers have been requested: "
                    + datalayersParam);
        }
        for (String layerName : layerNames) {
            final CoverageInfo coverageInfo = catalog.getCoverageByName(layerName);
            if (coverageInfo == null) {
                throw new IllegalArgumentException("Requested coverage " + layerName
                        + " does not exist");
            }
            try {
                AbstractGridCoverage2DReader coverageReader;
                coverageReader = (AbstractGridCoverage2DReader) coverageInfo.getGridCoverageReader(
                        listener, hints);
                layers.add(coverageReader);
            } catch (IOException e) {
                throw new RuntimeException("Can't obtain reader for layer " + layerName, e);
            }
        }

        return layers;
    }

    private Geometry parseGeometryParam(final JSONObject request) {
        final Geometry geometry;

        final JSONObject geometryParam = request.getJSONObject(GEOMETRY_PARAM);
        if (geometryParam == null) {
            throw new IllegalArgumentException(GEOMETRY_PARAM + " parameter was not provided");
        }

        final Object geometryObject = GeoJSONParser.parse(geometryParam);

        if (geometryObject instanceof Geometry) {
            geometry = (Geometry) geometryObject;
        } else {
            throw new IllegalArgumentException(GEOMETRY_PARAM + " is not a GeoJSON geometry: "
                    + geometryParam);
        }
        return geometry;
    }

    private Double parseRadiusParam(final JSONObject attributes) {
        final Double radius;
        Object radiusParam = (Object) attributes.get(RADIUS_PARAM);
        if (radiusParam == null) {
            throw new IllegalArgumentException(RADIUS_PARAM + " parameter was not provided");
        }

        if (radiusParam instanceof Number) {
            radius = Double.valueOf(((Number) radiusParam).doubleValue());
        } else {
            throw new IllegalArgumentException(RADIUS_PARAM + " is not a floating point number: "
                    + radiusParam);
        }
        return radius;
    }
}
