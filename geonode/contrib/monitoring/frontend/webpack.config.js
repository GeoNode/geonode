const webpack = require('webpack');
const config = require('./webpack.common');


config.plugins = [
  new webpack.DefinePlugin({ 'process.env.NODE_ENV': "'dev'" }),
];


config.devtool = 'cheap-module-source-map';


config.devServer = {
  proxy: {
    '/monitoring/api': {
      target: 'http://localhost:8000',
    },
    '/static': {
      target: 'http://localhost:8000',
    },
    '/lang.js': {
      target: 'http://localhost:8000',
    },
  },
};


module.exports = config;
