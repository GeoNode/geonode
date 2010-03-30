package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;

import org.geoserver.platform.GeoServerResourceLoader;
import org.springframework.core.io.Resource;

public class GeoServerDataDirStorageManagerFactory implements StorageManagerFactory {

    private GeoServerResourceLoader resourceLoader;

    private String processesTemptDir;

    public GeoServerDataDirStorageManagerFactory(final GeoServerResourceLoader resourceLoader,
            final String baseDirName) {
        this.resourceLoader = resourceLoader;
        this.processesTemptDir = baseDirName;

        Resource resource = resourceLoader.getResource(processesTemptDir);
        if (!resource.exists()) {
            File baseDir;
            try {
                baseDir = resource.getFile();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
            baseDir.mkdirs();
            if (!baseDir.exists()) {
                throw new IllegalStateException("Couldn't create directory "
                        + baseDir.getAbsolutePath());
            }
        }
    }

    public StorageManager newStorageManager(final String name) throws IOException {
        return new StorageManager(resourceLoader, processesTemptDir, name);
    }
}
