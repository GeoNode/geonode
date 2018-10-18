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
    modules: ["web_loaders", "web_modules", "node_loaders", "node_modules"],
  },
  module: {
    rules: [{
        test: /\.js$/,
        use: ['babel-loader', 'eslint-loader'],
        enforce: 'pre',
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.js$/,
        loaders: ['babel-loader'],
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
        loaders: [
          'csv-loader?dynamicTyping=true&header=true&skipEmptyLines=true'
        ],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
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
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.(jpe?g|png|gif|woff|woff2|eot|ttf|svg)$/i,
        loaders: [
          'file-loader?hash=sha512&digest=hex&name=[hash].[ext]',
          'image-webpack-loader?bypassOnDebug&optimizationLevel=7&interlaced=false',
        ],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
      {
        test: /\.(png|woff(2)?|eot|ttf|)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loaders: ['base64-font-loader'],
        exclude: /node_modules/,
        include: path.join(__dirname, 'src'),
      },
    ],
  },
};
