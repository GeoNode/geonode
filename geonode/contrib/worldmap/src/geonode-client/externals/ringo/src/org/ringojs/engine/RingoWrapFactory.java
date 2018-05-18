package org.ringojs.engine;

import org.mozilla.javascript.Context;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.WrapFactory;
import org.ringojs.util.CaseInsensitiveMap;
import org.ringojs.wrappers.ScriptableMap;

/**
 * Ringo default wrap factory implementation.
 */
public class RingoWrapFactory extends WrapFactory {

        public RingoWrapFactory() {
            // disable java primitive wrapping, it's just annoying.
            setJavaPrimitiveWrap(false);
        }

        /**
         * Override to wrap maps as scriptables.
         *
         * @param cx         the current Context for this thread
         * @param scope      the scope of the executing script
         * @param obj        the object to be wrapped. Note it can be null.
         * @param staticType type hint. If security restrictions prevent to wrap
         *                   object based on its class, staticType will be used instead.
         * @return the wrapped value.
         */
        @Override
        public Object wrap(Context cx, Scriptable scope, Object obj, Class staticType) {
            if (obj instanceof CaseInsensitiveMap) {
                return new ScriptableMap(scope, (CaseInsensitiveMap) obj);
            }
            return super.wrap(cx, scope, obj, staticType);
        }

    }