package org.geonode.rest.batchdownload;

import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONArray;
import net.sf.json.JSONException;
import net.sf.json.JSONObject;

import org.apache.commons.io.IOUtils;
import org.geonode.process.batchdownload.BatchDownloadFactory;
import org.geonode.process.batchdownload.LayerReference;
import org.geonode.process.batchdownload.MapMetadata;
import org.geonode.process.control.AsyncProcess;
import org.geonode.process.control.ProcessController;
import org.geonode.process.control.ProcessStatus;
import org.geoserver.catalog.Catalog;
import org.geoserver.catalog.CoverageInfo;
import org.geoserver.catalog.FeatureTypeInfo;
import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.data.FeatureSource;
import org.geotools.factory.Hints;
import org.geotools.feature.NameImpl;
import org.geotools.process.ProcessException;
import org.geotools.process.Processors;
import org.geotools.util.NullProgressListener;
import org.geotools.util.logging.Logging;
import org.opengis.feature.Feature;
import org.opengis.feature.type.FeatureType;
import org.opengis.feature.type.Name;
import org.restlet.Restlet;
import org.restlet.data.MediaType;
import org.restlet.data.Method;
import org.restlet.data.Request;
import org.restlet.data.Response;
import org.restlet.data.Status;
import org.restlet.resource.Representation;
import org.restlet.resource.StringRepresentation;

/**
 * 
 * Expects a JSON object with the following structure:
 * <p>
 * <code>
 * <pre>
 *  {  map : { 
 *           title: "human readable title",
 *           abstract: "abstract information",
 *           author: "author name" 
 *           } 
 *    layers: 
 *        [
 *          {
 *              name:"&lt;layerName&gt;",
 *              service: "&lt;WFS|WCS&gt;,
 *              metadataURL: "&lt;csw request for the layer metadata?&gt;", 
 *              serviceURL:"&lt;serviceURL&gt;" //eg, "http://geonode.org/geoserver/wfs" 
 *          } ,...
 *        ]
 *  } 
 * </pre>
 * </code> or <code>
 * <pre>
 *  {  map : { 
 *           readme: "full content for the readme.tx file here...",
 *           } 
 *    layers: 
 *        [
 *          {
 *              name:"&lt;layerName&gt;",
 *              service: "&lt;WFS|WCS&gt;,
 *              metadataURL: "&lt;csw request for the layer metadata?&gt;", 
 *              serviceURL:"&lt;serviceURL&gt;" //eg, "http://geonode.org/geoserver/wfs" 
 *          } ,...
 *        ]
 *  } 
 * </pre>
 * </code>
 * 
 * 
 * Upon successful process launching returns a JSON object with the following structure: <code>
 * <pre>
 * {
 *   process:{
 *        id: &lt;processId&gt;
 *        status: &lt;WAITING|RUNNING|FINISHED|FAILED|CANCELLED&gt;
 *        statusMessage: "&lt;status message&gt;"
 *   }     
 * }
 * </pre>
 * </code>
 * </p>
 * 
 * @author Gabriel Roldan
 * @version $Id$
 */
public class DownloadLauncherRestlet extends Restlet {

    private static Logger LOGGER = Logging.getLogger(DownloadLauncherRestlet.class);

    private static final Name PROCESS_NAME = new NameImpl("geonode", "BatchDownload");

    private final Catalog catalog;

    private final ProcessController controller;

    public DownloadLauncherRestlet(final Catalog catalog, final ProcessController controller) {
        this.catalog = catalog;
        this.controller = controller;
    }

