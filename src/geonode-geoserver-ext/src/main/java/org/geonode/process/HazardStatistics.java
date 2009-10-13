package org.geonode.process;

import static org.geonode.process.HazardStatisticsFactory.DATALAYER;
import static org.geonode.process.HazardStatisticsFactory.GEOMERTY;
import static org.geonode.process.HazardStatisticsFactory.RADIUS;

import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.media.jai.Histogram;

import org.geotools.coverage.grid.GridCoverage2D;
import org.geotools.coverage.grid.GridEnvelope2D;
import org.geotools.coverage.grid.GridGeometry2D;
import org.geotools.coverage.grid.ViewType;
import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.coverage.grid.io.AbstractGridFormat;
import org.geotools.coverage.processing.OperationJAI;
import org.geotools.geometry.GeneralEnvelope;
import org.geotools.geometry.jts.ReferencedEnvelope;
import org.geotools.parameter.Parameter;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.process.ProcessFactory;
import org.geotools.process.impl.AbstractProcess;
import org.geotools.referencing.CRS;
import org.opengis.parameter.GeneralParameterValue;
import org.opengis.parameter.ParameterValueGroup;
import org.opengis.referencing.FactoryException;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import org.opengis.referencing.datum.PixelInCell;
import org.opengis.referencing.operation.MathTransform;
import org.opengis.referencing.operation.NoninvertibleTransformException;
import org.opengis.referencing.operation.TransformException;
import org.opengis.util.ProgressListener;

import com.vividsolutions.jts.geom.Geometry;

final class HazardStatistics extends AbstractProcess {

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

        /**
         * CoverageReaders have no Name, so we return a list of results in the same order than the
         * provided readers for client code to match them up
         */
        List<Map<String, double[]>> perLayerStats = new ArrayList<Map<String, double[]>>();
        for (AbstractGridCoverage2DReader layer : inputDataLayers) {
            Map<String, double[]> stats = gatherCoverageStats(layer, bufferedGeometry);
            perLayerStats.add(stats == null? null : new HashMap<String, double[]>(stats));
        }

        Map<String, Object> results = new HashMap<String, Object>();

        results.put(HazardStatisticsFactory.RESULT_STATISTICS.key, perLayerStats);

        // TODO: un-fake
        HashMap<String, Object> politicalData = new HashMap<String, Object>();
        politicalData.put("country", "Tasmania");
        politicalData.put("municipality", "Bicheno");

        results.put(HazardStatisticsFactory.RESULT_POLITICAL.key, politicalData);

        return results;
    }

    private Map<String, double[]> gatherCoverageStats(final AbstractGridCoverage2DReader layer,
            final Geometry bufferedGeometry) throws ProcessException {

        final GridCoverage2D geophysics;
        try {
            final ReferencedEnvelope requesEnvelope;
            final CoordinateReferenceSystem crs = layer.getCrs();
            requesEnvelope = new ReferencedEnvelope(bufferedGeometry.getEnvelopeInternal(), crs);

            GridCoverage2D coverage = getGridCoverage(layer, requesEnvelope);
            if (coverage == null) {
                // request envelope did not intersect coverage, return null stats
                return null;
            } else {
                geophysics = coverage.view(ViewType.GEOPHYSICS);
            }
        } catch (IOException e) {
            throw new ProcessException(e);
        }

        final OperationJAI op = new OperationJAI("Histogram");
        ParameterValueGroup params = op.getParameters();
        params.parameter("Source").setValue(geophysics);

        GridCoverage2D coverage = (GridCoverage2D) op.doOperation(params, null);
        Histogram histogram = (Histogram) coverage.getProperty("histogram");

        Map<String, double[]> stats = new HashMap<String, double[]>();
        stats.put("min", histogram.getLowValue());
        stats.put("max", histogram.getHighValue());
        stats.put("mean", histogram.getMean());
        stats.put("stddev", histogram.getStandardDeviation());

        return stats;
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
    @SuppressWarnings("deprecation")
    public GridCoverage2D getGridCoverage(final AbstractGridCoverage2DReader reader,
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
