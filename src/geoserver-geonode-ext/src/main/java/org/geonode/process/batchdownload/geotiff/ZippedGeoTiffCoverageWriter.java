package org.geonode.process.batchdownload.geotiff;

import java.io.IOException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import org.geotools.coverage.grid.GridCoverage2D;
import org.geotools.coverage.grid.io.AbstractGridFormat;
import org.geotools.coverage.grid.io.imageio.GeoToolsWriteParams;
import org.geotools.gce.geotiff.GeoTiffFormat;
import org.geotools.gce.geotiff.GeoTiffWriteParams;
import org.geotools.gce.geotiff.GeotiffWriterWithProgress;
import org.opengis.parameter.GeneralParameterValue;
import org.opengis.parameter.ParameterValueGroup;
import org.opengis.util.ProgressListener;

public class ZippedGeoTiffCoverageWriter {

    public void write(final String name, final GridCoverage2D coverage,
            final ZipOutputStream zipOut, final ProgressListener monitor) throws IOException {

        final GeoTiffWriteParams wp = new GeoTiffWriteParams();
        // setting compression to LZW
        wp.setCompressionMode(GeoTiffWriteParams.MODE_EXPLICIT);
        wp.setCompressionType("LZW");
        wp.setCompressionQuality(0.75F);

        // setting the tile size to 256X256
        wp.setTilingMode(GeoToolsWriteParams.MODE_EXPLICIT);
        wp.setTiling(256, 256);

        final GeoTiffFormat format = new GeoTiffFormat();
        // setting the write parameters for this geotiff
        final ParameterValueGroup params = format.getWriteParameters();
        params.parameter(AbstractGridFormat.GEOTOOLS_WRITE_PARAMS.getName().toString())
                .setValue(wp);

        final ZipEntry coverageEntry = new ZipEntry(name + ".tiff");
        zipOut.putNextEntry(coverageEntry);

        // get a reader to the input File
        GeotiffWriterWithProgress writer = new GeotiffWriterWithProgress(zipOut);

        // writing the coverage
        writer.write(coverage, (GeneralParameterValue[]) params.values().toArray(
                new GeneralParameterValue[1]), monitor);

        zipOut.closeEntry();
        zipOut.flush();
    }
}
