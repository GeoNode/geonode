package org.ringojs.util;

import com.kenai.constantine.platform.Errno;
import org.jruby.ext.posix.POSIX;
import org.jruby.ext.posix.POSIXFactory;
import org.jruby.ext.posix.POSIXHandler;
import org.mozilla.javascript.Context;

import java.io.File;
import java.io.InputStream;
import java.io.PrintStream;
import java.util.Set;

public class POSIXSupport {

    static final POSIX POSIX = POSIXFactory.getPOSIX(new RingoPOSIXHandler(), true);

    public static POSIX getPOSIX() {
        return POSIX;
    }

    static class RingoPOSIXHandler implements POSIXHandler {

        public void error(Errno errno, String s) {
            throw Context.reportRuntimeError(errno + " - " + s);
        }

        public void unimplementedError(String s) {
            throw Context.reportRuntimeError(s);
        }

        public void warn(WARNING_ID warning_id, String s, Object... objects) {
        }

        public boolean isVerbose() {
            return "true".equals(System.getProperty("ringo.verbose"));
        }

        public File getCurrentWorkingDirectory() {
            return new File(System.getProperty("user.dir"));
        }

        public String[] getEnv() {
            Set<String> keys = System.getenv().keySet();
            return keys.toArray(new String[keys.size()]);
        }

        public InputStream getInputStream() {
            return System.in;
        }

        public PrintStream getOutputStream() {
            return System.out;
        }

        public int getPID() {
            return 0;
        }

        public PrintStream getErrorStream() {
            return System.err;
        }
    }

}

