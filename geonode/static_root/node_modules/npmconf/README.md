# npmconf

## THIS PACKAGE IS DEPRECATED

**This package's functionality has been reintegrated directly into npm. There
have been many changes made to npm's configuration since the last version of
this package was published. It should not be considered a source of truth for
npm configuration any longer, and npm itself is the best tool to use to manage
its configuration.

# **_Do not use this package._**

If you are writing a new Node.js program, and want
configuration functionality similar to what npm has, but for your
own thing, then I'd recommend using [rc](https://github.com/dominictarr/rc),
which is probably what you want.

## USAGE

```javascript
var npmconf = require('npmconf')

// pass in the cli options that you read from the cli
// or whatever top-level configs you want npm to use for now.
npmconf.load({some:'configs'}, function (er, conf) {
  // do stuff with conf
  conf.get('some', 'cli') // 'configs'
  conf.get('username') // 'joebobwhatevers'
  conf.set('foo', 'bar', 'user')
  conf.save('user', function (er) {
    // foo = bar is now saved to ~/.npmrc or wherever
  })
})
```
