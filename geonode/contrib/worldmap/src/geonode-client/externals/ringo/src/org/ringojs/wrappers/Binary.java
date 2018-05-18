package org.ringojs.wrappers;

import org.mozilla.javascript.*;
import org.mozilla.javascript.annotations.JSFunction;
import org.mozilla.javascript.annotations.JSGetter;
import org.mozilla.javascript.annotations.JSSetter;
import org.mozilla.javascript.annotations.JSConstructor;
import org.ringojs.util.ScriptUtils;

import java.io.UnsupportedEncodingException;
import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Map;
import java.lang.reflect.Method;

/**
 * <p>A wrapper around a Java byte array compliant to the Binary/ByteArray/ByteString
 * classes defined in the <a href="http://wiki.commonjs.org/wiki/Binary/B">Binary/B proposal</a>.
 * To register Binary, ByteArray and ByteString as a host objects in Rhino call the
 * <code>defineClass()</code> function with this class as argument.</p>
 *
 * <pre><code>defineClass(org.ringojs.wrappers.Binary);</code></pre>
 *
 * <p>The JavaScript Binary class serves as common base class for ByteArray and ByteString
 * and can't be instantiated. ByteArray implements a modifiable and resizable byte buffer,
 * while ByteString implements an immutable byte sequence. The ByteArray and ByteString
 * constructors can take several arguments. Have a look at the proposal for details.</p>
 *
 * <p>When passed to a Java method that expects a byte array, instances of thes class
 * are automatically unwrapped. Use the {@link #unwrap()} method to explicitly get the
 * wrapped Java byte array.</p>
 */
public class Binary extends ScriptableObject implements Wrapper {

    private byte[] bytes;
    private int length;
    private final Type type;

    enum Type {
        Binary, ByteArray, ByteString
    }

    public Binary() {
        type = Type.Binary;
    }

    public Binary(Type type) {
        this.type = type;
    }

    public Binary(Scriptable scope, Type type, int length) {
        super(scope, ScriptUtils.getClassOrObjectProto(scope, type.toString()));
        this.type = type;
        this.bytes = new byte[Math.max(length, 8)];
        this.length = length;
    }

    public Binary(Scriptable scope, Type type, byte[] bytes) {
        this(scope, type, bytes, 0, bytes.length);
    }

    public Binary(Scriptable scope, Type type, byte[] bytes, int offset, int length) {
        super(scope, ScriptUtils.getClassOrObjectProto(scope, type.toString()));
        this.bytes = new byte[length];
        this.length = length;
        this.type = type;
        System.arraycopy(bytes, offset, this.bytes, 0, length);
    }

    @JSConstructor
    public static Object construct(Context cx, Object[] args, Function ctorObj, boolean inNewExpr) {
        ScriptUtils.checkArguments(args, 0, 2);
        Scriptable scope = ctorObj.getParentScope();
        Type type = Type.valueOf((String) ctorObj.get("name", ctorObj));
        if (type == Type.Binary) {
            throw ScriptRuntime.constructError("Error", "cannot instantiate Binary base class");
        }
        if (args.length == 0) {
            return new Binary(scope, type, 0);
        }
        Object arg = args[0];
        if (arg instanceof Wrapper) {
            arg = ((Wrapper) arg).unwrap();
        }
        if (args.length == 2) {
            if (!(arg instanceof String)) {
                throw ScriptRuntime.constructError("Error", "Expected string as first argument");
            } else if (!(args[1] instanceof String)) {
                throw ScriptRuntime.constructError("Error", "Expected string as second argument");
            }
            try {
                return new Binary(scope, type, ((String) arg).getBytes((String) args[1]));
            } catch (UnsupportedEncodingException uee) {
                throw ScriptRuntime.constructError("Error", "Unsupported encoding: " + args[1]);
            }
        } else if (arg instanceof Number && type == Type.ByteArray) {
            return new Binary(scope, type, ((Number) arg).intValue());
        } else if (ScriptRuntime.isArrayObject(arg)) {
            Scriptable object = (Scriptable) arg;
            long longLength =  ScriptRuntime.toUint32(
                    ScriptRuntime.getObjectProp(object, "length", cx));
            if (longLength > Integer.MAX_VALUE) {
                throw new IllegalArgumentException();
            }
            int length = (int) longLength;
            Binary bytes = new Binary(scope, type, length);
            for (int i = 0; i < length; i++) {
                Object value = ScriptableObject.getProperty(object, i);
                bytes.putInternal(i, value);
            }
            return bytes;
        } else if (arg instanceof byte[]) {
            return new Binary(scope, type, (byte[]) arg);
        } else if (arg instanceof Binary) {
            return new Binary(scope, type, ((Binary) arg).getBytes());
        } else if (arg == Undefined.instance) {
            return new Binary(scope, type, 0);
        } else {
            throw ScriptRuntime.constructError("Error", "Unsupported argument: " + arg);
        }
    }

