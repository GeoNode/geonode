/*
 *  Copyright 2004 Hannes Wallnoefer <hannes@helma.at>
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

import org.mozilla.javascript.json.JsonParser;
import org.ringojs.repository.*;
import org.ringojs.tools.RingoDebugger;
import org.ringojs.tools.launcher.RingoClassLoader;
import org.ringojs.wrappers.*;
import org.mozilla.javascript.*;
import org.mozilla.javascript.tools.debugger.ScopeProvider;

import java.io.*;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.net.MalformedURLException;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.LinkedBlockingDeque;

/**
 * This class provides methods to create JavaScript objects
 * from JavaScript files.
 *
 * @author Hannes Wallnoefer <hannes@helma.at>
 */
public class RhinoEngine implements ScopeProvider {

    private RingoConfiguration config;
    private List<Repository> repositories;
    private RingoGlobal globalScope;
    private List<String> commandLineArgs;
    private Map<Trackable, ReloadableScript> compiledScripts, interpretedScripts;
    private final Map<Singleton, Singleton> singletons;
    private AppClassLoader loader = new AppClassLoader();
    private WrapFactory wrapFactory;
    private Set<Class> hostClasses;
    private ModuleLoader[] loaders;

    private RingoContextFactory contextFactory = null;
    private ModuleScope mainScope = null;

    private final RingoWorker mainWorker;
    private final ThreadLocal<RingoWorker> currentWorker = new ThreadLocal<RingoWorker>();
    private final Deque<RingoWorker> workers;
    private final AsyncTaskCounter asyncCounter = new AsyncTaskCounter();

    public static final List<Integer> VERSION =
            Collections.unmodifiableList(Arrays.asList(0, 9));

    /**
     * Create a RhinoEngine with the given configuration. If <code>globals</code>
     * is not null, its contents are added as properties on the global object.
     *
     * @param config the configuration used to initialize the engine.
     * @param globals an optional map of global properties
     * @throws Exception if the engine can't be created
     */
    public RhinoEngine(RingoConfiguration config, Map<String, Object> globals)
            throws Exception {
        this.config = config;
        workers = new LinkedBlockingDeque<RingoWorker>();
        mainWorker = new RingoWorker(this);
        compiledScripts = new ConcurrentHashMap<Trackable, ReloadableScript>();
        interpretedScripts = new ConcurrentHashMap<Trackable, ReloadableScript>();
        singletons = new HashMap<Singleton, Singleton>();
        contextFactory = new RingoContextFactory(this, config);
        repositories = config.getRepositories();
        this.wrapFactory = config.getWrapFactory();
        
        loaders = new ModuleLoader[] {
            new JsModuleLoader(), new JsonModuleLoader(), new ClassModuleLoader()
        };

        RingoDebugger debugger = null;
        if (config.getDebug()) {
            debugger = new RingoDebugger(config);
            debugger.setScopeProvider(this);
            debugger.attachTo(contextFactory);
            debugger.setBreakOnExceptions(true);
        }

        // create and initialize global scope
        Context cx = contextFactory.enterContext();
        try {
            boolean sealed = config.isSealed();
            globalScope = new RingoGlobal(cx, this, sealed);
            Class<Scriptable>[] classes = config.getHostClasses();
            if (classes != null) {
                for (Class<Scriptable> clazz: classes) {
                    defineHostClass(clazz);
                }
            }
            ScriptableList.init(globalScope);
            ScriptableMap.init(globalScope);
            ScriptableObject.defineClass(globalScope, ScriptableWrapper.class);
            ScriptableObject.defineClass(globalScope, ModuleObject.class);
            if (globals != null) {
                for (Map.Entry<String, Object> entry : globals.entrySet()) {
                    ScriptableObject.defineProperty(globalScope, entry.getKey(),
                            entry.getValue(), ScriptableObject.DONTENUM);
                }
            }
            mainWorker.evaluateScript(cx, getScript("ringo/global"), globalScope);
            evaluateBootstrapScripts(cx);
            if (sealed) {
                globalScope.sealObject();
            }
            if (debugger != null) {
                debugger.setBreak();
            }
        } finally {
            Context.exit();
        }
    }

