package org.geonode.process.coveragestats;

import static org.geonode.process.coveragestats.HazardStatisticsFactory.DATALAYER;
import static org.geonode.process.coveragestats.HazardStatisticsFactory.GEOMERTY;
import static org.geonode.process.coveragestats.HazardStatisticsFactory.RADIUS;

import java.awt.Shape;
import java.awt.geom.AffineTransform;
import java.awt.geom.Area;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
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

final class HazardStatistics extends AbstractProcess {

    public static final Logger LOGGER = Logging.getLogger("org.geonode.process");

    protected HazardStatistics(final ProcessFactory factory) {
        super(factory);
    }

    /**
     * @see Process#execute(Map, ProgressListener)
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> execute(final Map<String, Object> input,
            final ProgressListener monitor) throws ProcessException {

        final Geometry inputGeometry = (Geometry) input.get(GEOMERTY.key);
        final Double inputRadius = (Double) input.get(RADIUS.key);
        final List<AbstractGridCoverage2DReader> inputDataLayers;

        inputDataLayers = (List<AbstractGridCoverage2DReader>) input.get(DATALAYER.key);

        checkInputs(inputGeometry, inputRadius, inputDataLayers);

        final Geometry bufferedGeometry = performBuffer(inputGeometry, inputRadius);
        /*
         * If the inputGeometry carries over CRS information lets set it to the buffered geometry so
         * #gatherCoverageStats reprojects as needed
         */
        if (inputGeometry.getUserData() instanceof CoordinateReferenceSystem) {
            CoordinateReferenceSystem bufferCrs;
            bufferCrs = (CoordinateReferenceSystem) inputGeometry.getUserData();
            bufferedGeometry.setUserData(bufferCrs);
        }

        /*
         * CoverageReaders have no Name, so we return a list of results in the same order than the
         * provided readers for client code to match them up
         */
        List<Map<String, double[]>> perLayerStats = new ArrayList<Map<String, double[]>>();
        for (AbstractGridCoverage2DReader layer : inputDataLayers) {
            Map<String, double[]> stats = gatherCoverageStats(layer, bufferedGeometry);
            perLayerStats.add(stats == null ? null : new HashMap<String, double[]>(stats));
        }

        Map<String, Object> results = new HashMap<String, Object>();

        results.put(HazardStatisticsFactory.RESULT_STATISTICS.key, perLayerStats);

        FeatureSource<FeatureType, Feature> politicalLayer = (FeatureSource<FeatureType, Feature>) input
                .get(HazardStatisticsFactory.POLITICAL_LAYER.key);
        List<String> politicalLayerAtts = (List<String>) input
                .get(HazardStatisticsFactory.POLITICAL_LAYER_ATTRIBUTES.key);

        List<Map<String, Object>> politicalData = getPoliticalLayerIntersectionInfo(politicalLayer,
                politicalLayerAtts, bufferedGeometry);

        results.put(HazardStatisticsFactory.RESULT_POLITICAL.key, politicalData);
        results.put(HazardStatisticsFactory.RESULT_BUFER.key, bufferedGeometry);

        List<Double> coordinates = coordinates(inputGeometry);
        if (coordinates != null)
            results.put(HazardStatisticsFactory.RESULT_POSITION.key, coordinates);
        Double length = length(inputGeometry);
        if (length != null)
            results.put(HazardStatisticsFactory.RESULT_LENGTH.key, length);
        Double area = area(inputGeometry);
        if (area != null)
            results.put(HazardStatisticsFactory.RESULT_AREA.key, area);

