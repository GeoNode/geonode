package org.geonode.process.storage;

import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.OutputStream;

class CheckedOutputStream extends FilterOutputStream {

    private boolean open;

    public CheckedOutputStream(final OutputStream out) {
        super(out);
        open = true;
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
