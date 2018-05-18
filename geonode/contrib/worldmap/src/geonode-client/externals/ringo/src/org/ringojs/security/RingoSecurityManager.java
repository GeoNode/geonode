package org.ringojs.security;

import org.mozilla.javascript.RhinoSecurityManager;

import java.security.*;

public class RingoSecurityManager extends RhinoSecurityManager {

    public static final Permission
            GET_CLASSLOADER = new RuntimePermission("getClassLoader");
    public static final Permission
            ACCESS_DECLARED_MEMBERS = new RuntimePermission("accessDeclaredMembers");
    public static final Permission
            ACCESS_JAVA = new RingoRuntimePermission("accessJava");
    public static final Permission
            SPAWN_THREAD = new RingoRuntimePermission("spawnThread");

    /**
     * The default security manager does not provide a way to keep code from starting
     * threads. We overide this method to be able to do so by checking the
     * modifyThreadGroup permission on all thread groups, not just the root group.
     * @param g the threadgroup
     */
    @Override
    public void checkAccess(ThreadGroup g) {
        checkPermission(SPAWN_THREAD);
        super.checkAccess(g);
    }

    /**
     * Override to decide on top-most application script class instead of java class.
     * This is currently not as useful as it should be because of Rhino's caching of
     * reflection meta-data. Because of this, classes that have already been used
     * by trusted code are accessible to untrusted code as well.
     * @param clazz the class that reflection is to be performed on.
     * @param which type of access, PUBLIC or DECLARED.
     * @exception  SecurityException if the caller does not have
     *             permission to access members.
     * @exception  NullPointerException if the <code>clazz</code> argument is
     *             <code>null</code>.
     */
    @Override
    public void checkMemberAccess(final Class<?> clazz, int which) {
        if (clazz == null) {
            throw new NullPointerException("class can't be null");
        }
        if (clazz.getClassLoader() == null) {
            return;
        }
        final Class c = getCurrentScriptClass();
        if (c != null && clazz.getClassLoader() == c.getClassLoader()) {
            return;
        }
        Boolean allowed = AccessController.doPrivileged(new PrivilegedAction<Boolean>() {
            public Boolean run() {
                ProtectionDomain pd = c == null ? null : c.getProtectionDomain();
                return pd != null
                        && Policy.getPolicy().implies(pd, ACCESS_DECLARED_MEMBERS) ?
                    Boolean.TRUE : Boolean.FALSE;
            }
        });
        if (allowed.booleanValue()) {
            return;
        }
        checkPermission(ACCESS_DECLARED_MEMBERS);
    }

    /**
     * Check if the  top-most application script has permission to access
     * members of Java objects and classes.
     * <p>
     * This checks if the script trying to access a java class or object has the
     * <code>accessEngine</code> RingoRuntimePermission.
     *
     * @exception  SecurityException if the caller does not have
     *             permission to access java classes.
     */
    public void checkJavaAccess() {

        final Class c = getCurrentScriptClass();
        if (c == null) {
            return;
        }

        Boolean allowed = AccessController.doPrivileged(new PrivilegedAction<Boolean>() {
            public Boolean run() {
                ProtectionDomain pd = c.getProtectionDomain();
                return pd == null || Policy.getPolicy().implies(pd, ACCESS_JAVA) ?
                        Boolean.TRUE : Boolean.FALSE;
            }
        });

        if (!allowed.booleanValue()) {
            throw new AccessControlException("Java access denied", ACCESS_JAVA);
        }
    }

}