    /**
     * Define a Javascript host object implemented by the given class.
     * @param clazz The Java class implementing the host object.
     * @exception IllegalAccessException if access is not available
     *            to a reflected class member
     * @exception InstantiationException if unable to instantiate
     *            the named class
     * @exception InvocationTargetException if an exception is thrown
     *            during execution of methods of the named class
     */
    public void defineHostClass(Class<Scriptable> clazz)
            throws InvocationTargetException, InstantiationException, IllegalAccessException {
        if (hostClasses != null && hostClasses.contains(clazz)) {
            return;
        }
        synchronized (this) {
            if (hostClasses == null) {
                hostClasses = new HashSet<Class>();
            }
            hostClasses.add(clazz);
            ScriptableObject.defineClass(globalScope, clazz);
        }
    }

    /**
     * Invoke a script from the command line.
     * @param scriptResource the script resource of path
     * @param scriptArgs an array of command line arguments
     * @return the return value
     * @throws IOException an I/O related error occurred
     * @throws JavaScriptException the script threw an error during
     *         compilation or execution
     */
    public Object runScript(Object scriptResource, String... scriptArgs)
            throws IOException, JavaScriptException {
        Resource resource;
        if (scriptResource instanceof Resource) {
            resource = (Resource) scriptResource;
        } else if (scriptResource instanceof String) {
            resource = findResource((String) scriptResource, null, null);
        } else {
            throw new IOException("Unsupported script resource: " + scriptResource);
        }
        if (!resource.exists()) {
            throw new FileNotFoundException(scriptResource.toString());
        }
        Context cx = contextFactory.enterContext();
        try {
            Object retval;
            Map<Trackable,ReloadableScript> scripts = getScriptCache(cx);
            commandLineArgs = Arrays.asList(scriptArgs);
            ReloadableScript script = new ReloadableScript(resource, this);
            scripts.put(resource, script);
            mainScope = new ModuleScope(resource.getModuleName(), resource, globalScope);
            retval = mainWorker.evaluateScript(cx, script, mainScope);
            mainScope.updateExports();
            return retval instanceof Wrapper ? ((Wrapper) retval).unwrap() : retval;
        } finally {
            Context.exit();
        }
    }

    /**
     * Evaluate an expression from the command line.
     * @param expr the JavaScript expression to evaluate
     * @return the return value
     * @throws IOException an I/O related error occurred
     * @throws JavaScriptException the script threw an error during
     *         compilation or execution
     */
    public Object evaluateExpression(String expr)
            throws IOException, JavaScriptException {
        Context cx = contextFactory.enterContext();
        cx.setOptimizationLevel(-1);
        try {
            Object retval;
            Repository repository = repositories.get(0);
            Scriptable parentScope = mainScope != null ? mainScope : globalScope;
            ModuleScope scope = new ModuleScope("<expr>", repository, parentScope);
            Resource res = new StringResource("<expr>", expr, 1);
            ReloadableScript script = new ReloadableScript(res, this);
            retval = mainWorker.evaluateScript(cx, script, scope);
            return retval instanceof Wrapper ? ((Wrapper) retval).unwrap() : retval;
        } finally {
            Context.exit();
        }
    }

    /**
     * Invoke a javascript function. This enters a JavaScript context, creates
     * a new per-thread scope, calls the function, exits the context and returns
     * the return value of the invocation.
     *
     * @param module the module name or object, or null for the main module
     * @param method the method name to call in the script
     * @param args the arguments to pass to the method
     * @return the return value of the invocation
     * @throws NoSuchMethodException the method is not defined
     * @throws IOException an I/O related error occurred
     */
    public Object invoke(Object module, String method, Object... args)
            throws IOException, NoSuchMethodException, ExecutionException,
                    InterruptedException {
        return mainWorker.invoke(module, method, args);
    }

    /**
     * Get the worker associated with the current thread, or null if no worker
     * is associated with the current thread.
     * @return the worker associated with the current thread, or null.
     */
    public RingoWorker getCurrentWorker() {
        return currentWorker.get();
    }

