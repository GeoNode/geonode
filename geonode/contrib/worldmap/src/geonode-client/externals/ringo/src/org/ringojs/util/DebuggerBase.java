package org.ringojs.util;

import org.mozilla.javascript.Context;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.ContextFactory;
import org.mozilla.javascript.debug.DebugFrame;
import org.mozilla.javascript.debug.DebuggableScript;
import org.mozilla.javascript.debug.Debugger;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * A base class for Debuggers and Profilers implemented in Javascript.
 * This allows to exclude the debugger/profiler module and all modules
 * it uses to be excluded from debugging/profiling.
 */
public abstract class DebuggerBase implements Debugger {

    String debuggerScript;
    int debuggerScriptDepth = 0;
    Logger log = Logger.getLogger("org.ringojs.util.DebuggerBase");

    public abstract DebuggerBase createDebugger();

    public abstract Object createContextData();

    public abstract void handleCompilationDone(Context cx, DebuggableScript fnOrScript, String source);

    public abstract DebugFrame getScriptFrame(Context cx, DebuggableScript fnOrScript);

    public void attach() {
        attach(createContextData());
    }

    public void setDebuggerScript(String path) {
        debuggerScript = path;
    }

    public void install() {
        ContextFactory factory = Context.getCurrentContext().getFactory();
        factory.addListener(new ContextFactory.Listener() {
            public void contextCreated(Context cx) {
                DebuggerBase debugger = createDebugger();
                if (debugger != null) {
                    debugger.attach(createContextData());
                }
            }
            public void contextReleased(Context cx) {
            }
        });
    }

    public void attach(Object contextData) {
        Context cx = Context.getCurrentContext();
        cx.setDebugger(this, contextData);
        cx.setOptimizationLevel(-1);
        cx.setGeneratingDebug(true);
    }

    public void detach() {
        Context cx = Context.getCurrentContext();
        cx.setDebugger(null, null);
    }

    public Object getContextData() {
        return Context.getCurrentContext().getDebuggerContextData();
    }

    public synchronized void suspend() {
        try {
            wait();
        } catch (InterruptedException ir) {
            Thread.currentThread().interrupt();
        }
    }

    public synchronized void resume() {
        notify();
    }

    public DebugFrame getFrame(Context cx, DebuggableScript fnOrScript) {
        String path = fnOrScript.getSourceName();
        if (log.isLoggable(Level.FINE)) {
            log.fine("Getting Frame for " + path +
                      ", debugger script depth is " + debuggerScriptDepth);
        }
        if (debuggerScriptDepth > 0 || path.equals(debuggerScript)) {
            return new DebuggerScriptFrame();
        } else {
            return getScriptFrame(cx, fnOrScript);
        }
    }

    /**
     * Get a string representation for the given script
     * @param script a function or script
     * @return the file and/or function name of the script
     */
    static String getScriptName(DebuggableScript script) {
        if (script.isFunction()) {
            return script.getSourceName() + ": " + script.getFunctionName();
        } else {
            return script.getSourceName();
        }
    }

    class DebuggerScriptFrame implements DebugFrame {

        public void onEnter(Context cx, Scriptable activation, Scriptable thisObj, Object[] args) {
            log.fine("Entering debugger script frame");
            debuggerScriptDepth ++;
        }

        public void onExit(Context cx, boolean byThrow, Object resultOrException) {
            log.fine("Exiting debugger script frame");
            debuggerScriptDepth --;
        }

        public void onLineChange(Context cx, int lineNumber) {}

        public void onExceptionThrown(Context cx, Throwable ex) {}

        public void onDebuggerStatement(Context cx) {}
    }

}
