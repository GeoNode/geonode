/**
 * @fileOverview Provides access to the Rhino JavaScript engine.
 */

export( 'properties',
        'addHostObject',
        'addRepository',
        'asJavaString',
        'asJavaObject',
        'createSandbox',
        'evaluate',
        'getErrors',
        'getRingoHome',
        'getRepositories',
        'getRhinoContext',
        'getRhinoEngine',
        'getOptimizationLevel',
        'setOptimizationLevel',
        'serialize',
        'deserialize',
        'version');

var rhino = org.mozilla.javascript;
var engine = org.ringojs.engine;

/**
 * An object reflecting the Java system properties.
 */
try {
    var properties = new ScriptableMap(java.lang.System.getProperties());
} catch (error) {
    properties = {};
}

/**
 * The RingoJS version as an array-like object with the major and minor version
 * number as first and second element.
 */
var version = new ScriptableList(engine.RhinoEngine.VERSION);

/**
 * Define a class as Rhino host object.
 * @param {JavaClass} javaClass the class to define as host object
 */
function addHostObject(javaClass) {
    getRhinoEngine().defineHostClass(javaClass);
}

/**
 * Create a sandboxed scripting engine with the same install directory as this and the
 * given module paths, global properties, class shutter and sealing
 * @param {Array} modulePath the comma separated module search path
 * @param {Object} globals a map of predefined global properties (may be undefined)
 * @param {Object} options an options object (may be undefined). The following options are supported:
 *  - systemModules array of system module directories to add to the module search path
 *                  (may be relative to the ringo install dir)
 *  - classShutter a Rhino class shutter, may be null
 *  - sealed if the global object should be sealed, defaults to false
 * @returns {RhinoEngine} a sandboxed RhinoEngine instance
 * @throws {FileNotFoundException} if any part of the module paths does not exist
 */
function createSandbox(modulePath, globals, options) {
    options = options || {};
    var systemModules = options.systemModules || null;
    var config = new engine.RingoConfiguration(
            getRingoHome(), modulePath, systemModules);
    if (options.classShutter) {
        var shutter = options.shutter;
        config.setClassShutter(shutter instanceof rhino.ClassShutter ?
                shutter : new rhino.ClassShutter(shutter));
    }
    config.setSealed(Boolean(options.sealed));
    return getRhinoEngine().createSandbox(config, globals);
}

/**
 * Get the RingoJS installation directory.
 * @returns {Repository} a Repository representing the Ringo installation directory
 */
function getRingoHome() {
    return getRhinoEngine().getRingoHome();
}

/**
 * Get a wrapper for an object that exposes it as Java object to JavaScript.
 * @param {Object} object an object
 * @returns {Object} the object wrapped as native java object
 */
function asJavaObject(object) {
    return getRhinoEngine().asJavaObject(object);
}

/**
 * Get a wrapper for a string that exposes the java.lang.String methods to JavaScript
 * This is useful for accessing strings as java.lang.String without the cost of
 * creating a new instance.
 * @param {Object} object an object
 * @returns {Object} the object converted to a string and wrapped as native java object
 */
function asJavaString(object) {
    return getRhinoEngine().asJavaString(object);
}

/**
 * Get the Rhino optimization level for the current thread and context.
 * The optimization level is an integer between -1 (interpreter mode)
 * and 9 (compiled mode, all optimizations enabled). The default level
 * is 0.
 * @returns {Number} level an integer between -1 and 9
 */
function getOptimizationLevel() {
    return getRhinoEngine().getOptimizationLevel();
}

/**
 * Set the Rhino optimization level for the current thread and context.
 * The optimization level is an integer between -1 (interpreter mode)
 * and 9 (compiled mode, all optimizations enabled). The default level
 * is 0.
 * @param {Number} level an integer between -1 and 9
 */
function setOptimizationLevel(level) {
    getRhinoEngine().setOptimizationLevel(level);
}

/**
 * Evaluate a module script on an existing scope instead of creating a
 * new module scope. This can be used to mimic traditional JavaScript
 * environments such as those found in web browsers.
 * @param {String} moduleName the name of the module to evaluate
 * @param {Object} scope the JavaScript object to evaluate the script on
 */
function evaluate(moduleName, scope) {
    var script = getRhinoEngine().getScript(moduleName);
    if (!scope) {
        // create a new top level scope object
        scope = new engine.ModuleScope(moduleName, script.getSource(), global);
    }
    script.evaluate(scope, getRhinoContext());
    return scope;
}

/**
 * Get the org.mozilla.javascript.Context associated with the current thread.
 */
function getRhinoContext() {
    return rhino.Context.getCurrentContext();
}

/**
 * Get the org.ringojs.engine.RhinoEngine associated with this application.
 * @returns {org.ringojs.engine.RhinoEngine} the current RhinoEngine instance
 */
function getRhinoEngine() {
    return engine.RhinoEngine.getEngine(global);
}

/**
 * Get a list containing the syntax errors encountered in the current context.
 * @returns {ScriptableList} a list containing the errors encountered in the current context
 */
function getErrors() {
    return new ScriptableList(getRhinoEngine().getCurrentErrors());
}

/**
 * Get the app's module search path as list of repositories.
 * @returns {ScriptableList} a list containing the module search path repositories
 */
function getRepositories() {
    return new ScriptableList(getRhinoEngine().getRepositories());
}

/**
 * Add a repository to the module search path
 * @param {Repository} repo a repository
 */
function addRepository(repo) {
    if (typeof repo == "string") {
        repo = new org.ringojs.repository.FileRepository(repo);
    }
    var path = getRepositories();
    if (repo.exists() && !path.contains(repo)) {
        path.add(Math.max(0, path.length) - 1, repo);
    }
}

