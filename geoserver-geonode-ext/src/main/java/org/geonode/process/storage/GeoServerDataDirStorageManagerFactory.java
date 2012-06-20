package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;
import java.util.logging.Logger;

import org.geoserver.platform.GeoServerResourceLoader;
import org.geotools.util.logging.Logging;

public class GeoServerDataDirStorageManagerFactory implements StorageManagerFactory {

    private static final Logger LOGGER = Logging
            .getLogger(GeoServerDataDirStorageManagerFactory.class);

    private GeoServerResourceLoader resourceLoader;

    private String processesTemptDir;

    public GeoServerDataDirStorageManagerFactory(final GeoServerResourceLoader resourceLoader,
            final String baseDirName) {
        LOGGER.info("Initializing GeoServer data directory based Process storage manager factory");
        this.resourceLoader = resourceLoader;
        this.processesTemptDir = baseDirName;

        File resource;
        try {
            resource = resourceLoader.findOrCreateDirectory(processesTemptDir);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        if (resource == null || !resource.exists()) {
            throw new IllegalStateException("Directory " + baseDirName
                    + " was not created indide GeoServer data directory");
        }
        LOGGER.info("GeoServer data directory based Process storage"
                + " manager factory initialized to " + resource.getAbsolutePath());
    }

    public StorageManager newStorageManager(final String name) throws IOException {
        return new StorageManager(resourceLoader, processesTemptDir, name);
    }
}
