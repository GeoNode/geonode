package org.ringojs.security;

import java.security.BasicPermission;

/**
 * This class represents a Ringo-specific runtime permission. Ringo
 * must be run with {@link RingoSecurityManager} in order for
 * <code>RingoRuntimePermissions</code> to take effect.
 * <p>
 * Currently the Ringo runtime recognizes the following permissions:
 *
 * <ul>
 * <li><code>accessJava</code>: grant JavaScript code access to Java classes</li>
 * <li><code>spawnThread</code>: allow JavaScript code to spawn threads</li>
 * </ul>
 */
public class RingoRuntimePermission extends BasicPermission {

    static final long serialVersionUID = -7850438718537722485L;

    public RingoRuntimePermission(String name) {
        super(name);
    }

    public RingoRuntimePermission(String name, String actions) {
        super(name, actions);
    }

}
