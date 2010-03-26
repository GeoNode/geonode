package org.geonode.process.bacthdownload;

import static org.geonode.process.bacthdownload.BatchDownloadFactory.LAYERS;
import static org.geonode.process.bacthdownload.BatchDownloadFactory.LOCALE;
import static org.geonode.process.bacthdownload.BatchDownloadFactory.MAP_METADATA;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.process.ProcessFactory;
import org.geotools.process.impl.AbstractProcess;
import org.geotools.util.logging.Logging;
import org.opengis.util.ProgressListener;

final class BatchDownload extends AbstractProcess {

    public static final Logger LOGGER = Logging.getLogger("org.geonode.process");

    protected BatchDownload(final ProcessFactory factory) {
        super(factory);
    }

    /**
     * @see Process#execute(Map, ProgressListener)
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> execute(final Map<String, Object> input,
            final ProgressListener monitor) throws ProcessException {

        final MapMetadata mapDetails = (MapMetadata) input.get(MAP_METADATA.key);
        final List<LayerReference> layers = (List<LayerReference>) input.get(LAYERS.key);
        final String locale = (String) input.get(LOCALE.key);

        checkInputs(mapDetails, layers, locale);

        Map<String, Object> results = new HashMap<String, Object>();
        return results;
    }

    private void checkInputs(final MapMetadata map, final List<LayerReference> layers,
            final String locale) {
        // map and locale are optional, all we really need to check is the layer references
        if (layers == null) {
            throw new NullPointerException("At least one input layer is required.");
        }

        for (LayerReference l : layers) {
            URL url;
            try {
                url = new URL(l.getServiceURL());
            } catch (MalformedURLException e) {
                throw new IllegalArgumentException("Unreadable service url: " + l.getServiceURL());
            }

            if (!"localhost".equals(url.getHost())) {
                throw new IllegalArgumentException("Layers for download must be local; remove " +
                        url + " and try again.");
            }
        }
    }
}
