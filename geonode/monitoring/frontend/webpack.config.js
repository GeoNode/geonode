/*
#########################################################################
#
# Copyright (C) 2019 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
*/

const path = require('path');
const DefinePlugin = require('webpack/lib/DefinePlugin');

const devServerHost = 'ENTER_DEV_HOST_IN_WEBPACK_CONFIG';

module.exports = (env, argv) => {
    const isProduction = argv.mode === 'production';
    return {
        entry: {
            bundle: './src/index.js'
        },
        output: {
            path: path.join(__dirname, '../static/monitoring'),
            publicPath: '/static/monitoring/',
            filename: '[name].js'
        },
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    exclude: /node_modules/,
                    use: [ 'babel-loader' ]
                },
                {
                    test: /\.scss$/,
                    use: [
                        { loader: 'style-loader' },
                        { loader: 'to-string-loader' },
                        { loader: 'css-loader' },
                        { loader: 'sass-loader' }
                    ]
                },
                {
                    test: /\.(png|jpg|gif|svg)$/,
                    use: [{
                        loader: 'url-loader',
                        options: {
                            name: '[path][name].[ext]',
                            limit: 8192
                        }
                    }]
                },
            ]
        },
        resolve: {
            extensions: ['*', '.js', '.jsx']
        },
        plugins: [
            new DefinePlugin({
                '__DEVELOPMENT__': !isProduction,
                '__TRANSLATION_PATH__': isProduction
                    ? "'/static/monitoring/translations/'"
                    : "'/translations/'",
                '__ASSETS_PATH__': isProduction
                    ? "'/static/monitoring/assets/'"
                    : "'/assets/'"
            })
        ],
        devServer: isProduction
            ? undefined
            : {
                port: 3000,
                contentBase: './',
                hot: true,
                proxy: [
                    {
                        context: [
                            '**',
                            '!**/static/monitoring/**',
                            '!**/assets/**',
                            '!**/translations/**'
                        ],
                        target: `http://${devServerHost}/`,
                        secure: false,
                        changeOrigin: true,
                        headers: {
                            host: devServerHost
                        }
                    }
                ]
            },
        devtool: isProduction ? undefined : 'eval'
    }
};
