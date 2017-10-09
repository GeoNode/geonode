// query parser module
if (typeof turbo === "undefined") turbo={};
turbo.query = function() {
  var statements = {};

  var parser = {};

  parser.parse = function(query, shortcuts, callback, _found_statements) {
    // 1. get list of overpass turbo statements
    statements = {};
    if (_found_statements) statements = _found_statements;
    var statement = /{{([A-Za-z0-9_]+):([\s\S]*?)}}/;
    var s;
    while (s = query.match(statement)) {
      var s_name = s[1];
      var s_instr = s[2];
      var s_replace = "";
      // save instructions for later
      if (statements[s_name] === undefined) statements[s_name] = "";
      statements[s_name] += s_instr;
      // if the statement is a shortcut, replace its content
      if (shortcuts[s_name] !== undefined) {
        // these shortcuts can also be callback functions, like {{date:-1day}}
        if (typeof shortcuts[s_name] === "function") {
          shortcuts[s_name](s_instr, function(res) {
            var seed = Math.round(Math.random()*Math.pow(2,22)); // todo: use some kind of checksum of s_instr if possible
            shortcuts["__statement__"+s_name+"__"+seed] = res;
            query = query.replace("{{"+s_name+":"+s_instr+"}}", "{{__statement__"+s_name+"__"+seed+":"+s_instr+"}}");
            // recursively call the parser with updated shortcuts
            parser.parse(query, shortcuts, callback, statements);
          });
          return;
        } else
          s_replace = shortcuts[s_name];
      }
      // remove statement, but preserve number of newlines
      var lc = s_instr.split(/\r?\n|\r/).length;
      query = query.replace("{{"+s_name+":"+s_instr+"}}", s_replace+Array(lc).join('\n'));
    }
    // 2. get user defined constants
    var constants = {};
    var constant = /{{([A-Za-z0-9_]+)=(.+?)}}/;
    var c;
    while (c = query.match(constant)) {
      var c_name = c[1];
      var c_val = c[2];
      constants[c_name] = c_val;
      // remove constant definitions
      query = query.replace(constant, '');
    }
    // 3. expand shortcuts (global and user defined)
    _.extend(constants, shortcuts, function(a,b) { return (typeof a == 'undefined') ? b : a; });
    for (var c_name in constants) {
      var c_val = constants[c_name];
      query = query.replace(new RegExp('{{'+c_name+'}}','g'), c_val);
    }
    // 4. remove remaining (e.g. unknown) mustache templates:
    var m;
    while (m = query.match(/{{[\S\s]*?}}/gm)) {
      // count lines in template and replace mustache with same number of newlines 
      var lc = m[0].split(/\r?\n|\r/).length;
      query = query.replace(m[0], Array(lc).join("\n"));
    };
    // return the query
    callback(query);
  };

  parser.hasStatement = function(statement) {
    return statements.hasOwnProperty(statement);
  };

  parser.getStatement = function(statement) {
    return statements[statement];
  };

  return parser;
};