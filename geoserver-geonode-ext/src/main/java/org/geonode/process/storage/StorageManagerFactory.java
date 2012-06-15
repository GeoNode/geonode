package org.geonode.process.storage;

import java.io.IOException;

public interface StorageManagerFactory {

    public StorageManager newStorageManager(final String name) throws IOException;

}
