var webpackConfig = require('./webpack.config.js');
var path = require("path");
var LoaderOptionsPlugin = require("webpack/lib/LoaderOptionsPlugin");
var ParallelUglifyPlugin = require("webpack-parallel-uglify-plugin");
var DefinePlugin = require("webpack/lib/DefinePlugin");
var OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var NormalModuleReplacementPlugin = require("webpack/lib/NormalModuleReplacementPlugin");
const extractThemesPlugin = require('./MapStore2/themes.js').extractThemesPlugin;

webpackConfig.plugins = [
    new LoaderOptionsPlugin({
        debug: false,
        options: {
            postcss: {
                plugins: [
                  require('postcss-prefix-selector')({prefix: '.drc', exclude: ['.drc']})
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
    new NormalModuleReplacementPlugin(/leaflet$/, path.join(__dirname, "MapStore2", "web", "client", "libs", "leaflet")),
    new NormalModuleReplacementPlugin(/openlayers$/, path.join(__dirname, "MapStore2", "web", "client", "libs", "openlayers")),
    new NormalModuleReplacementPlugin(/cesium$/, path.join(__dirname, "MapStore2", "web", "client", "libs", "cesium")),
    new NormalModuleReplacementPlugin(/proj4$/, path.join(__dirname, "MapStore2", "web", "client", "libs", "proj4")),
    new NormalModuleReplacementPlugin(/map\/leaflet\/Feature/, path.join(__dirname, "js", "ms2Override", "LeafletFeature.jsx")),
    new NormalModuleReplacementPlugin(/reducers\/map$/, path.join(__dirname, "js", "ms2Override", "mapreducer.js")),
    new NormalModuleReplacementPlugin(/client\/selectors\/layer/, path.join(__dirname, "js", "ms2Override", "layersSelector.js")),
    new NormalModuleReplacementPlugin(/map\/leaflet\/snapshot\/GrabMap/, path.join(__dirname, "js", "ms2Override", "LGrabMap.jsx")),
    new ParallelUglifyPlugin({
        uglifyJS: {
            sourceMap: false,
            compress: {warnings: false},
            mangle: true
        }
    }),
    extractThemesPlugin,
    new OptimizeCssAssetsPlugin({
        cssProcessorOptions: { discardComments: { removeAll: true } }
      })
];
webpackConfig.devtool = undefined;

// this is a workaround for this issue https://github.com/webpack/file-loader/issues/3
// use `__webpack_public_path__` in the index.html when fixed
webpackConfig.output.publicPath = "/static/js";

module.exports = webpackConfig;
