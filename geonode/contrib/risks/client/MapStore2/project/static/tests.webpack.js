var context = require.context('./js', true, /-test\.jsx?$/);
context.keys().forEach(context);
module.exports = context;
