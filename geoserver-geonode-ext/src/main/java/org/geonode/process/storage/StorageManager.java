package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;
import java.security.SecureRandom;

import org.geoserver.platform.GeoServerResourceLoader;

public class StorageManager {

    private final GeoServerResourceLoader resourceLoader;

    private String rootDir;

    private final String processDir;

    private static final SecureRandom random = new SecureRandom();

    /**
     * To be lazily created by {@link #getBaseDir()}. Hence do not use it directly.
     */
    private FileSystemFolder baseDir;

    public StorageManager(final GeoServerResourceLoader resourceLoader, final String rootDir,
            final String processDir) {
        this.resourceLoader = resourceLoader;
        this.rootDir = rootDir;
        this.processDir = processDir;
    }

    /**
     * Disposes all the resources handled by this storage manager and returns whether the operation
     * was successful or not
     * 
     * @return {@code true} if the directory managed by this instance was successfully deleted or it
     *         didn't exist, {@code false} if it was not possible to delete the directory and all
     *         its contents.
     */
    public boolean dispose() {
        if (baseDir != null && baseDir.exists()) {
            try {
                baseDir.delete();
            } catch (IOException e) {
                return false;
            }
        }
        return true;
    }

    private FileSystemFolder getBaseDir() throws IOException {
        if (baseDir == null) {
            File baseDirectory = resourceLoader.createDirectory(rootDir, processDir);
            baseDir = new FileSystemFolder(baseDirectory);
        }
        return baseDir;
    }

    public Resource createTempResource() throws IOException {
        FileSystemFolder baseDir = getBaseDir();
        String fileName = Math.abs(random.nextLong()) + ".tmp";
        Resource resource = baseDir.createResource(fileName);
        return resource;
    }

    public Resource createFile(String name) throws IOException {
        FileSystemFolder baseDir = getBaseDir();
        Resource file = baseDir.createResource(name);
        return file;
    }

    public Folder createTempFolder() throws IOException {
        FileSystemFolder baseDir = getBaseDir();
        String folderName = Math.abs(random.nextLong()) + ".tmp";
        Folder folder = baseDir.createFolder(folderName);
        return folder;
    }
}
