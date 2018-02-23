package org.ringojs.wrappers;

import org.ringojs.util.POSIXSupport;

import java.security.AccessController;
import java.security.PrivilegedAction;

/**
 * A wrapper class to allow retrieving jnr-posix support while protecting
 * the caller against NoClassDefFoundError if jnr-posix support is not installed.
 */
public class POSIX {

    public static Object getPOSIX() {
        return AccessController.doPrivileged(new PrivilegedAction<Object>() {
            public Object run() {
                try {
                    org.jruby.ext.posix.POSIX posix = POSIXSupport.getPOSIX();
                    // call some method to make sure native library gets loaded
                    posix.getuid();
                    return posix;
                } catch (Throwable t) {
                    throw new RuntimeException(t);
                }
            }
        });
    }
}
