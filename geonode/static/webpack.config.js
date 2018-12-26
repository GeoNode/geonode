const ConcatPlugin = require('webpack-concat-plugin');

module.exports = {
    
    context: __dirname,

    //define entry point
    entry: './app.js',

    //define output point
    output: {
        path: `${__dirname}/dist`,
        filename: 'bundle.js'
    },

     module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /(node_modules)/,
                loader: "babel-loader",
                query: {
                  presets: ["@babel/preset-env"],
                  cacheDirectory: true
                }
              },
        ] //loaders
    }, //module

    optimization: {
        minimizer: [
            new ConcatPlugin({
                uglify: true,
                sourceMap: true,
                outputPath: '.',
                fileName: 'assets.min.js',
                filesToConcat: [
                    './node_modules/jquery/dist/jquery.min.js',
                    './node_modules/datatables/media/js/jquery.dataTables.js',
                    './node_modules/timeago/jquery.timeago.js',
                    './node_modules/raty/lib/jquery.raty.js',
                    './node_modules/jquery-waypoints/waypoints.js',
                    './node_modules/jquery-ui/custom.js',
                    './node_modules/jquery-ajaxprogress/jquery.ajaxprogress.js',
                    './node_modules/jquery.ajaxQueue/dist/jquery.ajaxQueue.js',
                    './node_modules/multi-select/js/jquery.multi-select.js',
                    './node_modules/json2/json2.js',
                    './node_modules/select2/select2.js',
                    './node_modules/requirejs/require.js',
                    './node_modules/requirejs-text/text.js',
                    './node_modules/underscore/underscore-min.js',
                    './node_modules/angular/angular.js',
                    './node_modules/angular-cookies/angular-cookies.js',
                    './node_modules/angular-leaflet-directive/dist/angular-leaflet-directive.min.js',
                    './node_modules/bootstrap/dist/js/bootstrap.min.js',
                    './node_modules/zeroclipboard/dist/ZeroClipboard.min.js',
                    './node_modules/leaflet-fullscreen/dist/Leaflet.fullscreen.min.js',
                    './node_modules/leaflet-opacity/lib/opacity/Control.Opacity.js',
                    './node_modules/leaflet-measure/dist/leaflet-measure.js',
                    './node_modules/moment/min/moment-with-locales.min.js',
                    './node_modules/eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
                    './node_modules/bootstrap-treeview/dist/bootstrap-treeview.min.js',
                    './node_modules/bootstrap-tokenfield/dist/bootstrap-tokenfield.min.js',
                    './node_modules/bootstrap-select/dist/js/bootstrap-select.min.js',
                    './node_modules/bootstrap-wysiwyghtml5/dist/bootstrap-wysihtml5-0.0.2.min.js',
                    './node_modules/bootstrap-table/dist/bootstrap-table.min.js',
                    './node_modules/bootstrap-toggle/js/bootstrap-toggle.min.js',
                    './node_modules/fastselect/dist/fastselect.standalone.min.js',
                    './node_modules/clipboard/dist/clipboard.js',
                    './node_modules/leaflet-easybutton/src/easy-button.js'
                ],
                attributes: {
                    async: true
                }
            }),
            new ConcatPlugin({
                uglify: true,
                sourceMap: true,
                outputPath: '.',
                fileName: 'bootstrap.min.js',
                filesToConcat: [
                    'bootstrap/dist/js/bootstrap.js',
                    'bootstrap/js/affix.js',
                    'bootstrap/js/alert.js',
                    'bootstrap/js/button.js',
                    'bootstrap/js/carousel.js',
                    'bootstrap/js/collapse.js',
                    'bootstrap/js/dropdown.js',
                    'bootstrap/js/modal.js',
                    'bootstrap/js/popover.js',
                    'bootstrap/js/scrollspy.js',
                    'bootstrap/js/tab.js',
                    'bootstrap/js/tooltip.js',
                    'bootstrap/js/transition.js'
                ],
                attributes: {
                    async: true
                }
            }),
        ],
      },
};