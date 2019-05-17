var context = require.context('./web', true, /-test\.jsx?$/);
context.keys().forEach(context);
module.exports = context;
