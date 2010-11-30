package org.geonode.batchupload;

import static org.geoserver.ftp.CallbackAction.CONTINUE;

import java.io.File;
import java.util.List;
import java.util.logging.Logger;

import org.acegisecurity.userdetails.UserDetails;
import org.geoserver.ftp.CallbackAction;
import org.geoserver.ftp.DefaultFTPCallback;
import org.geotools.util.logging.Logging;

public class GeoNodeBatchUploadNotifier extends DefaultFTPCallback {

    private static final Logger LOGGER = Logging.getLogger(GeoNodeBatchUploadNotifier.class);

    /**
     * 
     * @param fileExtentions
     *            list of file extensions to recognize a file is one that GeoNode needs to know of
     *            (e.g. [.shp, .tiff])
     */
    public GeoNodeBatchUploadNotifier(final List<String> fileExtentions) {

    }

    /**
     * Notifies GeoNode that a spatial data file has been uploaded and hence should be published
     */
    public CallbackAction onUploadEnd(UserDetails user, File workingDir, String fileName) {
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that a spatial data file has been deleted and hence should be unpublished
     */
    public CallbackAction onDeleteEnd(UserDetails user, File workingDir, String fileName) {
        return CONTINUE;
    }

    /**
     * Notifies GeoNode that an upload resume on a previously truncated spatial data file finished
     */
    public CallbackAction onAppendEnd(UserDetails user, File workingDir, String fileName) {
        return CONTINUE;
    }

    /**
     * Notifies GeoNode of changes in the location of spatial data files
     */
    public CallbackAction onRenameEnd(UserDetails user, File workingDir, File renameFrom,
            File renameTo) {
        return CONTINUE;
    }
}
