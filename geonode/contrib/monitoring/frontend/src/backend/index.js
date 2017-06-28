let backend;

if (process.env.NODE_ENV === 'production') {
  backend = require('./prod.js');
} else {
  backend = require('./dev.js');
}


export default backend.default;
