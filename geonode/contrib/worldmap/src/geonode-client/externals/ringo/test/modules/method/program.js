var test = require('test');
var a = require('a');
var foo = a.foo;
test.assert(a.foo() == a, 'calling a module member');
test.assert(foo() != a, 'members not implicitly bound');
a.set(10);
test.assert(a.get() == 10, 'get and set')
sys.print('DONE', 'info');
