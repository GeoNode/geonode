#!/usr/bin/env ringo
/**
 * @fileoverview Script to create static JsDoc documentation.
 *      Use -h or --help to get a list of available options.
 *
 * @see http://code.google.com/p/jsdoc-toolkit/
 */

// stdlib
var files = require('ringo/utils/files');
var fs = require('fs');
var {Parser} = require('ringo/args');
var {ScriptRepository} = require('ringo/jsdoc');
var strings = require('ringo/utils/strings');
var objects = require('ringo/utils/objects');
var markdown = require('ringo/markdown');
var mustache = require('ringo/mustache');

var {repositoryList, moduleDoc, moduleList, structureModuleDoc, getRepositoryName}
        = require('./jsdocserializer');
var defaultContext = {};
var templates = {
        module: getResource('./templates/module.html').content,
        repository: getResource('./templates/repository.html').content,
        menu: getResource('./templates/menu.html').content,
        head: getResource('./templates/head.html').content,
        page: getResource('./templates/page.html').content,
        index: getResource('./templates/index_all.html').content
    };

/**
 * Renders jsdoc html files for the given repository into the given directory.
 *
 * @param {Object} repository
 * @param {String} directory
 * @param {Boolean} quiet
 */
var renderRepository = exports.renderRepository = function (repository, directory, quiet) {
    // need apps/jsdoc on path for skin extend to work
    if (require.paths.indexOf(module.directory) == -1) {
        require.paths.push(module.directory);
    }

    if (!quiet) print ('Writing to ' + directory + '...');
    copyStaticFiles(directory);
    if (!quiet) print ('Module index');
    writeRepositoryIndex(directory, repository);
    if (!quiet) print(repository.path);
    writeModuleList(directory, repository);
    moduleList(repository).forEach(function(module) {
        if (!quiet) print('\t' + module.name);
        writeModuleDoc(directory, repository, module);
    });

    if (!quiet) print('Finished writing to ' + directory);
    return;
}

/**
 * Copy static files of this webapp to target directory
 *
 * @param {String} directory
 */
function copyStaticFiles(directory) {
    fs.makeTree(fs.join(directory, 'static'));
    fs.copyTree(fs.join(module.directory, 'static'), fs.join(directory, 'static'));
}

/**
 * Write the html file listing all modules to directory.
 *
 * @param {String} directory directory of html file to be written
 * @param {Object} repository repository descriptor
 */
function writeModuleList(directory, repository) {
    var context = objects.merge(defaultContext, {
        repositoryName: repository.name,
        title: 'Module overview - ' + repository.name,
        modules: moduleList(repository, true),
        rootPath: './',
        markdown: function(text) {
            return markdown.process(text);
        }
    });

    context.head = mustache.to_html(templates.head, context);
    context.menu = mustache.to_html(templates.menu, context);
    context.content = mustache.to_html(templates.repository, context);
    var repositoryHtml = mustache.to_html(templates.page, context);
    fs.write(fs.join(directory, 'index.html'), repositoryHtml);
}

/**
 * Write html page documenting one module to the directory.
 *
 * @param {String} directory
 * @param {Object} repository repository descriptor
 * @param {Object} module module descriptor
 */
