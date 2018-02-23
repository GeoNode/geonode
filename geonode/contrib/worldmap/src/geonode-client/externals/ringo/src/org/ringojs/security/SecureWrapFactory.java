package org.ringojs.security;

import org.mozilla.javascript.Context;
import org.mozilla.javascript.NativeJavaClass;
import org.mozilla.javascript.NativeJavaObject;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.WrappedException;
import org.ringojs.engine.RingoWrapFactory;

public class SecureWrapFactory extends RingoWrapFactory {

    final static RingoSecurityManager secman;

    static {
        SecurityManager sm = System.getSecurityManager();
        secman = (sm instanceof RingoSecurityManager) ?
                (RingoSecurityManager) sm : null;
    }

    private static void checkAccess(Class clazz) {
        if (secman != null) {
            try {
                secman.checkJavaAccess();
            } catch (Exception x) {
                throw new WrappedException(x);
            }
        }
    }

    /**
     * Wrap Java object as Scriptable instance to allow full access to its
     * methods and fields from JavaScript. This implementation uses a custom wrappers
     * that checks the SecurityManager for permission each time a Java member is
     * accessed.
     *
     * @param cx         the current Context for this thread
     * @param scope      the scope of the executing script
     * @param javaObject the object to be wrapped
     * @param staticType type hint. If security restrictions prevent to wrap
     *                   object based on its class, staticType will be used instead.
     * @return the wrapped value which shall not be null
     */
    @Override
    public Scriptable wrapAsJavaObject(Context cx, Scriptable scope, Object javaObject, Class<?> staticType) {
        return new SecureObjectWrapper(scope, javaObject, staticType);
    }

    /**
     * Wrap a Java class as Scriptable instance to allow access to its static
     * members and fields and use as constructor from JavaScript.
     * <p>
     * Subclasses can override this method to provide custom wrappers for
     * Java classes.
     *
     * @param cx the current Context for this thread
     * @param scope the scope of the executing script
     * @param javaClass the class to be wrapped
     * @return the wrapped value which shall not be null
     */
    @Override
    public Scriptable wrapJavaClass(Context cx, Scriptable scope, Class javaClass) {
        return new SecureClassWrapper(scope, javaClass);
    }

    public static class SecureObjectWrapper extends NativeJavaObject {

        Class clazz;

        public SecureObjectWrapper(Scriptable scope, Object javaObject, Class staticType) {
            super(scope, javaObject, staticType);
            clazz = javaObject.getClass();
        }

        @Override
        public void put(String name, Scriptable start, Object value) {
            checkAccess(clazz);
            super.put(name, start, value);
        }

        @Override
        public Object get(String name, Scriptable start) {
            checkAccess(clazz);
            return super.get(name, start);
        }

        @Override
        public void delete(String name) {
            checkAccess(clazz);
            super.delete(name);
        }
    }

    public static class SecureClassWrapper extends NativeJavaClass {

        Class clazz;

        public SecureClassWrapper(Scriptable scope, Class<?> clazz) {
            super(scope, clazz);
            this.clazz = clazz;
        }

        @Override
        public Scriptable construct(Context cx, Scriptable scope, Object[] args) {
            checkAccess(clazz);
            return super.construct(cx, scope, args);
        }

        @Override
        public Object get(String name, Scriptable start) {
            checkAccess(clazz);
            return super.get(name, start);
        }

        @Override
        public Class<?> getClassObject() {
            checkAccess(clazz);
            return super.getClassObject();
        }

        @Override
        public void put(String name, Scriptable start, Object value) {
            checkAccess(clazz);
            super.put(name, start, value);
        }

        @Override
        public void delete(String name) {
            checkAccess(clazz);
            super.delete(name);
        }
    }
}

