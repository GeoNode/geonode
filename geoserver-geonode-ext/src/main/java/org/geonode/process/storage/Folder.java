package org.geonode.process.storage;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.URL;

public interface Folder {

    /**
     * Returns the parent folder, which is not guaranteed to exist, or {@code null} if this is the
     * root folder.
     * 
     * @return {@code null} if this is the root folder, the parent folder otherwise
     */
    public Folder getParent();

    /**
     * Deletes the underlying physical folder, or returns silently if it does not exist
     * 
     * @throws IOException
     *             if the folder exists and can't be deleted
     */
    public void delete() throws IOException;

    /**
     * Creates a new folder relative to this one named after the provided list of folder names
     * <p>
     * Upon normal return of this method, the returned folder is guaranteed to exist
     * </p>
     * 
     * @param relativePath
     * @return
     * @throws IOException
     *             if the folder can't be created
     */
    public Folder createFolder(String... relativePath) throws IOException;

    /**
     * Creates a new resource relative to this folder, creating intermediate folders if need be.
     * <p>
     * The last name in the provided {@code relativePath} is taken as the resource name. Any
     * previous name conforms the list of sub folders relative to this one where the resource is to
     * be created.
     * </p>
     * <p>
     * Upon normal return of this method, the resource's parent folder is guaranteed to exist, but
     * the resource may have not been created as specified by {@link Resource}
     * </p>
     * 
     * @param relativePath
     * @return
     * @throws IOException
     */
    public Resource createResource(String... relativePath) throws IOException;

    public boolean exists();

    public boolean create() throws IOException;

    public File getFile() throws IOException;

    public URL getURL() throws IOException;

    public URI getURI() throws IOException;
}