    protected void setCurrentWorker(RingoWorker worker) {
        if (worker == null) {
            currentWorker.remove();
        } else {
            currentWorker.set(worker);
        }
    }

    /**
     * Get a new {@link RingoWorker}.
     * @return a worker instance.
     */
    public RingoWorker getWorker() {
        RingoWorker worker = workers.pollFirst();
        if (worker == null) {
            worker = new RingoWorker(this);
        }
        return worker;
    }

    /**
     * Return a worker, returning it to the worker pool.
     * @param worker the worker to be released
     */
    void returnWorker(RingoWorker worker) {
        if (!workers.offerFirst(worker)) {
            worker.shutdown();
        }
    }

    /**
     * Get the list of errors encountered by the main worker.
     * @return a list of errors, may be null.
     */
    public List<ScriptError> getMainErrors() {
        return mainWorker.getErrors();
    }

    /**
     * Get the list of errors encountered by the current worker. This will only
     * succeed if a worker is associated with the current thread. Otherwise this
     * method returns null.
     * @return a list of errors, null if no worker is associated with the
     * current thread.
     */
    public List<ScriptError> getCurrentErrors() {
        RingoWorker worker = currentWorker.get();
        return worker != null ? worker.getErrors() : null;
    }

    /**
     * Return a shell scope for interactive evaluation
     * @return a shell scope
     * @throws IOException an I/O related exception occurred
     */
    public Scriptable getShellScope() throws IOException {
        Repository repository = new FileRepository("");
        repository.setAbsolute(true);
        Scriptable protoScope = mainScope != null ? mainScope : globalScope;
        return new ModuleScope("<shell>", repository, protoScope);
    }

    /**
     * Get the engine's global shared scope
     * @return the global scope
     */
    public Scriptable getScope() {
        return globalScope;
    }

    /**
     * Initialize and normalize the global variables and arguments on a thread scope.
     * @param args the arguments
     */
    protected void initArguments(Object[] args) {
        if (args != null) {
            for (int i = 0; i < args.length; i++) {
                args[i] = wrapArgument(args[i], globalScope);
            }
        }
    }

    /**
     * Prepare a single property or argument value for use within rhino.
     * @param value the property or argument value
     * @param scope the scope
     * @return the object wrapped and wired for rhino
     */
    public static Object wrapArgument(Object value, Scriptable scope) {
        if (value instanceof ScriptableObject) {
            ScriptableObject scriptable = ((ScriptableObject) value);
            // Avoid overwriting prototype and parent scope as this would break closures
            if (scriptable.getPrototype() == null) {
                scriptable.setPrototype(ScriptableObject.getClassPrototype(
                        scope, scriptable.getClassName()));
            }
            if (scriptable.getParentScope() == null) {
                scriptable.setParentScope(scope);
            }
            return scriptable;
        } else {
            return Context.javaToJS(value, scope);
        }
    }

    /**
     * Get the current Rhino optimization level
     * @return the current optimization level
     */
    public int getOptimizationLevel() {
        Context cx = Context.getCurrentContext();
        if (cx != null) {
            return cx.getOptimizationLevel();
        }
        return 0;
    }

    /**
     * Set Rhino optimization level
     * @param level the new optimization level
     */
    public void setOptimizationLevel(int level) {
        Context cx = Context.getCurrentContext();
        if (cx != null && cx.getOptimizationLevel() != level) {
            cx.setOptimizationLevel(level);
        }
    }

    /**
     * Resolves a type name to a script file within our script directory
     * and returns a Scriptable evaluated to the file.
     *
     * @param moduleName the name of the module to load
     * @return The raw compiled script for the module
     * @throws JavaScriptException if an error occurred evaluating the script file
     * @throws IOException if an error occurred reading the script file
     */
    public ReloadableScript getScript(String moduleName)
            throws JavaScriptException, IOException {
        return getScript(moduleName, null);
    }

