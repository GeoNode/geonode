/*
 *  Copyright 2008 Hannes Wallnoefer <hannes@helma.at>
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

package org.ringojs.tools;

import jline.Completor;
import jline.ConsoleReader;
import jline.History;
import org.ringojs.engine.ModuleScope;
import org.ringojs.engine.ReloadableScript;
import org.ringojs.engine.RhinoEngine;
import org.ringojs.engine.RingoConfiguration;
import org.ringojs.engine.RingoWorker;
import org.ringojs.engine.ScriptError;
import org.ringojs.repository.Repository;
import org.mozilla.javascript.*;
import org.mozilla.javascript.tools.ToolErrorReporter;
import org.ringojs.repository.Resource;
import org.ringojs.repository.StringResource;
import org.ringojs.wrappers.ScriptableList;

import java.io.*;
import java.util.Collections;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.security.CodeSource;
import java.security.CodeSigner;

/**
 * RingoShell is a simple interactive shell that provides the
 * additional global functions implemented by Ringo.
 */
public class RingoShell {

    RingoConfiguration config;
    RhinoEngine engine;
    RingoWorker worker;
    Scriptable scope;
    boolean silent;
    File history;
    CodeSource codeSource = null;

    public RingoShell(RhinoEngine engine) throws IOException {
        this(engine, null, false);
    }

    public RingoShell(RhinoEngine engine, File history, boolean silent)
            throws IOException {
        this.config = engine.getConfig();
        this.engine = engine;
        this.history = history;
    	this.scope = engine.getShellScope();
        this.silent = silent;
        this.worker = engine.getWorker();
        // FIXME give shell code a trusted code source in case security is on
        if (config.isPolicyEnabled()) {
            Repository modules = config.getRingoHome().getChildRepository("modules");
            codeSource = new CodeSource(modules.getUrl(), (CodeSigner[])null);
        }
    }

    public void run() throws IOException {
        if (silent) {
            // bypass console if running with redirected stdin or stout
            runSilently();
            return;
        }
        preloadShellModule();
        ConsoleReader reader = new ConsoleReader();
        reader.setBellEnabled(false);
        // reader.setDebug(new PrintWriter(new FileWriter("jline.debug")));
        reader.addCompletor(new JSCompletor());
        if (history == null) {
            history = new File(System.getProperty("user.home"), ".ringo-history");
        }
        reader.setHistory(new History(history));
        PrintStream out = System.out;
        int lineno = 0;
        repl: while (true) {
            Context cx = engine.getContextFactory().enterContext(null);
            cx.setErrorReporter(new ToolErrorReporter(false, System.err));
            String source = "";
            String prompt = getPrompt();
            while (true) {
                String newline = reader.readLine(prompt);
                if (newline == null) {
                    // NULL input, if e.g. Ctrl-D was pressed
                    out.println();
                    out.flush();
                    break repl;
                }
                source = source + newline + "\n";
                lineno++;
                if (cx.stringIsCompilableUnit(source)) {
                    break;
                }
                prompt = getSecondaryPrompt();
            }
            try {
                Resource res = new StringResource("<stdin>", source, lineno);
                ReloadableScript script = new ReloadableScript(res, engine);
                Object result = worker.evaluateScript(cx, script, scope);

                printResult(result, out);
                lineno++;
                // trigger GC once in a while - if we run in non-interpreter mode
                // we generate a lot of classes to unload
                if (lineno % 10 == 0) {
                    System.gc();
                }
            } catch (Exception ex) {
                // TODO: should this print to System.err?
                printError(ex, out, config.isVerbose());
            } finally {
                Context.exit();
            }
        }
        System.exit(0);
    }

    protected String getPrompt() {
        return ">> ";
    }

    protected String getSecondaryPrompt() {
        return ".. ";
    }

    protected void printResult(Object result, PrintStream out) {
        try {
            worker.invoke("ringo/shell", "printResult", result);
        } catch (Exception x) {
            // Avoid printing out undefined or function definitions.
            if (result != Context.getUndefinedValue()) {
                out.println(Context.toString(result));
            }
            out.flush();
        }
    }

    protected void printError(Exception ex, PrintStream out, boolean verbose) {
        List<ScriptError> errors = worker.getErrors();
        try {
            worker.invoke("ringo/shell", "printError", ex,
                    new ScriptableList(scope, errors), Boolean.valueOf(verbose));
        } catch (Exception x) {
            // fall back to RingoRunner.reportError()
            RingoRunner.reportError(ex, out, errors, verbose);
        }
    }