function writeModuleDoc(directory, repository, module){

    var moduleDirectory = directory;
    var modules = [];
    moduleDirectory = fs.join(directory, module.id);
    fs.makeTree(moduleDirectory);
    modules = moduleList(repository);

    var slashCount = strings.count(module.id, '/');
    var relativeRoot = '../' + strings.repeat('../', slashCount);

    function toLink(target) {
        // if link target roughly matches "foo/bar#xxx.yyy"
        // format as API reference link
        if (target.match(/^[\w\/\.#]+$/)) {
            var [module, hash] = target.split("#");
            if (!module) {
                return [target, target.slice(1)];
            } else {
                var href = relativeRoot + module + "/" + defaultContext.indexhtml;
                if (hash) href += "#" + hash;
                return [href, target.replace("#", ".")];
            }
        }
        return null;
    }

    var docs = moduleDoc(repository.path, module, toLink);
    if (docs == null) {
        throw new Error('Could not parse JsDoc for ' + repository.path + module.id);
    }

    var context = objects.merge(defaultContext, {
        rootPath: relativeRoot,
        repositoryName: repository.name,
        title: module.name + ' - ' + repository.name,
        moduleId: module.id,
        modules: modules,
        item: structureModuleDoc(docs),
        paramList: function() {
            return this.parameters.map(function(p) p.name).join(', ')
        },
        markdown: function(text) {
            return markdown.process(text, {getLink: toLink});
        },
        iterate: function(value) {
            return value && value.length ? {each: value} : null;
        },
        debug: function(value) {
            print(value.toSource());
            return null;
        },
        commaList: function(value) {
            return value && value.length ? value.join(', ') : '';
        },
        newlineList: function(value) {
            return value && value.length ? value.join('<br />') : '';
        }
    });
    context.head = mustache.to_html(templates.head, context);
    context.menu = mustache.to_html(templates.menu, context);
    context.content = mustache.to_html(templates.module, context);
    var moduleHtml = mustache.to_html(templates.page, context);
    var moduleFile = fs.join(moduleDirectory, 'index.html');
    fs.write(moduleFile, moduleHtml);
}

function writeRepositoryIndex(directory, repository) {
    var modules = moduleList(repository).map(function(module) {
        module.data = structureModuleDoc(moduleDoc(repository.path, module));
        module.moduleName = module.name;
        return module;
    });
    var context = objects.merge(defaultContext, {
        rootPath: './',
        repositoryName: repository.name,
        title: 'Index: ' + repository.name,
        modules: modules,
        paramTypeList: function(value) {
            return value && value.length ? [p.type for each (p in value)].join(', ') : '';
        },
        limit: function(value) {
            return value ? value.substr(0, 100) + '...' : '';
        }
    });
    context.head = mustache.to_html(templates.head, context);
    context.menu = mustache.to_html(templates.menu, context);
    context.content = mustache.to_html(templates.index, context);
    var indexHtml = mustache.to_html(templates.page, context);
    var indexFile = fs.join(directory, 'index_all.html');
    fs.write(indexFile, indexHtml);
}

/**
 * Create static documentation for a Repository.
 *
 *   ringo-doc -s /home/foo/ringojs/modules/
 *
 * You can specify a human readable name for the module which will
 * be display in the documentation:
 *
 *   ringo-doc -s /home/foo/ringojs/modules -n "Ringojs Modules"
 *
 * @param args
 */
function main(args) {

    /**
     * Print script help
     */
    function help() {
        print('Create JsDoc documentation for CommonJs modules.');
        print('Usage:');
        print('  ringo ' + script + ' -s [sourcepath]');
        print('Options:');
        print(parser.help());
    }

    var script = args.shift();
    var parser = new Parser();
    parser.addOption('s', 'source', 'repository', 'Path to repository');
    parser.addOption('d', 'directory', 'directory', 'Directory for output files (default: "out")');
    parser.addOption('t', 'template', 'file', 'Master template to use');
    parser.addOption('n', 'name', 'name', 'Name of the Repository (default: auto generated from path)');
    parser.addOption('q', 'quiet', null, 'Do not output any messages.');
    parser.addOption('p', 'package', 'package.json', 'Use package manifest to adjust module names.')
    parser.addOption(null, 'file-urls', null, 'Add "index.html" to all URLs for file:// serving.');
    parser.addOption('h', 'help', null, 'Print help message and exit');

    var opts = parser.parse(args);
    if (opts.help) {
        help();
        return;
    }
    if (!opts.source) {
        throw new Error('No source specified.');
    }
    if (opts.template) {
        var t = getResource(opts.template);
        if (!t.exists()) {
            throw new Error('Template "' + opts.template + '" not found.');
        }
        templates.page = t.content;
    }

    if (opts.package) {
        // read package.json manifest
        var packageJson = fs.absolute(opts.package);
        var pkg = opts.package = require(packageJson);
        if (pkg.main) {
            // make main module absolute
            pkg.main = fs.absolute(fs.join(fs.directory(packageJson), pkg.main))
        }
    }

    var directory = fs.join(opts.directory || './out/');
    var repository = {
        path: opts.source,
        name: opts.name || getRepositoryName(opts.source),
        package: opts.package || {}
    };
    var quiet = opts.quiet || false;
    defaultContext.indexhtml = opts['fileUrls'] ? 'index.html' : '';

    // check if export dir exists & is empty
    var dest = new fs.Path(directory);
    if (dest.exists() && !dest.isDirectory()) {
        throw new Error(dest + ' exists but is not a directory.');
    } else if (dest.isDirectory() && dest.list().length > 0) {
        throw new Error('Directory ' + dest + ' exists but is not empty');
    }

    if (!fs.isDirectory(repository.path)) {
        throw new Error('Invalid source specified. Must be directory.');
    }

    renderRepository(repository, directory, quiet);
}

if (require.main == module) {
    try {
        main(system.args);
    } catch (error) {
        print(error);
        print('Use -h or --help to get a list of available options.');
    }
}
