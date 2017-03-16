const merge = require('webpack-merge')
const devWebpackConfig = require('./webpack.dev.conf')
const HtmlWebpackPlugin = require('html-webpack-plugin')

const playConfig = merge(devWebpackConfig, {
  entry: {
    app: './src/play/app.js',
    preview: './src/play/preview.js',
  },
  plugins: [
    new HtmlWebpackPlugin({
      filename: 'index.html',
      template: 'index.html',
      chunks: ['app'],
    }),
    new HtmlWebpackPlugin({
      filename: 'preview.html',
      template: 'index.html',
      chunks: ['preview'],
    }),
  ],
})

Object.keys(playConfig.entry).forEach((name) => {
  playConfig.entry[name] = ['./build/dev-client'].concat(playConfig.entry[name])
})

module.exports = playConfig