package org.geonode.batchupload;

import static org.geoserver.ftp.CallbackAction.CONTINUE;

import java.io.File;
import java.net.URL;
import java.util.List;
import java.util.logging.Logger;

import org.acegisecurity.userdetails.UserDetails;
import org.geonode.http.GeoNodeHTTPClient;
import org.geoserver.ftp.CallbackAction;
import org.geoserver.ftp.DefaultFTPCallback;
import org.geotools.util.logging.Logging;

public abstract class GeoNodeBatchUploadNotifier extends DefaultFTPCallback {

    private static final Logger LOGGER = Logging.getLogger(GeoNodeBatchUploadNotifier.class);

    private final GeoNodeHTTPClient httpClient;

    /**
     * 
     */
    public GeoNodeBatchUploadNotifier(final GeoNodeHTTPClient httpClient) {
        this.httpClient = httpClient;
    }

    /**
     * Delegates to {@link #canHandle(String) canHandle(String fileName)} with
     * {@code file.getAbsolutePath()}; subclasses may override as needed.
     * 
     * @param file
     * @return
     */
    protected boolean canHandle(final File file) {
        return canHandle(file.getAbsolutePath());
    }

    protected abstract boolean canHandle(final String filePath);

    protected String extension(String fileName) {
        int separatorIdx = fileName.lastIndexOf('.');
        if (separatorIdx == -1) {
            return null;
        }
        String extension = fileName.substring(separatorIdx + 1);
        return extension;
    }

    /**
     * Notifies GeoNode that a spatial data file has been uploaded and hence should be published
     */
    public CallbackAction onUploadEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            String userName = user.getUsername();
            notifyUpload(userName, file, null);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that a spatial data file has been deleted and hence should be unpublished
     */
    public CallbackAction onDeleteEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            String userName = user.getUsername();
            notifyDeletion(userName, file, null);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that an upload resume on a previously truncated spatial data file finished
     */
    public CallbackAction onAppendEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            String userName = user.getUsername();
            notifyUpload(userName, file, null);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode of changes in the location of spatial data files
     */
    public CallbackAction onRenameEnd(UserDetails user, File workingDir, File renameFrom,
            File renameTo) {
        if (canHandle(renameTo)) {
            String userName = user.getUsername();
            notifyMove(userName, renameFrom, renameTo, null);
        }
        return CONTINUE;
    }

    private URL getGeoNodeBatchUploadURL() {
        // TODO Auto-generated method stub
        return null;
    }

    /**
     * Notifies GeoNode that the given {@code file} and, if present, its {@code accompanying} files
     * have been uploaded.
     * 
     * @param userName
     *            the user performing the operation
     * @param file
     *            the spatial dataset file that has been uploaded
     * @param accompanying
     *            any extra file that together with the main {@code file} compose the whole spatial
     *            dataset
     */
    public void notifyUpload(final String userName, final File file, final List<File> accompanying) {
        LOGGER.warning("Notifying GeoNode of an upload: " + file.getAbsolutePath());
        URL url = getGeoNodeBatchUploadURL();
        byte[] contents = null;
        httpClient.sendPOST(url, contents);
    }

    public void notifyDeletion(String userName, File file, Object object) {
        LOGGER.warning(getClass().getSimpleName() + ".notifyDeletion not yet implemented");
    }

    public void notifyMove(String userName, File renameFrom, File renameTo, Object object) {
        LOGGER.warning(getClass().getSimpleName() + ".notifyMove not yet implemented");
    }

}
