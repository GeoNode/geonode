package org.geonode.process.storage;

import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;

class CheckedInputStream extends FilterInputStream {

    public boolean open;

    public CheckedInputStream(final InputStream in) {
        super(in);
        this.open = true;
    }

    @Override
    public void close() throws IOException {
        super.close();
        open = false;
    }

    public boolean isOpen() {
        return open;
    }
}