    /**
     * Resolves a type name to a script file within our script directory
     * and returns a Scriptable evaluated to the file.
     *
     * @param moduleName the name of the module to load
     * @param localPath the path of the resource issuing this call
     * @return The raw compiled script for the module
     * @throws JavaScriptException if an error occurred evaluating the script file
     * @throws IOException if an error occurred reading the script file
     */
    public ReloadableScript getScript(String moduleName, Repository localPath)
            throws JavaScriptException, IOException {
        ReloadableScript script;
        Resource source = findResource(moduleName, loaders, localPath);
        if (!source.exists()) {
            source = loadPackage(moduleName, localPath);
            if (!source.exists()) {
                source = findResource(moduleName, null, localPath);
            }
        }
        Context cx = Context.getCurrentContext();
        Map<Trackable,ReloadableScript> scripts = getScriptCache(cx);
        if (scripts.containsKey(source)) {
            script = scripts.get(source);
        } else {
            script = new ReloadableScript(source, this);
            if (source.exists()) {
                scripts.put(source, script);
            }
        }
        return script;
    }

    /**
     * Resolves a module id to a package resource. If module id consists of
     * just one term and resolves to a package directory, the main module of
     * the package is returned. If the module id consists of several terms
     * and the first term resolves to a package directory, the remaining part
     * of the module id is resolved against the "lib" directory of the package.
     *
     * @link http://nodejs.org/docs/v0.4.4/api/modules.html#folders_as_Modules
     * @param moduleName the name of the package to load
     * @param localPath the path of the resource issuing this call
     * @return the location of the package's main module
     * @throws IOException an unrecoverable I/O exception occurred while
     * reading the package
     */
    protected Resource loadPackage(String moduleName, Repository localPath)
            throws IOException {

        int slash = 0;
        String packageName, remainingName;

        do {
            slash = moduleName.indexOf('/', slash + 1);
            if (slash == -1) {
                packageName = moduleName;
                remainingName = null;
            } else {
                packageName = moduleName.substring(0, slash);
                if (".".equals(packageName) || "..".equals(packageName))
                    continue;
                remainingName = moduleName.substring(slash + 1);
            }

            Resource json = findResource(packageName + "/package.json", null, localPath);

            if (json != null && json.exists()) {

                Scriptable obj = parseJsonResource(json);
                Repository parent = json.getParentRepository();
                String moduleId;
                Resource res;

                if (remainingName == null) {
                    // get the main module of this package
                    moduleId = getStringProperty(obj, "main", null);
                    if (moduleId != null) {
                        // optimize for the common case where main module
                        // property links to the exact file name
                        res = parent.getResource(moduleId);
                        if (res != null && res.exists()) return res;
                    }
                } else {
                    // map remaining name to libs directory
                    String lib = "lib";
                    Object dirs = ScriptableObject.getProperty(obj, "directories");
                    if (dirs instanceof Scriptable) {
                        lib = getStringProperty((Scriptable)dirs, "lib", "lib");
                    }
                    moduleId = lib + "/" + remainingName;
                }

                if (moduleId != null) {
                    for (ModuleLoader loader: loaders) {
                        res = parent.getResource(moduleId + loader.getExtension());
                        if (res != null && res.exists()) return res;
                    }
                    if (remainingName != null) {
                        res = parent.getResource(moduleId);
                        if (res != null && res.exists()) return res;
                    }
                }

            }

        } while (slash != -1);

        return findResource(moduleName + "/index", loaders, localPath);
    }
    
    private Scriptable parseJsonResource(Resource resource) throws IOException {
        JsonParser parser = new JsonParser(Context.getCurrentContext(), globalScope);
        try {
            Object result = parser.parseValue(resource.getContent());
            if (!(result instanceof Scriptable)) {
                throw new RuntimeException(
                        "Expected Object from package.json, got " + result);
            }
            return (Scriptable) result;
        } catch (JsonParser.ParseException px) {
            throw new RuntimeException(px);
        }
    }
    
    private String getStringProperty(Scriptable obj, String name, String defaultValue) {
        Object value = ScriptableObject.getProperty(obj, name);
        if (value != null && value != ScriptableObject.NOT_FOUND) {
            return ScriptRuntime.toString(value);
        }
        return defaultValue;
    }