    // Called after the host class has been defined.
    public static void finishInit(Scriptable scope, FunctionObject ctor, Scriptable prototype)
            throws NoSuchMethodException{
        initClass(scope, prototype, Type.ByteArray);
        initClass(scope, prototype, Type.ByteString);
    }

    private static void initClass(Scriptable scope, Scriptable parentProto, Type type)
            throws NoSuchMethodException {
        Binary prototype = new Binary(type);
        prototype.setPrototype(parentProto);
        Method ctorMember = Binary.class.getMethod("construct", new Class[] {
                Context.class, Object[].class, Function.class, Boolean.TYPE
        });
        FunctionObject constructor = new FunctionObject(type.toString(), ctorMember, scope);
        constructor.addAsConstructor(scope, prototype);
        constructor.defineProperty("wrap", new Wrap(scope, prototype, type),
                DONTENUM | READONLY | PERMANENT);
    }

    public Type getType() {
        return type;
    }

    @Override
    public Object get(int index, Scriptable start) {
        if (index < 0 || index >= length) {
            return Undefined.instance;
        }
        return Integer.valueOf(0xff & bytes[index]);
    }

    @Override
    public boolean has(int index, Scriptable start) {
        return index >= 0 && index < length;
    }

    @Override
    public void put(int index, Scriptable start, Object value) {
        if (type != Type.ByteArray) {
            return;
        }
        putInternal(index, value);
    }

    private void putInternal(int index, Object value) {
        if (index < 0) {
            throw ScriptRuntime.constructError("Error", "Negative ByteArray index");
        }
        if (!(value instanceof Number)) {
            throw ScriptRuntime.constructError("Error", "Non-numeric ByteArray member: " + value);
        }
        if (index >= length) {
            setLength(index + 1);
        }
        int n = ((Number) value).intValue();
        bytes[index] = (byte) (0xff & n);
    }

    @JSGetter
    public int getLength() {
        return length;
    }

    @JSSetter
    public synchronized void setLength(Object length) {
        int l = ScriptUtils.toInt(length, -1);
        if (l < 0) {
            throw ScriptRuntime.constructError("Error", "Inappropriate ByteArray length");
        }
        setLength(l);
    }

    protected synchronized void setLength(int newLength) {
        if (type != Type.ByteArray) {
            return;
        }
        if (newLength < length) {
            // if shrinking clear the old buffer
            Arrays.fill(bytes, newLength, length, (byte) 0);
        } else if (newLength > bytes.length) {
            // if growing make sure the buffer is large enough
            int newSize = Math.max(newLength, bytes.length * 2);
            byte[] b = new byte[newSize];
            System.arraycopy(bytes, 0, b, 0, length);
            bytes = b;
        }
        length = newLength;
    }

    @JSFunction
    public Object get(Object index) {
        int i = ScriptUtils.toInt(index, -1);
        if (i < 0 || i >= length) {
            return Undefined.instance;
        }
        return Integer.valueOf(0xff & bytes[i]);
    }

    @JSFunction
    public Object charCodeAt(Object index) {
        return get(index);
    }

    @JSFunction
    public Object byteAt(Object index) {
        int i = ScriptUtils.toInt(index, -1);
        if (i < 0 || i >= length) {
            return new Binary(getParentScope(), type, 0);
        }
        return new Binary(getParentScope(), type, new byte[] {bytes[i]});
    }

    @JSFunction
    public Object charAt(Object index) {
        return byteAt(index);
    }

