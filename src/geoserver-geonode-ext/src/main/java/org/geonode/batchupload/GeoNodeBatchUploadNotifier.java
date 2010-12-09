package org.geonode.batchupload;

import static org.geoserver.ftp.CallbackAction.CONTINUE;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.acegisecurity.userdetails.UserDetails;
import org.geonode.http.GeoNodeHTTPClient;
import org.geoserver.ftp.CallbackAction;
import org.geoserver.ftp.DefaultFTPCallback;
import org.geoserver.ftp.FTPCallback;
import org.geotools.util.logging.Logging;

/**
 * Base class for FTP activity notification to GeoNode.
 * <p>
 * This class implements {@link FTPCallback} in order to be notified of GeoServer's FTP file
 * activity.
 * </p>
 * <p>
 * Concrete subclasses indicate whether they can hanlde the upload, deletion or move for a given
 * file through the {@link #canHandle(String)} and {@link #canHandle(File)} methods. If
 * {@link #canHandle(File)} returns {@code true} at any of the {@link #onUploadEnd}
 * {@link #onDeleteEnd} or {@link #onRenameEnd} FTP callbaks, {@link #notifyUpload},
 * {@link #notifyDeletion} or {@link #notifyMove} will be called accordingly.
 * </p>
 * <p>
 * The GeoNode end point {@code GEONODE_BASE_URL/debug} (@TODO: update URL) will be called with a
 * POST request containing the following form url encoded arguments:
 * <ul>
 * <li>operation: one of {@code UPLOAD|DELETE|MOVE}
 * <li>user: the user name performing the operation
 * <li>file: the absolute path of the file
 * <li>fileURL: the location of the file as a {@code file://} URL
 * <li>renameFromFile: the absolute path of the file that's been renamed as {@code file}. Only if
 * {@code operation == MOVE}
 * <li>renameFromURL: the {@code file://} URL of the file that's been renamed as {@code file}. Only
 * if {@code operation == MOVE}
 * </ul>
 * </p>
 * 
 * @author groldan
 * 
 */
public abstract class GeoNodeBatchUploadNotifier extends DefaultFTPCallback {

    private static final Logger LOGGER = Logging.getLogger(GeoNodeBatchUploadNotifier.class);

    private static enum Operation {
        UPLOAD, DELETE, MOVE
    }

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

    /**
     * Notifies GeoNode that a spatial data file has been uploaded and hence should be published
     */
    public CallbackAction onUploadEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            notifyUpload(user, file);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that a spatial data file has been deleted and hence should be unpublished
     */
    public CallbackAction onDeleteEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            notifyDeletion(user, file);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that an upload resume on a previously truncated spatial data file finished
     */
    public CallbackAction onAppendEnd(UserDetails user, File workingDir, String fileName) {
        File file = new File(workingDir, fileName);
        if (canHandle(file)) {
            notifyUpload(user, file);
        }
        return CONTINUE;
    }

    /**
     * Notifies GeoNode of changes in the location of spatial data files
     */
    public CallbackAction onRenameEnd(UserDetails user, File workingDir, File renameFrom,
            File renameTo) {
        if (canHandle(renameTo)) {
            notifyMove(user, renameFrom, renameTo, null);
        }
        return CONTINUE;
    }

    private String getGeoNodeBatchUploadURL() {
        URL baseURL = this.httpClient.getBaseURL();
        try {
            return new URL(baseURL, "debug/").toExternalForm();
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Notifies GeoNode that the given {@code file} has been uploaded by the given user
     */
    public void notifyUpload(final UserDetails user, final File file) {
        LOGGER.fine("Notifying GeoNode of an upload: " + file.getAbsolutePath());
        String fileURL;
        try {
            fileURL = file.toURI().toURL().toString();
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }
        notifyGeoNode(user, Operation.UPLOAD, "file", file.getAbsolutePath(), "fileURL", fileURL);
        LOGGER.fine("UPLOAD notification succeeded for " + file.getAbsolutePath());
    }

    /**
     * Notifies GeoNode that the given {@code file} has been deleted by the given user
     */
    public void notifyDeletion(UserDetails user, File file) {
        LOGGER.fine("Notifying GeoNode of a deletion: " + file.getAbsolutePath());
        String fileURL;
        try {
            fileURL = file.toURI().toURL().toString();
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }
        notifyGeoNode(user, Operation.DELETE, "file", file.getAbsolutePath(), "fileURL", fileURL);
        LOGGER.fine("DELETE notification succeeded for " + file.getAbsolutePath());
    }

    /**
     * Notifies GeoNode that the given {@code renameFrom} file has been moved to {@code renameTo}
     */
    public void notifyMove(UserDetails user, File renameFrom, File renameTo, Object object) {
        LOGGER.fine("Notifying GeoNode of an moved file: " + renameFrom.getAbsolutePath() + " to "
                + renameTo.getAbsolutePath());
        String fileURL;
        String fromFileURL;
        try {
            fileURL = renameTo.toURI().toURL().toString();
            fromFileURL = renameFrom.toURI().toURL().toString();
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }

        notifyGeoNode(user, Operation.MOVE, "file", renameTo.getAbsolutePath(), "fileURL", fileURL,
                "renameFromFile", renameFrom.getAbsolutePath(), "renameFromURL", fromFileURL);
        LOGGER.fine("MOVE notification succeeded " + renameTo.getAbsolutePath() + " was "
                + renameFrom.getAbsolutePath());
    }

    private void notifyGeoNode(final UserDetails user, final Operation operation,
            final String... parameters) {

        String userName = user.getUsername();
        String password = user.getPassword();

        String url = getGeoNodeBatchUploadURL();
        Map<String, String> params = new HashMap<String, String>();
        params.put("operation", operation.name());
        params.put("user", userName);
        for (int i = 0; i < parameters.length; i += 2) {
            params.put(parameters[i], parameters[i + 1]);
        }
        try {
            httpClient.sendPOST(url, params, userName, password);
        } catch (IOException e) {
            LOGGER.log(Level.WARNING, "Error notifying GeoNode. Operation: " + operation
                    + ", params: " + params, e);
            throw new RuntimeException(e);
        }
    }
}