    /**
     * Load a Javascript module into a module scope. This checks if the module has already
     * been loaded in the current context and if so returns the existing module scope.
     * @param cx the current context
     * @param moduleName the module name
     * @param loadingScope the scope requesting the module
     * @return the loaded module's scope
     * @throws IOException indicates that in input/output related error occurred
     */
    public Scriptable loadModule(Context cx, String moduleName,
                                  Scriptable loadingScope)
            throws IOException {
        return mainWorker.loadModule(cx, moduleName, loadingScope);
    }

    /**
     * Get the name of the main script as module name, if any
     * @return the main module name, or null
     */
    public String getMainModule() {
        return config.getMainModule();
    }

    /**
     * Get the main scrip's module scope, if any
     * @return the main module scope, or null
     */
    public ModuleScope getMainModuleScope() {
        return mainScope;
    }

    /**
     * Get the script arguments as object array suitable for use with Context.newArray().
     * @return the script arguments
     */
    public Object[] getArguments() {
        String[] args = config.getArguments();
        if (args == null) {
            return ScriptRuntime.emptyArgs;
        } else {
            Object[] array = new Object[args.length];
            System.arraycopy(args, 0, array, 0, args.length);
            return array;
        }
    }

    public String getCharset() {
        return config.getCharset();
    }

    /**
     * Get the currently active RhinoEngine instance.
     * @param scope the global scope or a top level module scope
     * @return the current RhinoEngine
     */
    public static RhinoEngine getEngine(Scriptable scope) {
        if (scope instanceof ModuleScope) {
            scope = scope.getPrototype();
        }
        if (scope instanceof RingoGlobal) {
            return ((RingoGlobal) scope).getEngine();
        }
        throw new IllegalArgumentException("Unsupported scope");
    }

    /**
     * Create a sandboxed scripting engine with the same install directory as this and the
     * given module paths, global properties, class shutter and sealing
     * @param config the sandbox configuration
     * @param globals a map of predefined global properties, may be null
     * @return a sandboxed RhinoEngine instance
     * @throws FileNotFoundException if any part of the module paths does not exist
     */
    public RhinoEngine createSandbox(RingoConfiguration config, Map<String,Object> globals)
            throws Exception {
        config.setPolicyEnabled(this.config.isPolicyEnabled());
        return new RhinoEngine(config, globals);
    }

    protected boolean isPolicyEnabled() {
        // only use security when ringo runs standalone with default security manager,
        // not with google app engine
        return config.isPolicyEnabled();
    }

    /**
     * Wait until all daemon threads running in this engine have terminated.
     * @throws InterruptedException if the current thread has been interrupted
     */
    public void waitForAsyncTasks() throws InterruptedException {
        asyncCounter.waitTillDone();
    }

    protected void enterAsyncTask() {
        asyncCounter.increase();
    }

    protected void exitAsyncTask() {
        asyncCounter.decrease();
    }

    private Map<Trackable,ReloadableScript> getScriptCache(Context cx) {
        return cx.getOptimizationLevel() == -1 ?
                interpretedScripts : compiledScripts;
    }

    private void evaluateBootstrapScripts(Context cx)
            throws IOException {
        List<String> bootstrapScripts = config.getBootstrapScripts();
        if (bootstrapScripts != null) {
            for(String script : bootstrapScripts) {
                Resource resource = new FileResource(script);
                // not found, attempt to resolve the file relative to ringo home
                if (!resource.exists()) {
                    resource = getRingoHome().getResource(script);
                }
                if (resource == null || !resource.exists()) {
                    throw new FileNotFoundException(
                            "Bootstrap script " + script + " not found");
                }
                mainWorker.evaluateScript(cx, new ReloadableScript(resource, this),
                        globalScope);
            }
        }
    }

    /**
     * Get the list of command line arguments
     * @return the command line arguments passed to this engine
     */
    public List<String> getCommandLineArguments() {
        if (commandLineArgs == null) {
            commandLineArgs = Collections.emptyList();
        }
        return Collections.unmodifiableList(commandLineArgs);
    }

    /**
     * Get the engine's module search path as a list of repositories
     * @return the module repositories
     */
    public List<Repository> getRepositories() {
        return repositories;
    }