    @JSFunction
    public void set(Object index, int value) {
        if (type != Type.ByteArray) {
            return;
        }
        int i = ScriptUtils.toInt(index, -1);
        if (i > -1) {
            if (i >= length) {
                setLength(i + 1);
            }
            bytes[i] = (byte) (0xff & value);
        }
    }

    @JSFunction
    public Object toByteArray(Object sourceCharset, Object targetCharset)
            throws UnsupportedEncodingException {
        return makeCopy(Type.ByteArray, sourceCharset, targetCharset);
    }

    @JSFunction
    public Object toByteString(Object sourceCharset, Object targetCharset)
            throws UnsupportedEncodingException {
        // no need to make a copy of an unmodifiable ByteString
        if (type == Type.ByteString &&
                sourceCharset == Undefined.instance &&
                targetCharset == Undefined.instance) {
            return this;
        }
        return makeCopy(Type.ByteString, sourceCharset, targetCharset);
    }

    private synchronized Binary makeCopy(Type targetType, Object sourceCharset,
                                         Object targetCharset)
            throws UnsupportedEncodingException {
        String source = toCharset(sourceCharset);
        String target = toCharset(targetCharset);
        if (source != null && target != null) {
            String str = new String(bytes, 0, length, source);
            return new Binary(getParentScope(), targetType, str.getBytes(target));
        }
        if (this.type == Type.ByteString && this.type == targetType) {
            return this;
        }
        return new Binary(getParentScope(), targetType, bytes, 0, length);
    }

    @JSFunction
    public void copy(int srcStartIndex, int srcEndIndex, Binary target, Object targetIndex) {
        if (target.type != Type.ByteArray) {
            throw ScriptRuntime.constructError("Error", "Target object is not writable");
        } else if (srcStartIndex < 0 || srcStartIndex >= length) {
            throw ScriptRuntime.constructError("Error", "Invalid start index: " + srcStartIndex);
        } else if (srcEndIndex < srcStartIndex || srcEndIndex > length) {
            throw ScriptRuntime.constructError("Error", "Invalid end index: " + srcEndIndex);
        }
        int targetIdx = ScriptUtils.toInt(targetIndex, 0);
        if (targetIdx < 0) {
            throw ScriptRuntime.constructError("Error", "Invalid target index: " + targetIndex);
        }
        int size = srcEndIndex - srcStartIndex;
        target.copyFrom(bytes, srcStartIndex, size, targetIdx);

    }

    private synchronized void copyFrom(byte[] source, int srcIndex, int length, int targetIndex) {
        ensureLength(targetIndex + length);
        System.arraycopy(source, srcIndex, bytes, targetIndex,  length);
    }

    @JSFunction
    public synchronized Object toArray(Object charset)
            throws UnsupportedEncodingException {
        Object[] elements;
        String cs = toCharset(charset);
        if (cs != null) {
            String str = new String(bytes, 0, length, cs);
            elements = new Object[str.length()];
            for (int i = 0; i < elements.length; i++) {
                elements[i] = Integer.valueOf(str.charAt(i));
            }
        } else {
            elements = new Object[length];
            for (int i = 0; i < length; i++) {
                elements[i] = Integer.valueOf(0xff & bytes[i]);
            }
        }
        return Context.getCurrentContext().newArray(getParentScope(), elements);
    }

    @Override
    @JSFunction
    public String toString() {
        if (bytes != null) {
            return "[" + type.toString() + " " + length + "]";
        }
        return "[object " + type.toString() + "]";
    }

    /* @JSFunction
    public String toString(Object encoding) {
        return encoding == Undefined.instance ?
            toString() : decodeToString(encoding);
    } */

    @JSFunction
    public Object slice(Object begin, Object end) {
        if (begin == Undefined.instance && end == Undefined.instance) {
            return new Binary(getParentScope(), type, bytes, 0, length);
        }
        int from = ScriptUtils.toInt(begin, 0);
        if (from < 0) {
            from += length;
        }
        from = Math.min(length, Math.max(0, from));
        int to = end == Undefined.instance ? length : ScriptUtils.toInt(end, from);
        if (to < 0) {
            to += length;
        }
        int len = Math.max(0, Math.min(length - from,  to - from));
        return new Binary(getParentScope(), type, bytes, from, len);
    }

