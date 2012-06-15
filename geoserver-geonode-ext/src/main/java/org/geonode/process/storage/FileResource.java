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

    /**
     * @see org.geonode.process.storage.Resource#getInputStream()
     */
    public InputStream getInputStream() throws IOException {
        if (isOpen()) {
            throw new IOException("Stream already open");
        }
        inputStream = new CheckedInputStream(new FileInputStream(file));
        outputStream = null;
        return inputStream;
    }

    /**
     * @see org.geonode.process.storage.Resource#getOutputStream()
     */
    public OutputStream getOutputStream() throws IOException {
        if (isOpen()) {
            throw new IOException("Stream already open");
        }
        outputStream = new CheckedOutputStream(new FileOutputStream(file));
        inputStream = null;
        return outputStream;
    }

    /**
     * @see org.geonode.process.storage.Resource#isOpen()
     */
    public boolean isOpen() {
        boolean inOpen = inputStream != null && inputStream.isOpen();
        boolean outOpen = outputStream != null && outputStream.isOpen();
        return inOpen || outOpen;
    }

    /**
     * @see org.geonode.process.storage.Resource#delete()
     */
    public void delete() throws IOException {
        if (isOpen()) {
            throw new IOException("Resource is open");
        }
        if (file.exists() && !file.delete()) {
            throw new IOException("Couldn't delete " + file.getAbsolutePath());
        }
    }

    /**
     * @see org.geonode.process.storage.Resource#getParent()
     */
    public Folder getParent() {
        return parent;
    }

    /**
     * @see org.geonode.process.storage.Resource#getFile()
     */
    public File getFile() {
        return file;
    }

    /**
     * @see org.geonode.process.storage.Resource#getURI()
     */
    public URI getURI() {
        return getFile().toURI();
    }

    /**
     * @see org.geonode.process.storage.Resource#getURL()
     */
    public URL getURL() throws IOException {
        return getURI().toURL();
    }

    public String toString() {
        return new StringBuilder(getClass().getSimpleName()).append("[")
                .append(getFile().getAbsolutePath()).append("]").toString();
    }
}
