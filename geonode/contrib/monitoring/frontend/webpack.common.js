const path = require('path');
const precss = require('precss');
const autoprefixer = require('autoprefixer');


module.exports = {
  entry: ['./src/index'],
  output: {
    path: path.join(__dirname, '../static/monitoring'),
    filename: 'bundle.js',
    publicPath: '/static/monitoring/',
  },
  resolveLoader: {
    fallback: path.join(__dirname, 'node_modules'),
  },
  module: {
    preLoaders: [{
      test: /\.js$/,
      loader: 'eslint-loader',
      exclude: /node_modules/,
    }],
    loaders: [
      {
        test: /\.js$/,
        loaders: ['babel'],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.json$/,
        loaders: ['json'],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.csv$/,
        loaders: ['csv-loader'],
        options: {
          dynamicTyping: true,
          header: true,
          skipEmptyLines: true,
        },
      },
      {
        test: /\.geojson$/,
        loaders: ['json'],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.css$/,
        loaders: [
          'style?sourceMap',
          'css?sourceMap&modules&importLoaders=1',
          'resolve-url',
          'postcss',
        ],
      },
      {
        test: /\.(jpe?g|png|gif|svg)$/i,
        loaders: [
          'file?hash=sha512&digest=hex&name=[hash].[ext]',
          'image-webpack?bypassOnDebug&optimizationLevel=7&interlaced=false',
        ],
      },
      {
        test: /\.(png|woff(2)?|eot|ttf|)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'base64-font-loader',
      },
    ],
  },
  postcss() {
    return [precss, autoprefixer];
  },
};
