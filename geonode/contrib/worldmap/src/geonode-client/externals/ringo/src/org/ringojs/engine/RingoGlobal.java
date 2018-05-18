/*
 *  Copyright 2009 the Helma Project
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

package org.ringojs.engine;

import org.mozilla.javascript.Context;
import org.mozilla.javascript.ContextAction;
import org.mozilla.javascript.ContextFactory;
import org.mozilla.javascript.Function;
import org.mozilla.javascript.NativeJavaClass;
import org.mozilla.javascript.NativeJavaObject;
import org.mozilla.javascript.RhinoException;
import org.mozilla.javascript.ScriptRuntime;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.ScriptableObject;
import org.mozilla.javascript.WrappedException;
import org.mozilla.javascript.Wrapper;
import org.mozilla.javascript.tools.shell.Environment;
import org.mozilla.javascript.tools.shell.QuitAction;
import org.ringojs.repository.Repository;
import org.ringojs.repository.Trackable;
import org.ringojs.security.RingoSecurityManager;
import org.ringojs.util.ScriptUtils;
import org.mozilla.javascript.tools.shell.Global;
import org.ringojs.repository.Resource;

import java.lang.reflect.InvocationTargetException;
import java.security.AccessController;
import java.security.PrivilegedAction;
import java.io.IOException;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

public class RingoGlobal extends Global {

    private final RhinoEngine engine;
    private final static SecurityManager securityManager = System.getSecurityManager();
    private static ExecutorService threadPool;
    private static AtomicInteger ids = new AtomicInteger();

    public RingoGlobal(Context cx, RhinoEngine engine, boolean sealed) {
        this.engine = engine;
        init(cx, engine, sealed);
    }

    public void init(Context cx, RhinoEngine engine, boolean sealed) {
        // Define some global functions particular to the shell. Note
        // that these functions are not part of ECMA.
        initStandardObjects(cx, sealed);
        initQuitAction(new QuitAction() {
            public void quit(Context cx, int exitCode) {
                System.exit(exitCode);
            }
        });
        String[] names = {
            "doctest",
            "gc",
            "load",
            "loadClass",
            "print",
            "quit",
            "readFile",
            "readUrl",
            "runCommand",
            "seal",
            "sync",
            "toint32",
            "version",
        };
        defineFunctionProperties(names, Global.class,
                                 ScriptableObject.DONTENUM);
        names = new String[] {
            "defineClass",
            "getResource",
            "getRepository",
            "addToClasspath",
            "privileged",
            "spawn",
            "trycatch",
            "enterAsyncTask",
            "exitAsyncTask"
        };
        defineFunctionProperties(names, RingoGlobal.class,
                                 ScriptableObject.DONTENUM);
        defineProperty("require", new Require(engine, this), DONTENUM);
        defineProperty("arguments", cx.newArray(this, engine.getArguments()), DONTENUM);
        // Set up "environment" in the global scope to provide access to the
        // System environment variables. http://github.com/ringo/ringojs/issues/#issue/88
        Environment.defineClass(this);
        Environment environment = new Environment(this);
        defineProperty("environment", environment, ScriptableObject.DONTENUM);
    }

    public RhinoEngine getEngine() {
        return engine;
    }

    @SuppressWarnings("unchecked")
    public static void defineClass(final Context cx, Scriptable thisObj,
                                     Object[] args, Function funObj)
            throws IllegalAccessException, InstantiationException, InvocationTargetException {
        ScriptUtils.checkArguments(args, 1, 1);
        Object arg = args[0] instanceof Wrapper ? ((Wrapper) args[0]).unwrap() : args[0];
        if (!(arg instanceof Class)) {
            throw Context.reportRuntimeError("defineClass() requires a class argument");
        }
        RhinoEngine engine = ((RingoGlobal) funObj.getParentScope()).engine;
        engine.defineHostClass((Class) arg);
    }

    public static Object getResource(final Context cx, Scriptable thisObj,
                                     Object[] args, Function funObj) {
        if (args.length != 1 || !(args[0] instanceof String)) {
            throw Context.reportRuntimeError(
                    "getResource() requires a string argument");
        }
        RhinoEngine engine = ((RingoGlobal) funObj.getParentScope()).engine;
        try {
            Resource res = engine.findResource((String) args[0], null,
                    engine.getParentRepository(thisObj));
            return cx.getWrapFactory().wrapAsJavaObject(cx, engine.getScope(),
                    res, null);
        } catch (IOException iox) {
            throw Context.reportRuntimeError("Cannot find resource " + args[0] + "'");
        }
    }

    public static Object getRepository(final Context cx, Scriptable thisObj,
                                       Object[] args, Function funObj) {
        if (args.length != 1 || !(args[0] instanceof String)) {
            throw Context.reportRuntimeError(
                    "getRepository() requires a string argument");
        }
        RhinoEngine engine = ((RingoGlobal) funObj.getParentScope()).engine;
        try {
            Repository repo = engine.findRepository((String) args[0],
                    engine.getParentRepository(thisObj));
            return cx.getWrapFactory().wrapAsJavaObject(cx, engine.getScope(), repo, null);
        } catch (IOException iox) {
            throw Context.reportRuntimeError("Cannot find repository " + args[0] + "'");
        }
    }

    public static Object addToClasspath(final Context cx, Scriptable thisObj,
                                        Object[] args, Function funObj) {
        if (securityManager != null) {
            securityManager.checkPermission(RingoSecurityManager.GET_CLASSLOADER);
        }
        if (args.length != 1) {
            throw Context.reportRuntimeError(
                    "addToClasspath() requires one argument");
        }
        try {
            Trackable path;
            RhinoEngine engine = ((RingoGlobal) funObj.getParentScope()).engine;
            Object arg = args[0] instanceof Wrapper ?
                    ((Wrapper) args[0]).unwrap() : args[0];
            if (arg instanceof String) {
                path = engine.resolve((String) arg,
                        engine.getParentRepository(thisObj));
            } else if (arg instanceof Trackable) {
                path = (Trackable) arg;
            } else {
                throw Context.reportRuntimeError(
                        "addToClasspath() requires a path argument");
            }
            engine.addToClasspath(path);
            return path.exists() ? Boolean.TRUE : Boolean.FALSE;
        } catch (IOException iox) {
            throw new WrappedException(iox);
        }
    }

    @SuppressWarnings("unchecked")
    public static Object privileged(final Context cx, Scriptable thisObj,
                                    Object[] args, Function funObj) {
        if (args.length != 1 || !(args[0] instanceof Function)) {
            throw Context.reportRuntimeError(
                    "privileged() requires a function argument");
        }
        final Scriptable scope = getTopLevelScope(thisObj);
        Scriptable s = cx.newObject(scope);
        s.put("run", s, args[0]);
        final Object[] jargs = {new NativeJavaClass(scope, PrivilegedAction.class), s};
        PrivilegedAction action = AccessController.doPrivileged(
                new PrivilegedAction<PrivilegedAction>() {
                    public PrivilegedAction run() {
                        return (PrivilegedAction) ((Wrapper) cx.newObject(scope,
                                "JavaAdapter", jargs)).unwrap();
                    }
                }
        );
        // PrivilegedAction action = (PrivilegedAction) InterfaceAdapter.create(cx, PrivilegedAction.class, (Callable) args[0]);
        return cx.getWrapFactory().wrap(cx, scope,
                AccessController.doPrivileged(action), null);
    }

    public static Object trycatch(final Context cx, Scriptable thisObj, Object[] args,
                                    Function funObj) {
        if (args.length != 1 || !(args[0] instanceof Function)) {
            throw Context.reportRuntimeError("trycatch() requires a function argument");
        }
        Scriptable scope = getTopLevelScope(thisObj);
        try {
            return ((Function)args[0]).call(cx, scope, thisObj, ScriptRuntime.emptyArgs);
        } catch (RhinoException re) {
            return new NativeJavaObject(scope, re, null);
        }
    }

    public static Object spawn(Context cx, Scriptable thisObj,
                               Object[] args, Function funObj) {
        if (securityManager != null) {
            securityManager.checkPermission(RingoSecurityManager.SPAWN_THREAD);
        }
        if (args.length < 1  || !(args[0] instanceof Function)) {
            throw Context.reportRuntimeError("spawn() requires a function argument");
        }
        final Scriptable scope = funObj.getParentScope();
        final ContextFactory cxfactory = cx.getFactory();
        final Function function = (Function) args[0];
        final Object[] fnArgs;
        if (args.length > 1 && args[1] instanceof Scriptable) {
            fnArgs = cx.getElements((Scriptable) args[1]);
        } else {
            fnArgs = ScriptRuntime.emptyArgs;
        }
        return getThreadPool().submit(new Callable<Object>() {
            public Object call() {
                return cxfactory.call(new ContextAction() {
                    public Object run(Context cx) {
                        return function.call(cx, scope, scope, fnArgs);
                    }
                });
            }
        });
    }

    public void enterAsyncTask() {
        engine.enterAsyncTask();
    }

    public void exitAsyncTask() {
        engine.exitAsyncTask();
    }

    static ExecutorService getThreadPool() {
        if (threadPool != null) {
            return threadPool;
        }
        synchronized (Global.class) {
            if (threadPool == null) {
                threadPool = Executors.newCachedThreadPool(new ThreadFactory() {
                    public Thread newThread(Runnable runnable) {
                        Thread thread = new Thread(runnable,
                                "ringo-spawn-" + ids.incrementAndGet());
                        thread.setDaemon(true);
                        return thread;
                    }
                });
            }
            return threadPool;
        }
    }

}
