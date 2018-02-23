var test = require('test');
test.assert(require('a/b/c/d').foo() == 1, 'nested module identifier');
sys.print('DONE', 'info');
