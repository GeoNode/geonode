package org.geonode.process.batchdownload;

import static org.geonode.process.batchdownload.BatchDownloadFactory.LAYERS;
import static org.geonode.process.batchdownload.BatchDownloadFactory.MAP_METADATA;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.zip.ZipOutputStream;

import org.geonode.process.batchdownload.geotiff.ZippedGeoTiffCoverageWriter;
import org.geonode.process.batchdownload.shp.ShapeZipWriter;
import org.geonode.process.control.AsyncProcess;
import org.geonode.process.storage.Folder;
import org.geonode.process.storage.Resource;
import org.geonode.process.storage.StorageManager;
import org.geotools.coverage.grid.GridCoverage2D;
import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.data.FeatureSource;
import org.geotools.data.Query;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.text.Text;
import org.geotools.util.SubProgressListener;
import org.geotools.util.logging.Logging;
import org.opengis.feature.simple.SimpleFeature;
import org.opengis.feature.simple.SimpleFeatureType;
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

        monitor.started();
        if (null == getStorageManager()) {
            throw new IllegalStateException("No StorageManager has been provided");
        }
        final MapMetadata mapDetails = (MapMetadata) input.get(MAP_METADATA.key);
        final List<LayerReference> layers = (List<LayerReference>) input.get(LAYERS.key);

        if (monitor.isCanceled()) {
            return null;
        }

        checkInputs(mapDetails, layers);

        if (monitor.isCanceled()) {
            return null;
        }

        Resource zipFileHandle = buildZippFile(mapDetails, layers, monitor);

        if (monitor.isCanceled()) {
            return null;
        }

        Map<String, Object> results = new HashMap<String, Object>();
        results.put(BatchDownloadFactory.RESULT_ZIP.key, zipFileHandle);

        monitor.complete();
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

    private Resource buildZippFile(final MapMetadata mapDetails, final List<LayerReference> layers,
            final ProgressListener monitor) throws ProcessException {

        LOGGER.fine("Building zip file for map " + mapDetails.getTitle());

        final StorageManager storageManager = getStorageManager();
        final int nLayers = layers.size();

        final String mapName = mapDetails.getTitle();
        final Resource zipFile = getTargetFileHandle(mapName, storageManager);
        final ZipOutputStream zipOut;
        {
            OutputStream outputStream;
            try {
                outputStream = zipFile.getOutputStream();
            } catch (IOException e) {
                throw new ProcessException("Unable to get a handle to the target file", e);
            }
            zipOut = new ZipOutputStream(outputStream);
        }
        try {
            final float layerProgressAmount = 100F / nLayers;
            LayerReference layerRef;
            ProgressListener layerMonitor;
            for (int layerN = 0; layerN < nLayers; layerN++) {
                layerRef = layers.get(layerN);
                layerMonitor = new SubProgressListener(monitor, layerProgressAmount);
                zipLayer(layerRef, zipOut, layerMonitor);
            }
            try {
                zipOut.finish();
                zipOut.flush();
            } catch (IOException e) {
                throw new ProcessException(e);
            }
        } finally {
            try {
                zipOut.close();
            } catch (IOException e) {
                LOGGER.info("Error closing zip file: " + e.getMessage());
            }
        }

        return zipFile;
    }

    private Resource getTargetFileHandle(final String mapName, final StorageManager storageManager) {

        String fileName = mapName + ".zip";// TODO: replace strange characters?
        Resource zipFileHandle;
        try {
            zipFileHandle = storageManager.createFile(fileName);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return zipFileHandle;
    }

    private void zipLayer(final LayerReference layerRef, final ZipOutputStream zipOut,
            final ProgressListener monitor) throws ProcessException {

        monitor.started();
        monitor.setTask(Text.text("Compressing layer " + layerRef.getName()));
        if (LOGGER.isLoggable(Level.FINER)) {
            LOGGER.finer("Compressing layer " + layerRef.getName());
        }

        try {
            switch (layerRef.getKind()) {
            case VECTOR:
                zipVectorLayer(layerRef, zipOut, monitor);
                break;
            case RASTER:
                zipRasterLayer(layerRef, zipOut, monitor);
                break;
            default:
                throw new IllegalArgumentException("Unknown layer type");
            }
        } catch (IOException e) {
            throw new ProcessException(e);
        }

        monitor.complete();
    }

    @SuppressWarnings("unchecked")
    private void zipVectorLayer(final LayerReference layerRef, final ZipOutputStream zipOut,
            final ProgressListener monitor) throws IOException {

        FeatureSource<SimpleFeatureType, SimpleFeature> vectorSource;
        vectorSource = (FeatureSource<SimpleFeatureType, SimpleFeature>) layerRef.getVectorSource();

        LOGGER.finest("Obtaining layer's feature collection...");

        Charset defaultCharset = Charset.forName("UTF-8");

        LOGGER.finest("Creating temp folder to hold layer's shapefiles...");
        Folder tmpDir = getStorageManager().createTempFolder();
        try {
            File tempDir = tmpDir.getFile();

            ShapeZipWriter shapeArchiver = new ShapeZipWriter();
            shapeArchiver.write(vectorSource, Query.ALL, zipOut, defaultCharset, tempDir, monitor);
        } finally {
            tmpDir.delete();
        }
    }

    private void zipRasterLayer(final LayerReference layerRef, final ZipOutputStream zipOut,
            final ProgressListener monitor) throws IOException {

        final AbstractGridCoverage2DReader reader = layerRef.getRasterSource();

        // read coverage
        final GridCoverage2D coverage2d = reader.read(null);

        ZippedGeoTiffCoverageWriter writer = new ZippedGeoTiffCoverageWriter();

        String name = layerRef.getName();
        writer.write(name, coverage2d, zipOut, monitor);
    }
}
