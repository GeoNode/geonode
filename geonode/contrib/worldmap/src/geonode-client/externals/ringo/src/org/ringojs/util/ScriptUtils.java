/*
 *  Copyright 2006 Hannes Wallnoefer <hannes@helma.at>
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package org.ringojs.util;

import org.mozilla.javascript.*;
import org.ringojs.wrappers.ScriptableMap;
import org.ringojs.wrappers.ScriptableList;

import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * A collection of Rhino utility methods.
 */
public class ScriptUtils {

    /**
     * Coerce/wrap a java object to a JS object, and mask Lists and Maps
     * as native JS objects.
     * @param obj the object to coerce/wrap
     * @param scope the scope
     * @return the wrapped/masked java object
     */
    @SuppressWarnings("unchecked")
    public static Object javaToJS(Object obj, Scriptable scope) {
        if (obj instanceof Scriptable) {
            if (obj instanceof ScriptableObject
                    && ((Scriptable) obj).getParentScope() == null
                    && ((Scriptable) obj).getPrototype() == null) {
                ScriptRuntime.setObjectProtoAndParent((ScriptableObject) obj, scope);
            }
            return obj;
        } else if (obj instanceof List) {
            return new ScriptableList(scope, (List) obj);
        } else if (obj instanceof Map) {
            return new ScriptableMap(scope, (Map) obj);
        } else {
            return Context.javaToJS(obj, scope);
        }
    }

    /**
     * Unwrap a JS object to a java object. This is much more conservative than
     * Context.jsToJava in that it will preserve undefined values.
     * @param obj a JavaScript value
     * @return a Java object corresponding to obj
     */
    public static Object jsToJava(Object obj) {
        while (obj instanceof Wrapper) {
            obj = ((Wrapper) obj).unwrap();
        }
        return obj;
    }

    /**
     * Return a class prototype, or the object prototype if the class
     * is not defined.
     * @param scope the scope
     * @param className the class name
     * @return the class or object prototype
     */
    public static Scriptable getClassOrObjectProto(Scriptable scope, String className) {
        Scriptable proto = ScriptableObject.getClassPrototype(scope, className);
        if (proto == null) {
            proto = ScriptableObject.getObjectPrototype(scope);
        }
        return proto;
    }

    /**
     * Make sure that number of arguments is valid.
     * @param args the argument array
     * @param min the minimum number of arguments
     * @param max the maximum number of arguments
     * @throws IllegalArgumentException if the number of arguments is not valid
     */
    public static void checkArguments(Object[] args, int min, int max) {
        if (min > -1 && args.length < min)
            throw new IllegalArgumentException();
        if (max > -1 && args.length > max)
            throw new IllegalArgumentException();
    }

    /**
     * Get an argument as ScriptableObject
     * @param args the argument array
     * @param pos the position of the requested argument
     * @return the argument as ScriptableObject
     * @throws IllegalArgumentException if the argument can't be converted to a map
     */
    public static ScriptableObject getScriptableArgument(Object[] args, int pos, boolean allowNull)
            throws IllegalArgumentException {
        if (pos >= args.length || args[pos] == null || args[pos] == Undefined.instance) {
            if (allowNull) return null;
            throw ScriptRuntime.constructError("Error", "Argument " + (pos + 1) + " must not be null");
        } if (args[pos] instanceof ScriptableObject) {
            return (ScriptableObject) args[pos];
        }
        throw ScriptRuntime.constructError("Error", "Can't convert to ScriptableObject: " + args[pos]);
    }

    /**
     * Get an argument as string
     * @param args the argument array
     * @param pos the position of the requested argument
     * @return the argument as string
     */
    public static String getStringArgument(Object[] args, int pos, boolean allowNull) {
        if (pos >= args.length || args[pos] == null || args[pos] == Undefined.instance) {
            if (allowNull) return null;
            throw ScriptRuntime.constructError("Error", "Argument " + (pos + 1) + " must not be null");
        }
        return ScriptRuntime.toString(args[pos].toString());
    }

    /**
     * Get an argument as Map
     * @param args the argument array
     * @param pos the position of the requested argument
     * @return the argument as map
     * @throws IllegalArgumentException if the argument can't be converted to a map
     */
    public static Map getMapArgument(Object[] args, int pos, boolean allowNull)
            throws IllegalArgumentException {
        if (pos >= args.length || args[pos] == null || args[pos] == Undefined.instance) {
            if (allowNull) return null;
            throw ScriptRuntime.constructError("Error", "Argument " + (pos + 1) + " must not be null");
        } if (args[pos] instanceof Map) {
            return (Map) args[pos];
        }
        throw ScriptRuntime.constructError("Error", "Can't convert to java.util.Map: " + args[pos]);
    }

    /**
     * Get an argument as object
     * @param args the argument array
     * @param pos the position of the requested argument
     * @return the argument as object
     */
    public static Object getObjectArgument(Object[] args, int pos, boolean allowNull) {
        if (pos >= args.length || args[pos] == null || args[pos] == Undefined.instance) {
            if (allowNull) return null;
            throw ScriptRuntime.constructError("Error", "Argument " + (pos + 1) + " must not be null");
        }
        return args[pos];
    }

    /**
     * Try to convert an object to an int value, returning the default value if conversion fails.
     * @param obj the value
     * @param defaultValue the default value
     * @return the converted value
     */
    public static int toInt(Object obj, int defaultValue) {
        double d = ScriptRuntime.toNumber(obj);
        if (d == ScriptRuntime.NaN || (int)d != d) {
            return defaultValue;
        }
        return (int) d;
    }


    /**
     * Get a snapshot of the current JavaScript evaluation state by creating
     * an Error object and invoke the function on it passing along any arguments.
     * Used to invoke console.trace() and friends because implementing this
     * in JavaScript would mess with the evaluation state.
     * @param function the function to call
     * @param args optional arguments to pass to the function.
     */
    public static void traceHelper(Function function, Object... args) {
        Context cx = Context.getCurrentContext();
        Scriptable scope = ScriptableObject.getTopLevelScope(function);
        EcmaError error = ScriptRuntime.constructError("Trace", "");
        WrapFactory wrapFactory = cx.getWrapFactory();
        Scriptable thisObj = wrapFactory.wrapAsJavaObject(cx, scope, error, null);
        for (int i = 0; i < args.length; i++) {
            args[i] = wrapFactory.wrap(cx, scope, args[i], null);
        }
        function.call(cx, scope, thisObj, args);
    }

    /**
     * Helper for console.assert(). Implemented in Java in order not to
     * modify the JavaScript stack.
     * @param condition the condition to test
     * @param args one or more message parts
     */
    public static void assertHelper(Object condition, Object... args) {
        if (ScriptRuntime.toBoolean(condition)) {
            return;
        }
        // assertion failed
        String msg = "";
        if (args.length > 0) {
            msg = ScriptRuntime.toString(args[0]);
            Pattern pattern = Pattern.compile("%[sdifo]");
            for (int i = 1; i < args.length; i++) {
                Matcher matcher = pattern.matcher(msg);
                if (matcher.find()) {
                    msg = matcher.replaceFirst(ScriptRuntime.toString(args[i]));
                } else {
                    msg = msg + " " + ScriptRuntime.toString(args[i]);
                }
            }
        }
        throw ScriptRuntime.constructError("AssertionError", msg);
    }

}