    @JSFunction
    public static Object concat(Context cx, Scriptable thisObj,
                                      Object[] args, Function func) {
        int arglength = 0;
        List<byte[]> arglist = new ArrayList<byte[]>(args.length);
        for (Object arg : args) {
            if (arg instanceof Binary) {
                byte[] bytes = ((Binary) arg).getBytes();
                arglength += bytes.length;
                arglist.add(bytes);
            } else if (ScriptRuntime.isArrayObject(arg)) {
                Scriptable object = (Scriptable) arg;
                long longLength =  ScriptRuntime.toUint32(
                        ScriptRuntime.getObjectProp(object, "length", cx));
                if (longLength > Integer.MAX_VALUE) {
                    throw new IllegalArgumentException();
                }
                int length = (int) longLength;
                byte[] bytes = new byte[length];
                for (int i = 0; i < length; i++) {
                    Object value = ScriptableObject.getProperty(object, i);
                    if (!(value instanceof Number)) {
                        throw ScriptRuntime.constructError("Error", "Non-numeric ByteArray member: " + value);
                    }
                    int n = ((Number) value).intValue();
                    bytes[i] = (byte) (0xff & n);
                }
                arglength += bytes.length;
                arglist.add(bytes);
            } else {
                throw ScriptRuntime.constructError("Error", "Unsupported argument: " + arg);
            }
        }
        Binary thisByteArray = (Binary) thisObj;
        synchronized (thisByteArray) {
            byte[] newBytes = new byte[thisByteArray.length + arglength];
            System.arraycopy(thisByteArray.bytes, 0, newBytes, 0, thisByteArray.length);
            int index = thisByteArray.length;
            for (byte[] b : arglist) {
                System.arraycopy(b, 0, newBytes, index, b.length);
                index += b.length;
            }
            return new Binary(thisObj.getParentScope(), thisByteArray.type, newBytes);
        }
    }

    @JSFunction
    public String decodeToString(Object charset) {
        String cs = toCharset(charset);
        try {
            return cs == null ?
                    new String(bytes, 0, length) :
                    new String(bytes, 0, length, cs);
        } catch (UnsupportedEncodingException uee) {
            throw ScriptRuntime.constructError("Error", "Unsupported encoding: " + charset);
        }
    }

    @JSFunction
    public int indexOf(Object arg, Object from, Object to) {
        byte[] b = getBytesArgument(arg);
        int start = Math.max(0, Math.min(length - 1, ScriptUtils.toInt(from, 0)));
        int end = Math.max(0, Math.min(length - b.length + 1, ScriptUtils.toInt(to, length)));
        outer:
        for (int i = start; i < end; i++) {
            for (int j = 0; j < b.length; j++) {
                if (bytes[i + j] != b[j]) {
                    continue outer;
                }
            }
            return i;
        }
        return -1;
    }

    @JSFunction
    public int lastIndexOf(Object arg, Object from, Object to) {
        byte[] b = getBytesArgument(arg);
        int start = Math.max(0, Math.min(length - 1, ScriptUtils.toInt(from, 0)));
        int end = Math.max(0, Math.min(length - b.length + 1, ScriptUtils.toInt(to, length)));
        outer:
        for (int i = end - 1; i >= start; i--) {
            for (int j = 0; j < b.length; j++) {
                if (bytes[i + j] != b[j]) {
                    continue outer;
                }
            }
            return i;
        }
        return -1;
    }