    /**
     * Get the our installation directory.
     * @return the RingoJS installation directory
     */
    public Repository getRingoHome() {
        return config.getRingoHome();
    }

    /**
     * Get the repository associated with the scope or one of its prototypes
     *
     * @param scope the scope to get the repository from
     * @return the repository, or null
     */
    public Repository getParentRepository(Scriptable scope) {
        while (scope != null) {
            if (scope instanceof ModuleScope) {
                return ((ModuleScope) scope).getRepository();
            }
            scope = scope.getPrototype();
        }
        return null;
    }

    /**
     * Get a list of all child resources for the given path relative to
     * our script repository.
     * @param path the repository path
     * @param recursive whether to include nested resources
     * @return a list of all contained child resources
     */
    public List<Resource> findResources(String path, boolean recursive) throws IOException {
        return config.getResources(path, recursive);
    }

    /**
     * Try to resolve path to a resource or repository relative to a local path,
     * or the engine's repository path.
     * @param path the resource name
     * @param localRoot a repository to look first
     * @return the resource or repository
     * @throws IOException if an I/O error occurred
     */
    public Trackable resolve(String path, Repository localRoot) throws IOException {
        Trackable t = findResource(path, null, localRoot);
        if (t == null || !t.exists()) {
            t = findRepository(path, localRoot);
        }
        return t;
    }

    /**
     * Search for a resource in a local path, or the main repository path.
     * @param path the resource name
     * @param loaders optional list of module loaders
     * @param localRoot a repository to look first
     * @return the resource
     * @throws IOException if an I/O error occurred
     */
    public Resource findResource(String path, ModuleLoader[] loaders,
                                 Repository localRoot)
            throws IOException {
        // Note: as an extension to the CommonJS modules API
        // we allow absolute module paths for resources
        File file = new File(path);
        if (file.isAbsolute()) {
            Resource res;
            outer: if (loaders != null) {
                // loaders must contain at least one loader
                assert loaders.length > 0 && loaders[0] != null;
                for (ModuleLoader loader: loaders) {
                    res = new FileResource(path + loader.getExtension());
                    if (res.exists()) {
                        break outer;
                    }
                }
                res = new FileResource(path + loaders[0].getExtension());
            } else {
                res = new FileResource(file);
            }
            res.setAbsolute(true);
            return res;
        } else if (localRoot != null && 
                (path.startsWith("./") || path.startsWith("../"))) {
            String newpath = localRoot.getRelativePath() + path;
            return findResource(newpath, loaders, null);
        } else {
            return config.getResource(normalizePath(path), loaders);
        }
    }

    /**
     * Search for a repository in the local path, or the main repository path.
     * @param path the repository name
     * @param localPath a repository to look first
     * @return the repository
     * @throws IOException if an I/O error occurred
     */
    public Repository findRepository(String path, Repository localPath) throws IOException {
        // To be consistent, always return absolute repository if path is absolute
        // if we make this dependent on whether files exist we introduce a lot of
        // vague and undetermined behaviour.
        File file = new File(path);
        if (file.isAbsolute()) {
            return new FileRepository(file);
        }
        if (localPath != null) {
            Repository repository = localPath.getChildRepository(path);
            if (repository != null && repository.exists()) {
                return repository;
            }
        }
        return config.getRepository(normalizePath(path));
    }
    
    public ModuleLoader getModuleLoader(Resource resource) {
        String name = resource.getName();
        for (ModuleLoader loader : loaders) {
            if (name.endsWith(loader.getExtension())) {
                return loader;
            }
        }
        return loaders[0];
    }

    public synchronized void addModuleLoader(String extension, Object value) {
        if (value == null || value == Undefined.instance) {
            removeModuleLoader(extension);
        } else if (!(value instanceof Function)) {
            throw Context.reportRuntimeError("Module loader must be a function");
        }
        Function function = (Function) value;
        int length = loaders.length;
        for (int i = 0; i < length; i++) {
            if (extension.equals(loaders[i].getExtension())) {
                // replace existing loader
                loaders[i] = new ScriptedModuleLoader(extension, function);
                return;
            }
        }
        ModuleLoader[] newLoaders = new ModuleLoader[length + 1];
        System.arraycopy(loaders, 0, newLoaders, 0, length);
        newLoaders[length] = new ScriptedModuleLoader(extension, function);
        loaders = newLoaders;
    }
    