    @Override
    public void handle(Request request, Response response) {
        if (!request.getMethod().equals(Method.POST)) {
            response.setStatus(Status.CLIENT_ERROR_METHOD_NOT_ALLOWED,
                    "POST method is required to launch a batch download process");
            return;
        }

        LOGGER.fine("Reading JSON request...");
        final String requestContent;
        try {
            final InputStream inStream = request.getEntity().getStream();
            requestContent = IOUtils.toString(inStream);
            if (LOGGER.isLoggable(Level.FINER)) {
                LOGGER.finer("Plain request: " + requestContent);
            }
        } catch (IOException e) {
            if (LOGGER.isLoggable(Level.FINER)) {
                LOGGER.log(Level.FINER, "Bad request", e);
            }
            final String message = "Process failed: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            return;
        }

        LOGGER.finest("Parsing JSON request...");
        JSONObject jsonRequest;
        try {
            jsonRequest = JSONObject.fromObject(requestContent);
        } catch (JSONException e) {
            response.setStatus(Status.CLIENT_ERROR_BAD_REQUEST, e.getMessage());
            return;
        }

        LOGGER.finest("Launch request parsed, validating inputs and launching process...");
        final JSONObject responseData;
        try {
            responseData = execute(jsonRequest);
        } catch (ProcessException e) {
            final String message = "Process failed: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.INFO, message, e);
            return;
        } catch (IllegalArgumentException e) {
            final String message = "Process can't be executed: " + e.getMessage();
            response.setStatus(Status.CLIENT_ERROR_EXPECTATION_FAILED, message);
            LOGGER.log(Level.INFO, message, e);
            return;
        } catch (RuntimeException e) {
            final String message = "Unexpected exception: " + e.getMessage();
            response.setStatus(Status.SERVER_ERROR_INTERNAL, message);
            LOGGER.log(Level.WARNING, message, e);
            return;
        }

        final String jsonStr = responseData.toString(0);
        if (LOGGER.isLoggable(Level.FINER)) {
            LOGGER.finer("Process launched, response is " + jsonStr);
        }
        final Representation representation = new StringRepresentation(jsonStr,
                MediaType.APPLICATION_JSON);

        response.setEntity(representation);
    }

    private JSONObject execute(final JSONObject jsonRequest) throws ProcessException {

        final Map<String, Object> processInputs = convertProcessInputs(jsonRequest);

        final AsyncProcess process = (AsyncProcess) Processors.createProcess(PROCESS_NAME);
        if (process == null) {
            throw new IllegalStateException("Process factory not found for " + PROCESS_NAME);
        }

        final Long processId = controller.submitAsync(process, processInputs);

        JSONObject convertedOutputs = new JSONObject();
        convertedOutputs.element("id", processId.longValue());
        ProcessStatus status = controller.getStatus(processId);
        convertedOutputs.element("status", status.toString());
        float progress = controller.getProgress(processId);
        convertedOutputs.element("progress", progress);

        return convertedOutputs;
    }

    /**
     * Converts REST process inputs given as JSON objects to the actual {@link BatchDownloadFactory
     * process} inputs.
     * 
     * @param attributes
     * @return
     */
    private Map<String, Object> convertProcessInputs(final JSONObject request)
            throws ProcessException {

        Map<String, Object> processInputs;
        try {
            JSONObject map = request.getJSONObject("map");
            final MapMetadata mapDetails = convertMapMetadataParam(map);
            JSONArray layersParam = request.getJSONArray("layers");
            final List<LayerReference> layers = convertLayersParam(layersParam);

            processInputs = new HashMap<String, Object>();
            processInputs.put(BatchDownloadFactory.MAP_METADATA.key, mapDetails);
            processInputs.put(BatchDownloadFactory.LAYERS.key, layers);
        } catch (JSONException e) {
            throw new IllegalArgumentException(e.getMessage(), e);
        }
        return processInputs;
    }

    /**
     * Takes either a {@code "readme"} property as the complete contents for the README file, or the
     * following properties: {@code "title", "abstract", "author"}, whichever is present, in that
     * order of precedence.
     * 
     * @param obj
     *            the {@code "map"} json object
     * @return
     * @throws JSONException
     *             if a required json object property is not found
     */
    private MapMetadata convertMapMetadataParam(final JSONObject obj) throws JSONException {
        MapMetadata mmd;
        if (obj.containsKey("readme")) {
            String readme = obj.getString("readme");
            mmd = new MapMetadata(readme);
        } else {
            String title = obj.getString("title");
            if (title.length() == 0) {
                throw new IllegalArgumentException("Map name is empty");
            }
            String _abstract = obj.containsKey("abstract") ? obj.getString("abstract") : null;
            String author = obj.getString("author");
            if (author.length() == 0) {
                throw new IllegalArgumentException("author name is empty");
            }
            mmd = new MapMetadata(title, _abstract, author);
        }
        return mmd;
    }

