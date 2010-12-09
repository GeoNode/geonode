package org.geonode.batchupload;

import java.io.File;
import java.io.FileFilter;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Logger;

import org.acegisecurity.userdetails.UserDetails;
import org.apache.commons.io.FilenameUtils;
import org.geonode.http.GeoNodeHTTPClient;
import org.geoserver.ftp.CallbackAction;
import org.geotools.util.logging.Logging;

/**
 * GeoNode batch upload notifier that recognizes ShapeFile uploads by comparing the file extensions
 * to {@code .shp}.
 * 
 * @author groldan
 * 
 */
public class ShapefileWatcher extends GeoNodeBatchUploadNotifier {

    private static final Logger LOGGER = Logging.getLogger(ShapefileWatcher.class);

    public ShapefileWatcher(GeoNodeHTTPClient httpClient) {
        super(httpClient);
    }

    @Override
    protected boolean canHandle(String filePath) {
        String name = filePath.toLowerCase();
        return name.endsWith(".shp");
    }

    private Set<File> getMissingFiles(final File shapefile) {
        final File workingDir = shapefile.getParentFile();
        final String fileName = shapefile.getName();
        final String baseName = FilenameUtils.getBaseName(fileName);
        final File dbf = new File(workingDir, baseName + ".dbf");
        final File shx = new File(workingDir, baseName + ".shx");
        // final File prj = new File(workingDir, baseName + ".prj");

        File[] existingFiles = workingDir.listFiles(new FileFilter() {
            public boolean accept(File pathname) {
                /*
                 * Use File.equals() to check for existence. It takes care for lexicographic case
                 * comparisons depending on whether the file system is case sensitive or not.
                 */
                if (dbf.equals(pathname) || shx.equals(pathname)) {// || prj.equals(pathname)) {
                    return true;
                }
                return false;
            }
        });

        Set<File> missingFiles = new HashSet<File>(Arrays.asList(dbf, shx));// , prj));
        missingFiles.removeAll(Arrays.asList(existingFiles));
        return missingFiles;
    }

    @Override
    public CallbackAction onUploadEnd(final UserDetails user, final File workingDir,
            final String fileName) {
        /*
         * Is is one of the missing files? if so and it's the last one, proceed to notifyUpload
         */
        String extension = FilenameUtils.getExtension(fileName).toLowerCase();
        if ("dbf".equals(extension) || "shx".equals(extension)) {
            final String shapefileName = FilenameUtils.getBaseName(fileName) + ".shp";
            final File shapefile = new File(workingDir, shapefileName);
            if (shapefile.exists()) {
                LOGGER.info("Missing file " + fileName + " just uploaded.");
                Set<File> missingFiles = getMissingFiles(shapefile);
                if (missingFiles.size() == 0) {
                    LOGGER.info("All " + shapefileName
                            + " accompanying files finished uploading, notifying GeoNode...");
                    notifyUpload(user, shapefile);
                } else {
                    LOGGER.info("There're still " + missingFiles.size()
                            + " accompanying files before notifying GeoNode of " + shapefileName);
                }
                // shapefile was uploaded
            }
            return CallbackAction.CONTINUE;
        } else {
            return super.onUploadEnd(user, workingDir, fileName);
        }
    }

    @Override
    public void notifyUpload(final UserDetails user, final File shapefile) {
        final Set<File> missingFiles = getMissingFiles(shapefile);
        if (missingFiles == null || missingFiles.size() == 0) {
            super.notifyUpload(user, shapefile);
        } else {
            LOGGER.info("Can't notify of shapefile upload yet as the following files are still missing: "
                    + missingFiles + ". Will notify GeoNode once they're uploaded");
        }
    }
}
