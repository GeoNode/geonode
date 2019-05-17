var context = require.context('../..', true, /^\.*((\/components)|(\/actions)|(\/reducers))((?!__tests__).)*jsx?$/);
context.keys().forEach(context);
module.exports = context;
