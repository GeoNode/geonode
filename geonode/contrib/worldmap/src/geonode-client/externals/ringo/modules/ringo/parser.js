/**
 * @fileoverview This module provides an interface to the Rhino parser.
 */

export("Token",
       "Parser",
       "isName",
       "getName",
       "getTypeName");

/**
 * Create a new Parser object. The constructor must be called with the `new` keyword.
 * It takes an `options` argument which may contain the following properties:
 *
 *  - `languageVersion` (number) the JavaScript language version to use.
 *     Defaults to `180`.
 *  - `parseComments` (boolean) whether to attach jsdoc-style comments to parsed nodes.
 *     Defaults to `false`.
 * 
 * @param {Object} options the parser options
 */
function Parser(options) {

    options = options || {};

    /**
     * Parse a script resource and return its AST tree.
     * @param {Resource|String} script a string or org.ringojs.repository.Resource object representing
     *     the script.
     * @param {string} [encoding] optional encoding to use, defaults to UTF-8
     * @return {AstNode} the root node of the AST tree, an instance of org.mozilla.javascript.ast.AstRoot
     */
    this.parse = function(script, encoding) {
        var name = "<script>";
        if (script instanceof org.ringojs.repository.Resource) {
            name =  script.getPath();
            script = script.getReader(encoding || "utf-8");
        }
        return getParser().parse(script, name, 0);
    };

    /**
     * Parse a script resource and apply the visitor function to its AST tree.
     * The function takes one argument which is a org.mozilla.javascript.ast.AstNode.
     * The function must return true to visit child nodes of the current node.
     * @param {Resource|String} script a string or org.ringojs.repository.Resource object representing
     *     the script.
     * @param {Function} visitorFunction the visitor function
     * @param {string} [encoding] optional encoding to use, defaults to UTF-8
     */
    this.visit = function(script, visitorFunction, encoding) {
        var name = "<script>";
        if (script instanceof org.ringojs.repository.Resource) {
            name =  script.getPath();
            script = script.getReader(encoding || "utf-8");
        }
        var ast = getParser().parse(script, name, 0);
        ast.visit(new org.mozilla.javascript.ast.NodeVisitor({
            visit: visitorFunction
        }));
    };

    function getParser() {
        var ce = new org.mozilla.javascript.CompilerEnvirons();
        if (options.parseComments) {
            ce.setRecordingComments(true);
            ce.setRecordingLocalJsDocComments(true);
        }
        ce.initFromContext(org.mozilla.javascript.Context.getCurrentContext());
        if (options.languageVersion) {
            ce.setLanguageVersion(options.languageVersion);
        }
        return new org.mozilla.javascript.Parser(ce, ce.getErrorReporter());
    }


}

/**
 * The org.mozilla.javascript.Token class. This can be used to  easily check
 * find out the types of AST nodes:
 *
 *     node.type == Token.NAME
 */
var Token = org.mozilla.javascript.Token;

/**
 * Utility function to test whether a node is a `NAME` node
 * (a node of type org.mozilla.javascript.ast.Name)
 * @param {Object} node an AST node
 * @returns {Boolean} true if node is a name node
 */
function isName(node) {
    return node instanceof org.mozilla.javascript.ast.Name;
}

/**
 * Utility function to get the name value of a node, or the empty
 * string if it is not a `NAME` node.
 * @param {AstNode} node an AST node
 * @returns {String} the name value of the node
 */
function getName(node) {
    return isName(node) ? node.getString() : "";
}

/**
 * Get the type name of the token as string such as "CALL" or "NAME".
 * @param {AstNode} node a AST node
 * @returns {String} the name of the AST node's type
 */
function getTypeName(node) {
    return node ? Token.typeToName(node.getType()) : "" ;
}



