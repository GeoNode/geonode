/**
 * @fileoverview <p>This module provides access to the Google Closure Compiler.
 */
var jar = module.resolve("../../jars/compiler.jar");
addToClasspath(jar);


var google = Packages.com.google;
var jscomp = google.javascript.jscomp;
var ImmutableList = google.common.collect.ImmutableList;

// assert that the compiler is available
if (typeof jscomp.Compiler !== "function") {
    throw "com.google.javascript.jscomp.Compiler is not available in " + jar;
}


var levels = {
    whitespace: jscomp.CompilationLevel.WHITESPACE_ONLY,
    simple: jscomp.CompilationLevel.SIMPLE_OPTIMIZATIONS,
    advanced: jscomp.CompilationLevel.ADVANCED_OPTIMIZATIONS
};

var warnings = {
    quiet: jscomp.WarningLevel.QUIET,
    "default": jscomp.WarningLevel.DEFAULT,
    verbose: jscomp.WarningLevel.VERBOSE
};

/**
 * Constructor for creating JavaScript compilers.
 *
 * #### Compiler configuration properties
 *
 *  The **config** object may contain the following properties:
 *  - `String` **level**: The compilation level.  One of "whitespace", 
 *     "simple", or "advanced".  Default is "simple".
 *  - `String` **warnings**: The warning level.  One of "quiet", "default", or 
 *     "verbose".  Default is "default".
 *  - `Boolean` **debug**: Run compiler in debug mode.
 *
 * @param {Object} config Compiler configuration properties
 */
var Compiler = exports.Compiler = function(config) {
    config = config || {};
    
    // TODO: deal with logging level
    jscomp.Compiler.setLoggingLevel(java.util.logging.Level.WARNING);

    // TODO: deal with error stream
    var compiler = new jscomp.Compiler();
    
    // assemble compiler options
    var options = new jscomp.CompilerOptions();
    options.setCodingConvention(new jscomp.ClosureCodingConvention());

    // set compilation level
    var level = levels[config.level] || levels.simple;
    level.setOptionsForCompilationLevel(options);

    if (config.debug) {
        level.setDebugOptionsForCompilationLevel(options);
    }
    
    var warningLevel = warnings[config.warnings] || warnings["default"];
    warningLevel.setOptionsForWarningLevel(options);

    // TODO: handle formatting options
    // TODO: handle closure primitives    
    // TODO: deal with run options
    // TODO: deal with output options
    // TODO: deal with modules
    
    /**
     * Minifies JavaScript source code.
     * 
     * #### Compilation configuration properties
     *
     *  The **config** object may contain the following properties:
     *  - `String` **code**: Source code string (required).
     *  - `String` **externs**: Code containing externs declarations.  Relevant
     *     with "advanced" level compilation only.
     *
     * @param {Object|String} config Compilation configuration properties.
     *     Alternatively, a JavaScript source string may be provided to compile
     *     with all the default options.
     * @returns {String} Minified code
     */
    this.compile = function(config) {
        if (typeof config === "string") {
            config = {code: config};
        }
        
        if (!config.code) {
            throw new Error("Compile must be called with source code string.");
        }

        // TODO: accept list of externs files
        var externs = ImmutableList.of(
            jscomp.JSSourceFile.fromCode("externs.js", config.externs || "")
        );

        // TODO: accept list of input files
        var inputs = ImmutableList.of(
            jscomp.JSSourceFile.fromCode("input.js", config.code)
        );

        var result = compiler.compile(externs, inputs, options);
        if (!result.success) {
            throw new Error("Unable to compile source.");
        }
        
        return compiler.toSource();
    }
    
}

/**
 * Minifies JavaScript source code.
 *
 * #### Compilation configuration properties
 *
 *  The **config** object may contain any of the properties accepted by the
 *  [Compiler](#Compiler) constructor or the [compile](#Compiler.prototype.compile)
 *  instance method.
 *
 * @param {Object|String} config Compilation configuration properties.
 *     Alternatively, a JavaScript source string may be provided to compile
 *     with all the default options.
 * @returns {String} Minified code
 */
var compile = exports.compile = function(config) {
    if (typeof config === "string") {
        config = {code: config};
    }
    var compiler = new Compiler(config);
    return compiler.compile(config.code);
}
