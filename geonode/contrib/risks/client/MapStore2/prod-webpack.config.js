var webpackConfig = require('./webpack.config.js');
var path = require("path");
var LoaderOptionsPlugin = require("webpack/lib/LoaderOptionsPlugin");
var ParallelUglifyPlugin = require("webpack-parallel-uglify-plugin");
var DefinePlugin = require("webpack/lib/DefinePlugin");
var NormalModuleReplacementPlugin = require("webpack/lib/NormalModuleReplacementPlugin");
const extractThemesPlugin = require('./themes.js').extractThemesPlugin;
var assign = require('object-assign');
var CopyWebpackPlugin = require('copy-webpack-plugin');

assign(webpackConfig.entry, require('./examples.js'));

webpackConfig.plugins = [
    new CopyWebpackPlugin([
        { from: path.join(__dirname, 'node_modules', 'bootstrap', 'less'), to: path.join(__dirname, "web", "client", "dist", "bootstrap", "less") }
    ]),
    new LoaderOptionsPlugin({
        debug: false,
        options: {
            postcss: {
                plugins: [
                  require('postcss-prefix-selector')({prefix: '.ms2', exclude: ['.ms2']})
                ]
            },
            context: __dirname
        }
    }),
    new DefinePlugin({
        "__DEVTOOLS__": false
    }),
    new DefinePlugin({
      'process.env': {
        'NODE_ENV': '"production"'
      }
    }),
    new NormalModuleReplacementPlugin(/leaflet$/, path.join(__dirname, "web", "client", "libs", "leaflet")),
    new NormalModuleReplacementPlugin(/openlayers$/, path.join(__dirname, "web", "client", "libs", "openlayers")),
    new NormalModuleReplacementPlugin(/proj4$/, path.join(__dirname, "web", "client", "libs", "proj4")),
    new ParallelUglifyPlugin({
        uglifyJS: {
            sourceMap: false,
            compress: {warnings: false},
            mangle: true
        }
    }),
    extractThemesPlugin
];
webpackConfig.devtool = undefined;

// this is a workaround for this issue https://github.com/webpack/file-loader/issues/3
// use `__webpack_public_path__` in the index.html when fixed
webpackConfig.output.publicPath = "/mapstore/dist/";

module.exports = webpackConfig;