    @JSFunction
    public synchronized Object split(Object delim, Object options) {
        byte[][] delimiters = getSplitDelimiters(delim);
        boolean includeDelimiter = false;
        int count = Integer.MAX_VALUE;
        if (options instanceof Scriptable) {
            Scriptable o = (Scriptable) options;
            Object include = ScriptableObject.getProperty(o, "includeDelimiter");
            includeDelimiter = include != NOT_FOUND && ScriptRuntime.toBoolean(include);
            Object max = ScriptableObject.getProperty(o, "count");
            if (max != NOT_FOUND) count = ScriptRuntime.toInt32(max);
        }
        List<Binary> list = new ArrayList<Binary>();
        Scriptable scope = getParentScope();
        int index = 0;
        int found = 0;
        outer:
        for (int i = 0; i < length && found < count - 1; i++) {
            inner:
            for (byte[] delimiter : delimiters) {
                if (i + delimiter.length > length) {
                    continue;
                }
                for (int j = 0; j < delimiter.length; j++) {
                    if (bytes[i + j] != delimiter[j]) {
                        continue inner;
                    }
                }
                list.add(new Binary(scope, type, bytes, index, i - index));
                if (includeDelimiter) {
                    list.add(new Binary(scope, type, delimiter));
                }
                index = i + delimiter.length;
                i = index - 1;
                found++;
                continue outer;
            }
        }
        if (index == 0) {
            list.add(this);
        } else {
            list.add(new Binary(scope, type, bytes, index, length - index));
        }
        return Context.getCurrentContext().newArray(scope, list.toArray());
    }

    protected static Binary wrap(Type type, byte[] bytes, Scriptable scope,
                                 Scriptable prototype) {
        Binary wrapper = new Binary(type);
        wrapper.bytes = bytes;
        wrapper.length = bytes.length;
        wrapper.setParentScope(scope);
        wrapper.setPrototype(prototype);
        return wrapper;
    }

    /**
     * Static method that wraps a java byte array without copying.
     */
    static class Wrap extends BaseFunction {
        Type type;
        Scriptable prototype;

        Wrap(Scriptable scope, Scriptable prototype, Type type) {
            super(scope, ScriptableObject.getFunctionPrototype(scope));
            this.type = type;
            this.prototype = prototype;
        }

        @Override
        public Object call(Context cx, Scriptable scope, Scriptable thisObj, Object[] args) {
            Object arg = ScriptUtils.getObjectArgument(args, 0, false);
            if (arg instanceof Wrapper) {
                arg = ((Wrapper) arg).unwrap();
            }
            if (!(arg instanceof byte[])) {
                throw ScriptRuntime.constructError("Error", "wrap() requires an argument of type byte[]");
            }
            byte[] bytes = (byte[]) arg;
            return wrap(type, bytes, getTopLevelScope(scope), prototype);
        }
    }

    @JSFunction("unwrap")
    public Object jsunwrap() {
        return NativeJavaArray.wrap(getParentScope(), getBytes());
    }

    /**
     * Unwrap the object by returning the wrapped value.
     *
     * @return a wrapped value
     */
    public Object unwrap() {
        return getBytes();
    }

    public byte[] getBytes() {
        normalize();
        return bytes;
    }

    public String getClassName() {
        return type.toString();
    }

    protected synchronized void ensureLength(int minLength) {
        if (minLength > length) {
            setLength(minLength);
        }
    }

    private synchronized void normalize() {
        if (length != bytes.length) {
            byte[] b = new byte[length];
            System.arraycopy(bytes, 0, b, 0, length);
            bytes = b;
        }
    }

    private byte[] getBytesArgument(Object arg) {
        if (arg instanceof Number) {
            return new byte[] {(byte) (0xff & ((Number) arg).intValue())};
        } else if (arg instanceof Binary) {
            return ((Binary) arg).getBytes();
        } else {
            throw new RuntimeException("unsupported delimiter: " + arg);
        }
    }

    private byte[][] getSplitDelimiters(Object delim) {
        List<byte[]> list = new ArrayList<byte[]>();
        Collection values = null;
        if (delim instanceof Collection) {
            values = (Collection) delim;
        } else if (delim instanceof Map && delim instanceof NativeArray) {
            // NativeArray used to implement java.util.Map
            values = ((Map) delim).values();
        }
        if (values != null) {
            for (Object value : values) {
                list.add(getBytesArgument(value));
            }
        } else {
            list.add(getBytesArgument(delim));
        }
        return list.toArray(new byte[list.size()][]);
    }

    private String toCharset(Object charset) {
        if (charset == Undefined.instance || charset == null) {
            return null;
        }
        if (!(charset instanceof String)) {
            throw ScriptRuntime.constructError("Error",
                    "Charset is not a string: " + charset);
        }
        return (String) charset;
    }
}
