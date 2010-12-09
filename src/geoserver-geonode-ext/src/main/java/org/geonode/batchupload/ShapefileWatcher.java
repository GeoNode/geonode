package org.geonode.batchupload;

import java.io.File;
import java.io.FileFilter;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
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

    /**
     * A Map to track missing needed files before GeoNode is notified of a shapefile upload. The Map
     * key is the shapefile and the values a set of missing file names on that directory.
     */
    private Map<File, Set<File>> waitQueue;

    public ShapefileWatcher(GeoNodeHTTPClient httpClient) {
        super(httpClient);
        waitQueue = new ConcurrentHashMap<File, Set<File>>();
    }

    @Override
    protected boolean canHandle(String filePath) {
        String name = filePath.toLowerCase();
        return name.endsWith(".shp");
    }

    /**
     * If the file starting to be uploaded is a shapefile, adds to the list of missing files any
     * expected accompanying file that's not already in the same directory than {@code fileName}.
     * 
     * @see #onUploadEnd(UserDetails, File, String)
     */
    @Override
    public CallbackAction onUploadStart(final UserDetails user, final File workingDir,
            final String fileName) {
        /*
         * Check if it's a shapefile and its accompanying files are missing. Add any missing file to
         * the wait queue here on upload start to be checked at onUploadEnd. Otherwise the file may
         * exist but may have not yet finished uploading.
         */
        if (canHandle(fileName)) {
            String baseName = FilenameUtils.getBaseName(fileName);
            final File dbf = new File(workingDir, baseName + ".dbf");
            final File shx = new File(workingDir, baseName + ".shx");
            // final File prj = new File(workingDir, baseName + ".prj");

            File[] existingFiles = workingDir.listFiles(new FileFilter() {
                public boolean accept(File pathname) {
                    /*
                     * Use File.equals() to check for existence. It takes care for lexicographic
                     * case comparisons depending on whether the file system is case sensitive or
                     * not.
                     */
                    if (dbf.equals(pathname) || shx.equals(pathname)) {// || prj.equals(pathname)) {
                        return true;
                    }
                    return false;
                }
            });

            Set<File> missingFiles = new HashSet<File>(Arrays.asList(dbf, shx));// , prj));
            missingFiles.removeAll(Arrays.asList(existingFiles));
            missingFiles = Collections.synchronizedSet(missingFiles);

            if (missingFiles.size() > 0) {
                LOGGER.info("When shapefile " + fileName
                        + " finishes uploading we'll have to wait for " + missingFiles
                        + " before notifying GeoNode");
                File shapeFile = new File(workingDir, fileName);
                this.waitQueue.put(shapeFile, missingFiles);
            }
        }
        return super.onUploadStart(user, workingDir, fileName);
    }

    @Override
    public CallbackAction onUploadEnd(final UserDetails user, final File workingDir,
            final String fileName) {
        /*
         * Is is one of the missing files? if so and it's the last one, proceed to notifyUpload
         */
        String extension = FilenameUtils.getExtension(fileName).toLowerCase();
        if ("dbf".equals(extension) || "shx".equals(extension)) {
            String shapefileName = FilenameUtils.getBaseName(fileName) + ".shp";
            File shapefile = new File(workingDir, shapefileName);
            if (shapefile.exists()) {
                Set<File> missingFiles = waitQueue.get(shapefile);
                File file = new File(workingDir, fileName);
                if (missingFiles != null) {
                    boolean removed = missingFiles.remove(file);
                    if (removed) {
                        LOGGER.info("Missing file " + fileName + " just uploaded.");
                    }
                    if (missingFiles.size() == 0) {
                        LOGGER.info("All " + shapefileName
                                + " accompanying files finished uploading, notifying GeoNode...");
                        notifyUpload(user, shapefile);
                    } else {
                        LOGGER.info("There're still " + missingFiles.size()
                                + " accompanying files before notifying GeoNode of "
                                + shapefileName);
                    }
                }
                // shapefile was uploaded
            }
        }
        return super.onUploadEnd(user, workingDir, fileName);
    }

    @Override
    public void notifyUpload(final UserDetails user, final File file) {
        Set<File> missingFiles = waitQueue.get(file);
        if (missingFiles == null || missingFiles.size() == 0) {
            super.notifyUpload(user, file);
        } else {
            LOGGER.info("Can't notify of shapefile upload yet as the following files are still missing: "
                    + missingFiles + ". Will notify GeoNode once they're uploaded");
        }
    }
}