    private List<LayerReference> convertLayersParam(final JSONArray obj) {
        if (obj == null || obj.size() == 0) {
            throw new IllegalArgumentException("no layers provided");
        }

        final int size = obj.size();
        List<LayerReference> layers = new ArrayList<LayerReference>(size);

        for (int layerN = 0; layerN < size; layerN++) {
            JSONObject layerParam = obj.getJSONObject(layerN);
            LayerReference layer = parseLayerReference(layerParam);
            layers.add(layer);
        }
        return layers;
    }

    private LayerReference parseLayerReference(final JSONObject layerParam) {
        final String layerName = layerParam.getString("name");
        final String service = layerParam.getString("service");
        final String serviceURL = layerParam.getString("serviceURL");

        final URL metadataURL;

        if (layerParam.containsKey("metadataURL")) {
            final String metadataURLParam = layerParam.getString("metadataURL");
            if (metadataURLParam.length() > 0) {
                try {
                    metadataURL = new URL(metadataURLParam);
                } catch (MalformedURLException e) {
                    throw new IllegalArgumentException("invalid format for metadataURL: '"
                            + metadataURLParam + "'");
                }
            } else {
                metadataURL = null;
            }
        } else {
            if (LOGGER.isLoggable(Level.FINE)) {
                LOGGER.fine("metadataURL not provided for " + layerParam);
            }
            metadataURL = null;
        }

        LayerReference layer;
        if ("WFS".equals(service)) {
            FeatureSource<FeatureType, Feature> source = getFeatureSource(serviceURL, layerName);
            layer = new LayerReference(layerName, source);
        } else if ("WCS".equals(service)) {
            AbstractGridCoverage2DReader source = getCoverageReader(serviceURL, layerName);
            layer = new LayerReference(layerName, source);
        } else {
            throw new IllegalArgumentException("Invalid service name for layer '" + layerName
                    + "'. Expected one of WFS,WCS. Was '" + service + "'");
        }

        layer.setMetadataURL(metadataURL);

        return layer;
    }

    private AbstractGridCoverage2DReader getCoverageReader(final String serviceURL,
            final String layerName) {
        if (LOGGER.isLoggable(Level.FINE)) {
            LOGGER.fine("Ignoring serviceURL '" + serviceURL
                    + "'. Process only supports references to local resources by now.");
        }

        final CoverageInfo coverageInfo = catalog.getCoverageByName(layerName);
        if (coverageInfo == null) {
            throw new IllegalArgumentException("Coverage '" + layerName + "' does not exist");
        }
        AbstractGridCoverage2DReader reader;
        try {
            reader = (AbstractGridCoverage2DReader) coverageInfo.getGridCoverageReader(
                    new NullProgressListener(), (Hints) null);
        } catch (IOException e) {
            throw new RuntimeException("Error retrieveing coverage '" + layerName + "': "
                    + e.getMessage(), e);
        }
        return reader;
    }

    @SuppressWarnings("unchecked")
    private FeatureSource<FeatureType, Feature> getFeatureSource(final String serviceURL,
            final String layerName) {
        if (LOGGER.isLoggable(Level.FINE)) {
            LOGGER.fine("Ignoring serviceURL '" + serviceURL
                    + "'. Process only supports references to local resources by now.");
        }

        final FeatureTypeInfo typeInfo = catalog.getFeatureTypeByName(layerName);
        if (typeInfo == null) {
            throw new IllegalArgumentException("Feature Type '" + layerName + "' does not exist");
        }
        FeatureSource<FeatureType, Feature> source;
        try {
            source = (FeatureSource<FeatureType, Feature>) typeInfo.getFeatureSource(
                    new NullProgressListener(), (Hints) null);
        } catch (IOException e) {
            throw new RuntimeException("Error retrieveing feature type '" + layerName + "': "
                    + e.getMessage(), e);
        }
        return source;
    }

}
