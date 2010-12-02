package org.geonode.batchupload;

import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.geonode.http.GeoNodeHTTPClient;
import org.geoserver.platform.GeoServerExtensions;
import org.geotools.util.logging.Logging;
import org.springframework.util.Assert;

/**
 * Decorating {@link SpatialFileWatcher} that captures ZIP file uploads an notifies GeoNode of any
 * spatial file contained in the ZIP file by first uncompressing the file.
 * 
 * @author groldan
 */
public class ArchiveFileWatcher extends GeoNodeBatchUploadNotifier {

    private static final Logger LOGGER = Logging.getLogger(ArchiveFileWatcher.class);

    private VFSWorker vfsWorker;

    public ArchiveFileWatcher(GeoNodeHTTPClient httpClient) {
        super(httpClient);
        // TODO: make vfsWorker a constructor argument and a Spring bean?
        this.vfsWorker = new VFSWorker();
    }

    @Override
    protected boolean canHandle(String filePath) {
        File file = new File(filePath);
        if (!file.exists()) {
            /*
             * We're not interested in notifying deletes for archived files since they're
             * uncompressed automatically when uploaded, so we can still rely on the virtual file
             * system worker's canHandle() method only for existing files
             */
            return false;
        }
        return vfsWorker.canHandle(file);
    }

    @Override
    protected boolean canHandle(final File file) {
        if (!vfsWorker.canHandle(file)) {
            return false;
        }
        // does the zip contains more spatial files?
        final List<GeoNodeBatchUploadNotifier> notifiers = getNotifiers();
        FilenameFilter fileNameFilter = getNotifyableFiles(notifiers);

        List<String> containedSpatialFiles = this.vfsWorker.listFiles(file, fileNameFilter);
        if (LOGGER.isLoggable(Level.FINE)) {
            LOGGER.fine("Found the following spatial files in the archive "
                    + file.getAbsolutePath() + ": " + containedSpatialFiles);
        }
        boolean canHandle = containedSpatialFiles.size() > 0;
        return canHandle;
    }

    private FilenameFilter getNotifyableFiles(final List<GeoNodeBatchUploadNotifier> notifiers) {
        FilenameFilter fileNameFilter = new FilenameFilter() {
            /**
             * @see java.io.FilenameFilter#accept(java.io.File, java.lang.String)
             */
            public boolean accept(File dir, String name) {
                for (GeoNodeBatchUploadNotifier watcher : notifiers) {
                    if (watcher.canHandle(name)) {
                        return true;
                    }
                }
                return false;
            }
        };
        return fileNameFilter;
    }

    @Override
    public void notifyUpload(final String userName, final File file, final List<File> accompanying) {
        LOGGER.info("Uncompressing ZIP file " + file.getAbsolutePath()
                + " before notifying of it's contained spatial datasets...");

        final File targetFolder = new File(file.getParentFile(), stripExtension(file.getName()));
        Assert.isTrue(!targetFolder.exists());
        Assert.isTrue(targetFolder.mkdir());

        // extract the archive file (.zip, .tgz, etc) to the target folder
        vfsWorker.extractTo(file, targetFolder);

        LOGGER.info("Archive " + file.getAbsolutePath() + " uncompressed");

        // traverse the extracted files and delegate as appropriate
        final List<GeoNodeBatchUploadNotifier> notifiers = getNotifiers();
        FilenameFilter fileNameFilter = getNotifyableFiles(notifiers);
        List<String> spatialFiles = vfsWorker.listFiles(targetFolder, fileNameFilter);
        LOGGER.info("Uncompressed folder contains the following spatial data files: "
                + spatialFiles);
        for (String filePath : spatialFiles) {
            for (GeoNodeBatchUploadNotifier notifier : notifiers) {
                File spatialFile = new File(filePath);
                if (notifier.canHandle(spatialFile)) {
                    notifier.notifyUpload(userName, spatialFile, accompanying);
                }
            }
        }
    }

    private String stripExtension(String name) {
        if (name.lastIndexOf('.') > 0) {
            name = name.substring(0, name.lastIndexOf('.'));
        }
        return name;
    }

    private List<GeoNodeBatchUploadNotifier> getNotifiers() {
        List<GeoNodeBatchUploadNotifier> extensions;
        extensions = GeoServerExtensions.extensions(GeoNodeBatchUploadNotifier.class);
        extensions = new ArrayList<GeoNodeBatchUploadNotifier>(extensions);
        extensions.remove(this);
        return extensions;
    }
}
