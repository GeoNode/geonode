package org.geonode.process;

import static org.geonode.process.BatchDownloadFactory.MAP_METADATA;
import static org.geonode.process.BatchDownloadFactory.LAYERS;
import static org.geonode.process.BatchDownloadFactory.LOCALE;

import java.awt.Shape;
import java.awt.geom.AffineTransform;
import java.awt.geom.Area;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.net.URL;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.media.jai.Histogram;
import javax.media.jai.ROI;
import javax.media.jai.ROIShape;

import org.geotools.coverage.grid.GridCoverage2D;
import org.geotools.coverage.grid.GridEnvelope2D;
import org.geotools.coverage.grid.GridGeometry2D;
import org.geotools.coverage.grid.ViewType;
import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.coverage.grid.io.AbstractGridFormat;
import org.geotools.coverage.processing.OperationJAI;
import org.geotools.data.DefaultQuery;
import org.geotools.data.FeatureSource;
import org.geotools.factory.CommonFactoryFinder;
import org.geotools.factory.GeoTools;
import org.geotools.feature.FeatureCollection;
import org.geotools.feature.FeatureIterator;
import org.geotools.geometry.Envelope2D;
import org.geotools.geometry.GeneralEnvelope;
import org.geotools.geometry.jts.JTS;
import org.geotools.geometry.jts.LiteShape;
import org.geotools.geometry.jts.ReferencedEnvelope;
import org.geotools.parameter.Parameter;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.process.ProcessFactory;
import org.geotools.process.impl.AbstractProcess;
import org.geotools.referencing.CRS;
import org.geotools.util.logging.Logging;
import org.opengis.coverage.grid.GridEnvelope;
import org.opengis.feature.Feature;
import org.opengis.feature.Property;
import org.opengis.feature.type.FeatureType;
import org.opengis.feature.type.GeometryDescriptor;
import org.opengis.filter.Filter;
import org.opengis.filter.FilterFactory2;
import org.opengis.parameter.GeneralParameterValue;
import org.opengis.parameter.ParameterValueGroup;
import org.opengis.referencing.FactoryException;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import org.opengis.referencing.datum.PixelInCell;
import org.opengis.referencing.operation.MathTransform;
import org.opengis.referencing.operation.MathTransform2D;
import org.opengis.referencing.operation.NoninvertibleTransformException;
import org.opengis.referencing.operation.TransformException;
import org.opengis.util.ProgressListener;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.Envelope;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.MultiLineString;
import com.vividsolutions.jts.geom.MultiPolygon;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;
import com.vividsolutions.jts.geom.PrecisionModel;

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