    private void runSilently() throws IOException {
        int lineno = 0;
        outer: while (true) {
            Context cx = engine.getContextFactory().enterContext(null);
            cx.setErrorReporter(new ToolErrorReporter(false, System.err));
            String source = "";
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            while (true) {
                String line = reader.readLine();
                if (line == null) {
                    // reached EOF
                    break outer;
                }
                source = source + line + "\n";
                lineno++;
                if (cx.stringIsCompilableUnit(source))
                    break;
            }
            try {
                Resource res = new StringResource("<stdin>", source, lineno);
                ReloadableScript script = new ReloadableScript(res, engine);
                worker.evaluateScript(cx, script, scope);
                lineno++;
            } catch (Exception ex) {
                RingoRunner.reportError(ex, System.err, worker.getErrors(),
                        config.isVerbose());
            } finally {
                Context.exit();
            }
        }
        System.exit(0);
    }

    // preload ringo/shell in separate thread
    private void preloadShellModule() {
        Thread t = new Thread() {
            public void run() {
                Context cx = engine.getContextFactory().enterContext(null);
                try {
                    worker.loadModule(cx, "ringo/shell", null);
                } catch (Exception ignore) {
                    // ignore
                } finally {
                    Context.exit();
                }
            }
        };
        t.setPriority(Thread.MIN_PRIORITY);
        t.setDaemon(true);
        t.start();
    }

    class JSCompletor implements Completor {

        Pattern variables = Pattern.compile(
                "(^|\\s|[^\\w\\.'\"])([\\w\\.]+)$");
        Pattern keywords = Pattern.compile(
                "(^|\\s)([\\w]+)$");

        @SuppressWarnings("unchecked")
        public int complete(String s, int i, List list) {
            int start = i;
            try {
                Matcher match = keywords.matcher(s);
                if (match.find() && s.length() == i) {
                    String word = match.group(2);
                    for(String str: jsKeywords) {
                        if (str.startsWith(word)) {
                            list.add(str);
                        }
                    }
                }
                match = variables.matcher(s);
                if (match.find() && s.length() == i) {
                    String word = match.group(2);
                    Scriptable obj = scope;
                    String[] parts = word.split("\\.", -1);
                    for (int k = 0; k < parts.length - 1; k++) {
                        Object o = ScriptableObject.getProperty(obj, parts[k]);
                        if (o == null || o == ScriptableObject.NOT_FOUND) {
                            return start;
                        }
                        obj = ScriptRuntime.toObject(scope, o);
                    }
                    String lastpart = parts[parts.length - 1];
                    // set return value to beginning of word we're replacing
                    start = i - lastpart.length();
                    while (obj != null) {
                        // System.err.println(word + " -- " + obj);
                        Object[] ids = obj.getIds();
                        collectIds(ids, obj, word, lastpart, list);
                        if (list.size() <= 3 && obj instanceof ScriptableObject) {
                            ids = ((ScriptableObject) obj).getAllIds();
                            collectIds(ids, obj, word, lastpart, list);
                        }
                        if (word.endsWith(".") && obj instanceof ModuleScope) {
                            // don't walk scope prototype chain if nothing to compare yet -
                            // the list is just too long.
                            break;
                        }
                        obj = obj.getPrototype();
                    }
                }
            } catch (Exception ignore) {
                // ignore.printStackTrace();
            }
            Collections.sort(list);
            return start;
        }

        @SuppressWarnings("unchecked")
        private void collectIds(Object[] ids, Scriptable obj, String word, String lastpart, List list) {
            for(Object id: ids) {
                if (!(id instanceof String)) {
                    continue;
                }
                String str = (String) id;
                if (str.startsWith(lastpart) || word.endsWith(".")) {
                    if (ScriptableObject.getProperty(obj, str) instanceof Callable) {
                        list.add(str + "(");
                    } else {
                        list.add(str);
                    }
                }
            }
        }

    }

    static String[] jsKeywords =
        new String[] {
            "break",
            "case",
            "catch",
            "continue",
            "default",
            "delete",
            "do",
            "else",
            "finally",
            "for",
            "function",
            "if",
            "in",
            "instanceof",
            "new",
            "return",
            "switch",
            "this",
            "throw",
            "try",
            "typeof",
            "var",
            "void",
            "while",
            "with"
    };

}

