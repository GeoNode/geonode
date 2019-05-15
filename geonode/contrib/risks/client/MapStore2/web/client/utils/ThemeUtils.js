function LessNodeResolve(options) {
    this.options = options;
}

function NodeProcessor(options) {
    this.options = options || {};
}

NodeProcessor.prototype = {
    process: function(src, extra) {
        const basePath = extra.fileInfo.currentDirectory.replace(this.options.path, '');
        return src.replace(/\"~(.*)\"/g, '"' + basePath + 'dist/$1"');
    }
};

LessNodeResolve.prototype = {
    install: function(less, pluginManager) {
        pluginManager.addPreProcessor(new NodeProcessor(this.options));
    },
    printUsage: function() {
        // TODO
    },
    setOptions: function(options) {
        this.options = options;
    },
    minVersion: [2, 4, 0]
};

const less = require('less');

module.exports = {
    renderFromLess: (theme, container, path, callback) => {
        less.render(theme, {
            plugins: [new LessNodeResolve({path: path})],
            filename: 'custom.theme.less',
            compress: true
        }, (e, output) => {
            document.getElementById(container).innerText = output.css;
            if (callback) {
                callback();
            }
        });
    }
};
