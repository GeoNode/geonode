var test = require('test');
test.assert(require('a').foo() == 1, 'transitive');
sys.print('DONE', 'info');
