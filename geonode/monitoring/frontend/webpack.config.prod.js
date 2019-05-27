const webpack = require('webpack');
const config = require('./webpack.common');


config.plugins = [
  new webpack.DefinePlugin({ 'process.env.NODE_ENV': "'production'" }),
  new webpack.optimize.DedupePlugin(),
  new webpack.optimize.UglifyJsPlugin({
    comments: false,
  }),
  new webpack.optimize.AggressiveMergingPlugin(),
];


module.exports = config;
