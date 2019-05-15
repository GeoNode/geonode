var webpackConfig = require('./webpack.config.js');
var assign = require('object-assign');

assign(webpackConfig.entry, require('./examples.js'));

module.exports = webpackConfig;
