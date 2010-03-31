package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.URL;

/**
 * Represents a handle to a physical storage unit such as a file in a file system.
 * <p>
 * The existence of an instance of this class does not guarantee the existence of the actual
 * physical resource. It is up to the implementation to decide whether to create the resource lazily
 * or not when either {@link #getInputStream()} or {@link #getOutputStream()} is first called.
 * </p>
 * 
 * @author Gabriel Roldan
 * @version $Id$
 */
public interface Resource {

    /**
     * Creates an output stream to the resource referenced by this object.
     * <p>
     * 
     * </p>
     * 
     * @return
     * @throws IOException
     */
    public OutputStream getOutputStream() throws IOException;

    public InputStream getInputStream() throws IOException;

    /**
     * Checks whether the resource referenced has been opened either by {@link #getOutputStream()}
     * or {@link #getInputStream()} and the resuling stream has not been closed yet.
     * <p>
     * If there is an open stream for the resource referenced neither {@link #getOutputStream()} nor
     * {@link #getInputStream()} can be called again, resulting in an exception.
     * </p>
     * 
     * @return
     */
    public boolean isOpen();

    /**
     * Deletes the underlying physical resource, or returns silently if it does not exist
     * 
     * @throws IOException
     *             if resource is open or can't be deleted by any other reason
     */
    public void delete() throws IOException;

    public Folder getParent();

    public File getFile() throws IOException;

    public URL getURL() throws IOException;

    public URI getURI() throws IOException;
}