    public synchronized void removeModuleLoader(String extension) {
        int length = loaders.length;
        for (int i = 0; i < length; i++) {
            if (loaders[i] instanceof ScriptedModuleLoader && 
                    extension.equals(loaders[i].getExtension())) {
                ModuleLoader[] newLoaders = new ModuleLoader[length - 1];
                if (i > 0) 
                    System.arraycopy(loaders, 0, newLoaders, 0, i);
                if (i < length - 1) 
                    System.arraycopy(loaders, i + 1, newLoaders, i, length - i - 1);
                loaders = newLoaders;
                return;
            }
        }
    }
    
    public static String normalizePath(String path) {
        if (!path.contains("./")) {
            return path;
        }
        boolean absolute = path.startsWith("/");
        String[] elements = path.split(Repository.SEPARATOR);
        LinkedList<String> list = new LinkedList<String>();
        for (String e : elements) {
            if ("..".equals(e)) {
                if (list.isEmpty() || "..".equals(list.getLast())) {
                    list.add(e);
                } else {
                    list.removeLast();
                }
            } else if (!".".equals(e) && e.length() > 0) {
                list.add(e);
            }
        }
        StringBuilder sb = new StringBuilder(path.length());
        if (absolute) {
            sb.append("/");
        }
        int count = 0, last = list.size() - 1;
        for (String e : list) {
            sb.append(e);
            if (count++ < last)
                sb.append("/");
        }
        return sb.toString();
    }

    public void addToClasspath(Trackable path) throws MalformedURLException {
        loader.addURL(path.getUrl());
    }

    public RingoContextFactory getContextFactory() {
        return contextFactory;
    }

    public RingoClassLoader getClassLoader() {
        return loader;
    }

    public RingoConfiguration getConfig() {
        return config;
    }

    Singleton getSingleton(Singleton singleton) {
        synchronized (singletons) {
            Singleton st = singletons.get(singleton);
            if (st == null) {
                st = singleton;
                singletons.put(singleton, singleton);
            }
            return st;
        }
    }

    /**
     * Get a wrapper for a string that exposes the java.lang.String methods to JavaScript
     * This is useful for accessing strings as java.lang.String without the cost of
     * creating a new instance.
     * @param object an object
     * @return the object converted to a string and wrapped as native java object
     */
    public Object asJavaString(Object object) {
        if (!(object instanceof String)) {
            object = object.toString();
        }
        Context cx = Context.getCurrentContext();
        return wrapFactory.wrapAsJavaObject(cx, globalScope, object, null);
    }

    /**
     * Get a wrapper for an object that exposes it as Java object to JavaScript.
     * @param object an object
     * @return the object wrapped as native java object
     */
    public Object asJavaObject(Object object) {
        if (object instanceof Wrapper) {
            object = ((Wrapper) object).unwrap();
        }
        Context cx = Context.getCurrentContext();
        return wrapFactory.wrapAsJavaObject(cx, globalScope, object, null);
    }

    /**
     * Get the engine's WrapFactory.
     * @return the engine's WrapFactory instance
     */
    public WrapFactory getWrapFactory() {
        return wrapFactory;
    }

    static class AsyncTaskCounter {

        int count = 0;

        synchronized void waitTillDone() throws InterruptedException {
            while(count > 0) {
                wait();
            }
        }

        synchronized void increase() {
            ++count;
        }

        synchronized void decrease() {
            if (--count <= 0) {
                notifyAll();
            }
        }
    }

}

class AppClassLoader extends RingoClassLoader {

    HashSet<URL> urls = new HashSet<URL>();

    public AppClassLoader() {
        super(new URL[0], RhinoEngine.class.getClassLoader());
    }

    /**
     * Overrides addURL to make it accessable to RingoGlobal.addToClasspath()
     * @param url the url to add to the classpath
     */
    protected synchronized void addURL(URL url) {
        if (!urls.contains(url)) {
            urls.add(url);
            super.addURL(url);
        }
    }
}


