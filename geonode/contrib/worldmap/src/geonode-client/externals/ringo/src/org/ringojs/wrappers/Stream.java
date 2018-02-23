package org.ringojs.wrappers;

import org.mozilla.javascript.*;
import org.mozilla.javascript.annotations.JSFunction;
import org.mozilla.javascript.annotations.JSConstructor;
import org.mozilla.javascript.annotations.JSGetter;
import org.ringojs.util.ScriptUtils;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;

/**
 * <p>A CommonJS-compliant wrapper around a Java input or output stream. To
 * register Stream as a host object in Rhino call the <code>defineClass()</code> function
 * with this class.</p>
 *
 * <pre><code>defineClass(org.ringojs.wrappers.Stream);</code></pre>
 *
 * <p>To create an Stream wrapper around an instance of <code>java.io.InputStream</code>
 * or <code>java.io.OutputStream</code> call the constructor with the stream as argument:</p>
 *
 * <pre><code>var io = new Stream(javaInputStream);</code></pre>
 *
 * <p>When passed to a Java method that expects an input or output stream, Stream wrappers
 * are automatically unwrapped. use the {@link #unwrap()} method to explicitly get the
 * wrapped stream.</p>
 */
public class Stream extends ScriptableObject implements Wrapper {

    private InputStream input;
    private OutputStream output;
    private boolean closed = false;

    private final static String CLASSNAME = "Stream";

    public Stream() {
        input = null;
        output = null;
    }

    public Stream(Scriptable scope, Object arg1, Object arg2) {
        super(scope, ScriptUtils.getClassOrObjectProto(scope, CLASSNAME));
        init(arg1, arg2);
    }

    @JSConstructor
    public void init(Object arg1, Object arg2) {
        setStream(arg1);
        setStream(arg2);
    }

    private void setStream(Object arg) {
        if (arg instanceof Wrapper) {
            arg = ((Wrapper) arg).unwrap();
        }
        if (arg instanceof InputStream) {
            input = (InputStream) arg;
        } else if (arg instanceof OutputStream) {
            output = (OutputStream) arg;
        } else if (arg != Undefined.instance && arg != null) {
            throw ScriptRuntime.constructError("Error", "Unsupported argument: " + arg);
        }
    }

    @JSFunction
    public boolean readable() {
        return input != null;
    }

    @JSFunction
    public boolean writable() {
        return output != null;
    }

    @JSFunction
    public boolean seekable() {
        return false;
    }

    @JSFunction
    public Object read(Object limit) {
        if (input == null) {
            throw ScriptRuntime.constructError("Error", "no input stream");
        }
        int max = limit == Undefined.instance ? -1 : ScriptRuntime.toInt32(limit);
        Scriptable scope = ScriptableObject.getTopLevelScope(this);
        if (max > -1) {
            try {
                byte[] bytes = new byte[max];
                int read = input.read(bytes);
                return read > -1 ?
                        new Binary(scope, Binary.Type.ByteString, bytes, 0, read) :
                        new Binary(scope, Binary.Type.ByteString, 0);
            } catch (IOException iox) {
                throw new WrappedException(iox);
            }
        } else {
            byte[] buffer = new byte[8192];
            int read, count = 0;
            try {
                while ((read = input.read(buffer, count, buffer.length - count)) > -1) {
                    count += read;
                    if (count == buffer.length) {
                        byte[] b = new byte[buffer.length * 2];
                        System.arraycopy(buffer, 0, b, 0, count);
                        buffer = b;
                    }
                }
                return count > -1 ?
                        new Binary(scope, Binary.Type.ByteString, buffer, 0, count) :
                        new Binary(scope, Binary.Type.ByteString, 0);
            } catch (IOException iox) {
                throw ScriptRuntime.constructError("Error", "Error reading from input stream: " + iox);
            }
        }
    }

    @JSFunction
    public int readInto(Binary bytes, Object start, Object end) {
        if (input == null) {
            throw ScriptRuntime.constructError("Error", "no input stream");
        } else if (bytes == Undefined.instance || bytes == null) {
            throw ScriptRuntime.constructError("Error", "readInto called without Binary argument");
        } else if (bytes.getType() != Binary.Type.ByteArray) {
            throw ScriptRuntime.constructError("Error", "argument to readInto must be ByteArray");
        }
        int from = ScriptUtils.toInt(start, 0);
        int to = ScriptUtils.toInt(end, bytes.getLength());
        try {
            byte[] b = bytes.getBytes();
            return input.read(b, from, to - from);
        } catch (IOException iox) {
            throw new WrappedException(iox);
        }
    }

    @JSFunction
    public void write(Object arg, Object start, Object end) {
        if (arg instanceof Wrapper) {
            arg = ((Wrapper) arg).unwrap();
        }
        byte[] bytes;
        if (arg instanceof Binary) {
            bytes = ((Binary) arg).getBytes();
        } else if (arg instanceof byte[]) {
            bytes = (byte[]) arg;
        } else if (arg instanceof String) {
            // TODO this is for narwhal compatibility only
            System.err.println("Warning: binary write called with string argument. Using default encoding.");
            bytes = ((String) arg).getBytes();
        } else {
            throw Context.reportRuntimeError("write called with illegal argument: " + arg);
        }
        if (output == null) {
            throw ScriptRuntime.constructError("Error", "no output stream");
        }
        int from = start == Undefined.instance ? 0 : ScriptRuntime.toInt32(start);
        int to = end == Undefined.instance ? bytes.length : ScriptRuntime.toInt32(end);
        try {
            output.write(bytes, from, to - from);
        } catch (IOException iox) {
            throw Context.throwAsScriptRuntimeEx(iox);
        }
    }

    @JSFunction
    public void flush() {
        if (output == null) {
            throw ScriptRuntime.constructError("Error", "no output stream");
        }
        try {
            output.flush();
        } catch (IOException iox) {
            throw new WrappedException(iox);
        }
    }

    @JSFunction
    public int skip(int num) {
        try {
            if (input != null) {
                return (int) input.skip(num);
            } else {
                throw Context.reportRuntimeError(
                        "skip() invoked on non-readable Stream");
            }
        } catch (IOException iox) {
            throw new WrappedException(iox);
        }
    }

    @JSFunction
    public void close() {
        try {
            if (output != null) {
                output.close();
            }
            if (input != null) {
                input.close();
            }
            closed = true;
        } catch (IOException iox) {
            throw new WrappedException(iox);
        }
    }

    @JSFunction
    public boolean closed() {
        return closed;
    }

    @JSFunction("unwrap")
    public Object jsunwrap() {
        return new NativeJavaObject(getParentScope(), unwrap(), null);
    }

    @JSGetter
    public Object getInputStream() {
        return input == null ? null : new NativeJavaObject(getParentScope(), input, null);
    }

    @JSGetter
    public Object getOutputStream() {
        return output == null ? null : new NativeJavaObject(getParentScope(), output, null);
    }

    /**
     * Unwrap the object by returning the wrapped value.
     * @return a wrapped value
     */
    public Object unwrap() {
        return input != null ? input : output;
    }

    /**
     * Return the name of the class.
     * @return the class name
     */
    public String getClassName() {
        return CLASSNAME;
    }
}
