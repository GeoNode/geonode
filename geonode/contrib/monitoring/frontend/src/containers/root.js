/* eslint global-require: 0 */
if (process.env.NODE_ENV === 'production') {
  module.exports = require('./root.prod');
} else {
  module.exports = require('./root.dev');
}
