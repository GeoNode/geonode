package org.geonode.process.storage;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.URL;

class FileResource implements Resource {

    private File file;

    private CheckedInputStream inputStream;

    private CheckedOutputStream outputStream;

    private FileSystemFolder parent;

    public FileResource(final FileSystemFolder parent, final File file) {
        this.parent = parent;
        this.file = file;
    }

    public InputStream getInputStream() throws IOException {
        if (isOpen()) {
            throw new IOException("Stream already open");
        }
        inputStream = new CheckedInputStream(new FileInputStream(file));
        outputStream = null;
        return inputStream;
    }

    public OutputStream getOutputStream() throws IOException {
        if (isOpen()) {
            throw new IOException("Stream already open");
        }
        outputStream = new CheckedOutputStream(new FileOutputStream(file));
        inputStream = null;
        return outputStream;
    }

    public boolean isOpen() {
        boolean inOpen = inputStream != null && inputStream.isOpen();
        boolean outOpen = outputStream != null && outputStream.isOpen();
        return inOpen || outOpen;
    }

    public void delete() throws IOException {
        if (isOpen()) {
            throw new IOException("Resource is open");
        }
        if (file.exists() && !file.delete()) {
            throw new IOException("Couldn't delete " + file.getAbsolutePath());
        }
    }

    public Folder getParent() {
        return parent;
    }

    public File getFile() throws IOException {
        return file;
    }

    public URI getURI() throws IOException {
        return getFile().toURI();
    }

    public URL getURL() throws IOException {
        return getURI().toURL();
    }
}