        return results;
    }

    private List<Double> coordinates(Geometry geom) {
        if (geom instanceof Point) {
            Coordinate c = geom.getCoordinate();
            return Arrays.asList(new Double[] { c.x, c.y });
        } else {
            return null;
        }
    }

    private Double length(Geometry geom) {
        if (geom instanceof LineString || geom instanceof MultiLineString) {
            return geom.getLength();
        } else {
            return null;
        }
    }

    private Double area(Geometry geom) {
        if (geom instanceof Polygon || geom instanceof MultiPolygon) {
            return geom.getArea();
        } else {
            return null;
        }
    }

    private List<Map<String, Object>> getPoliticalLayerIntersectionInfo(
            final FeatureSource<FeatureType, Feature> politicalLayer,
            final List<String> politicalLayerAtts, final Geometry bufferedGeometry) {

        if (politicalLayer == null) {
            return Collections.emptyList();
        }
        if (politicalLayerAtts == null || politicalLayerAtts.size() == 0) {
            throw new IllegalArgumentException(
                    "Required return attribtues shall be specified for the political layer");
        }

        final GeometryDescriptor geometryDescriptor = politicalLayer.getSchema()
                .getGeometryDescriptor();
        if (geometryDescriptor == null) {
            throw new IllegalArgumentException("Political layer " + politicalLayer.getName()
                    + " has no geometry property");
        }

        final FeatureIterator<Feature> iterator;
        {
            final FilterFactory2 ff = CommonFactoryFinder.getFilterFactory2(GeoTools
                    .getDefaultHints());
            final CoordinateReferenceSystem layerCrs = geometryDescriptor
                    .getCoordinateReferenceSystem();

            final CoordinateReferenceSystem requestCrs;
            if (bufferedGeometry.getUserData() instanceof CoordinateReferenceSystem) {
                requestCrs = (CoordinateReferenceSystem) bufferedGeometry.getUserData();
            } else {
                requestCrs = layerCrs;
            }
            final Filter filter = ff.intersects(ff.property(geometryDescriptor.getName()),
                    ff.literal(bufferedGeometry));

            DefaultQuery query = new DefaultQuery();
            query.setPropertyNames(politicalLayerAtts);
            query.setFilter(filter);
            query.setCoordinateSystem(requestCrs);
            // query.setCoordinateSystemReproject(layerCrs);

            FeatureCollection<FeatureType, Feature> features;
            try {
                features = politicalLayer.getFeatures(query);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }

            iterator = features.features();
        }

        List<Map<String, Object>> political = new ArrayList<Map<String, Object>>(2);
        try {
            Feature feature;
            Map<String, Object> featureData;
            while (iterator.hasNext()) {
                feature = iterator.next();
                featureData = new HashMap<String, Object>();
                for (String propName : politicalLayerAtts) {
                    Property property = feature.getProperty(propName);
                    Object value = property == null ? null : property.getValue();
                    featureData.put(propName, value);
                }
                political.add(featureData);
            }
        } finally {
            iterator.close();
        }

        return political;
    }

    private Map<String, double[]> gatherCoverageStats(final AbstractGridCoverage2DReader layer,
            final Geometry bufferedGeometry) throws ProcessException {

        final CoordinateReferenceSystem layerCrs = layer.getCrs();

        final Geometry requestGeometry = transformBufferToLayerCrs(bufferedGeometry, layerCrs);

        final GridCoverage2D geophysics;
        try {
            final ReferencedEnvelope requestEnvelope;
            requestEnvelope = new ReferencedEnvelope(requestGeometry.getEnvelopeInternal(),
                    layerCrs);

            GridCoverage2D coverage = getGridCoverage(layer, requestEnvelope);
            if (coverage == null) {
                // request envelope did not intersect coverage, return null stats
                return null;
            } else {
                geophysics = coverage.view(ViewType.GEOPHYSICS);
            }
        } catch (IOException e) {
            throw new ProcessException(e);
        }

        final ROI regionOfInterest = getRegionOfInterest(geophysics, requestGeometry);

        final OperationJAI op = new OperationJAI("Histogram");
        ParameterValueGroup params = op.getParameters();
        params.parameter("Source").setValue(geophysics);
        if (regionOfInterest != null) {
            params.parameter("ROI").setValue(regionOfInterest);
        }
        GridCoverage2D coverage = (GridCoverage2D) op.doOperation(params, null);
        Histogram histogram = (Histogram) coverage.getProperty("histogram");

        Map<String, double[]> stats = new HashMap<String, double[]>();
        double[] lowValue = histogram.getLowValue();
        double[] highValue = histogram.getHighValue();
        double[] mean = histogram.getMean();
        double[] standardDeviation = histogram.getStandardDeviation();

        stats.put("min", lowValue);
        stats.put("max", highValue);

        /*
         * how many different sample values have been computed (per band)? if zero, the region of
         * interest was too small
         */
        final int[] numBins = histogram.getTotals();
        if (0 == numBins[0]) {
            /*
             * If the ROI was too small for one band, it was for all of them
             */
            stats.put("mean", null);
            stats.put("stddev", null);
        } else {
            stats.put("mean", mean);
            stats.put("stddev", standardDeviation);
        }

        return stats;
    }

    /**
     * Creates a ROI (Region of Interest) for the histogram operation based on the coverage grid
     * dimensions and the buffered geometry {@code spatialRoi}
     * <p>
     * Precondition: {@code coverage} and {@code spatialRoi} CRS's shall match.
     * </p>
     * 
     * @param coverage
     * @param spatialRoi
     * @return
     */
    private ROI getRegionOfInterest(final GridCoverage2D coverage, final Geometry spatialRoi) {
        LOGGER.entering(getClass().getSimpleName(), "getRegionOfInterest");

        final MathTransform2D worldToGrid = coverage.getGridGeometry().getCRSToGrid2D();

        /*
         * The region of interest in the coverage's grid space
         */
        final Geometry gridRoi;
        try {
            gridRoi = JTS.transform(spatialRoi, worldToGrid);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        /*
         * The coverage's grid dimension as a Polygon
         */
        final Polygon gridRangeGeom;
        final Polygon spatialRangeGeom;
        {
            final GridEnvelope gridRange = coverage.getGridGeometry().getGridRange();
            Envelope2D envelope2d = coverage.getGridGeometry().getEnvelope2D();
            gridRangeGeom = JTS.toGeometry(new Envelope(gridRange.getLow(0), gridRange.getHigh(0),
                    gridRange.getLow(1), gridRange.getHigh(1)));
            spatialRangeGeom = JTS.toGeometry(new Envelope(envelope2d.getMinX(), envelope2d
                    .getMaxX(), envelope2d.getMinY(), envelope2d.getMaxY()));
        }

        /*
         * The intersection between the coverage grid range and the region of interest in grid space
         */
        PrecisionModel precisionModel = new PrecisionModel(1D);
        final Geometry finalRoiGeom = new GeometryFactory(precisionModel).createGeometry(gridRoi
                .intersection(gridRangeGeom));

        LOGGER.fine("Coverage envelope:                " + spatialRangeGeom);
        LOGGER.fine("Region of interest:               " + spatialRoi);
        LOGGER.fine("Coverage grid range:              " + gridRangeGeom);
        LOGGER.fine("Region of interest in grid space: " + gridRoi);
        LOGGER.fine("Region of interest intersection:  " + finalRoiGeom);

        final Shape roiShape;
        {
            final boolean generalize = false;
            final AffineTransform at = null;
            roiShape = new Area(new LiteShape(finalRoiGeom, at, generalize));
        }

        final ROI regionOfInterest = new ROIShape(roiShape);

        if (LOGGER.isLoggable(Level.FINER)) {
            LOGGER.exiting(getClass().getSimpleName(), "getRegionOfInterest", regionOfInterest);
        }
        return regionOfInterest;
    }

    private Geometry transformBufferToLayerCrs(final Geometry bufferedGeometry,
            final CoordinateReferenceSystem layerCrs) {
        final Geometry requestGeometry;
        if (bufferedGeometry.getUserData() instanceof CoordinateReferenceSystem) {
            /*
             * The buffer contains CRS information, lets see if we need to reproject the buffer to
             * the coverage's CRS
             */
            final CoordinateReferenceSystem requestCrs;
            requestCrs = (CoordinateReferenceSystem) bufferedGeometry.getUserData();

            if (CRS.equalsIgnoreMetadata(layerCrs, requestCrs)) {
                requestGeometry = bufferedGeometry;
            } else {
                final MathTransform bufferToCoverage;
                try {
                    bufferToCoverage = CRS.findMathTransform(requestCrs, layerCrs, true);
                } catch (FactoryException e) {
                    throw new RuntimeException("Error obtaining input geometry CRS to "
                            + "Coverage CRS math transform", e);
                }
                try {
                    requestGeometry = JTS.transform(bufferedGeometry, bufferToCoverage);
                    requestGeometry.setUserData(layerCrs);
                } catch (RuntimeException e) {
                    throw e;
                } catch (Exception e) {
                    throw new RuntimeException("Error transforming buffer to Coverage's CRS", e);
                }
            }
        } else {
            /*
             * Assume the buffer is in the same CRS than the coverage and the user knows what he's
             * doing
             */
            requestGeometry = bufferedGeometry;
        }
        return requestGeometry;
    }

    private void checkInputs(final Geometry inputGeometry, final Double inputRadius,
            final List<AbstractGridCoverage2DReader> inputDataLayers) {
        if (inputGeometry == null) {
            throw new NullPointerException("input geometry is required");
        }
        if (inputRadius == null) {
            throw new NullPointerException("input radius is required");
        }
        if (inputDataLayers == null || inputDataLayers.size() == 0) {
            throw new NullPointerException("input data layer is required");
        }
    }

    private Geometry performBuffer(Geometry inputGeometry, Double inputRadius) {
        return inputGeometry.buffer(inputRadius.doubleValue());
    }

    /**
     * Loads a grid coverage.
     * <p>
     * 
     * </p>
     * 
     * @param info
     *            The grid coverage metadata.
     * @param envelope
     *            The section of the coverage to load.
     * @param hints
     *            Hints to use while loading the coverage.
     * 
     * @throws IOException
     *             Any errors that occur loading the coverage.
     */
    private GridCoverage2D getGridCoverage(final AbstractGridCoverage2DReader reader,
            final ReferencedEnvelope env) throws IOException {

        GeneralEnvelope requestEnvelope = new GeneralEnvelope(env);

        // /////////////////////////////////////////////////////////
        //
        // Do we need to proceed?
        // I need to check the requested envelope in order to see if the
        // coverage we ask intersect it otherwise it is pointless to load it
        // since its reader might return null;
        // /////////////////////////////////////////////////////////
        final CoordinateReferenceSystem sourceCRS = requestEnvelope.getCoordinateReferenceSystem();
        final CoordinateReferenceSystem destCRS = reader.getCrs();

        if (!CRS.equalsIgnoreMetadata(sourceCRS, destCRS)) {
            // get a math transform
            MathTransform transform;
            try {
                transform = CRS.findMathTransform(sourceCRS, destCRS, true);
            } catch (FactoryException e) {
                final IOException ioe = new IOException("unable to determine coverage crs");
                ioe.initCause(e);
                throw ioe;
            }

            // transform the envelope
            if (!transform.isIdentity()) {
                try {
                    requestEnvelope = CRS.transform(transform, requestEnvelope);
                } catch (TransformException e) {
                    throw (IOException) new IOException("error occured transforming envelope")
                            .initCause(e);
                }
            }
        }

        final GeneralEnvelope coverageBounds = reader.getOriginalEnvelope();
        // just do the intersection since
        requestEnvelope.intersect(coverageBounds);

        if (requestEnvelope.isEmpty()) {
            return null;
        }

        requestEnvelope.setCoordinateReferenceSystem(destCRS);

        final MathTransform originalGridToWorld = reader
                .getOriginalGridToWorld(PixelInCell.CELL_CORNER);
        MathTransform worldToGrid;
        try {
            worldToGrid = originalGridToWorld.inverse();
        } catch (NoninvertibleTransformException e) {
            throw new RuntimeException(e);
        }
        Rectangle2D requestGridRange;
        try {
            requestGridRange = CRS.transform(worldToGrid, requestEnvelope).toRectangle2D();
        } catch (IllegalStateException e) {
            throw new RuntimeException(e);
        } catch (TransformException e) {
            throw new RuntimeException(e);
        }

        // /////////////////////////////////////////////////////////
        //
        // Reading the coverage
        //
        // /////////////////////////////////////////////////////////
        final Parameter<GridGeometry2D> readGG = new Parameter<GridGeometry2D>(
                AbstractGridFormat.READ_GRIDGEOMETRY2D);
        readGG.setValue(new GridGeometry2D(new GridEnvelope2D(requestGridRange.getBounds()),
                requestEnvelope));

        GeneralParameterValue[] parameters = new GeneralParameterValue[] { readGG };

        GridCoverage2D gc = reader.read(parameters);

        if ((gc == null) || !(gc instanceof GridCoverage2D)) {
            throw new IOException("The requested coverage could not be found.");
        }

        return gc;
    }

}
