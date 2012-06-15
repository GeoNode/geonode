package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URL;

import org.apache.commons.io.FileUtils;

class FileSystemFolder implements Folder {

    private FileSystemFolder parent;

    private final File directory;

    public FileSystemFolder(final File rootDir) {
        this.parent = null;
        this.directory = rootDir;
    }

    public FileSystemFolder(final FileSystemFolder parent, final String directory) {
        this.parent = parent;
        this.directory = new File(parent.getFile(), directory);
    }

    public File getFile() {
        return directory;
    }

    public boolean create() throws IOException {
        return directory.mkdirs();
    }

    public Folder createFolder(String... relativePath) throws IOException {
        if (relativePath == null || relativePath.length == 0) {
            throw new NullPointerException();
        }

        final int length = relativePath.length;

        FileSystemFolder parent = this;
        for (int i = 0; i < length; i++) {
            FileSystemFolder folder = new FileSystemFolder(parent, relativePath[i]);
            parent = folder;
        }

        File dir = parent.getFile();
        if (!dir.exists()) {
            if (!dir.mkdirs()) {
                throw new IOException("Can't create folder " + dir.getAbsolutePath());
            }
        }
        return parent;
    }

    public Resource createResource(String... relativePath) throws IOException {
        if (relativePath == null || relativePath.length == 0) {
            throw new NullPointerException();
        }

        final int length = relativePath.length;

        FileSystemFolder parent = this;

        for (int i = 0; i < length - 1; i++) {
            FileSystemFolder folder = new FileSystemFolder(parent, relativePath[i]);
            parent = folder;
        }

        File dir = parent.getFile();
        if (!dir.exists()) {
            if (!dir.mkdirs()) {
                throw new IOException("Can't create folder " + dir.getAbsolutePath());
            }
        }

        String fileName = relativePath[relativePath.length - 1];
        File file = new File(dir, fileName);
        return new FileResource(parent, file);
    }

    public boolean exists() {
        return directory.exists();
    }

    public Folder getParent() {
        return parent;
    }

    public void delete() throws IOException {
        FileUtils.deleteDirectory(directory);
    }

    public URI getURI() throws IOException {
        return getFile().toURI();
    }

    public URL getURL() throws IOException {
        return getURI().toURL();
    }

    public String toString() {
        return new StringBuilder(getClass().getSimpleName()).append("[")
                .append(getFile().getAbsolutePath()).append("]").toString();
    }
}
