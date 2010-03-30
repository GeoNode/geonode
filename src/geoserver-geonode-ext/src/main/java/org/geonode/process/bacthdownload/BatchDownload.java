package org.geonode.process.bacthdownload;

import static org.geonode.process.bacthdownload.BatchDownloadFactory.LAYERS;
import static org.geonode.process.bacthdownload.BatchDownloadFactory.MAP_METADATA;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import org.geonode.process.control.AsyncProcess;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.util.logging.Logging;
import org.opengis.util.ProgressListener;

final class BatchDownload extends AsyncProcess {

    public static final Logger LOGGER = Logging.getLogger(BatchDownload.class);

    protected BatchDownload() {

    }

    /**
     * @see Process#execute(Map, ProgressListener)
     */
    @SuppressWarnings("unchecked")
    @Override
    protected Map<String, Object> executeInternal(final Map<String, Object> input,
            final ProgressListener monitor) throws ProcessException {

        final MapMetadata mapDetails = (MapMetadata) input.get(MAP_METADATA.key);
        final List<LayerReference> layers = (List<LayerReference>) input.get(LAYERS.key);

        if (monitor.isCanceled()) {
            return null;
        }

        checkInputs(mapDetails, layers);

        if (monitor.isCanceled()) {
            return null;
        }

        Map<String, Object> results = new HashMap<String, Object>();
        return results;
    }

    private void checkInputs(final MapMetadata map, final List<LayerReference> layers) {
        if (map == null) {
            throw new IllegalArgumentException("map metadata not provided (missing "
                    + MAP_METADATA.key + " argument)");
        }

        // map and locale are optional, all we really need to check is the layer references
        if (layers == null || layers.size() == 0) {
            throw new IllegalArgumentException("At least one input layer is required. Missing "
                    + LAYERS.key + " argument?.");
        }
    }
}
