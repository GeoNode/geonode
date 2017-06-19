const webpack = require('webpack');
const config = require('./webpack.common');


config.plugins = [
  new webpack.DefinePlugin({ 'process.env.NODE_ENV': "'dev'" }),
];


config.devtool = 'cheap-module-source-map';


module.exports = config;
