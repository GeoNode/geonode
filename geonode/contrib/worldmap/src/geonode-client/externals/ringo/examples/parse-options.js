var {Parser} = require('ringo/args');
var {RED, BLUE, YELLOW, BOLD, writeln} = require('ringo/term');

function main(args) {
    var parser = new Parser();
    parser.addOption('f', 'foo', null, 'Enable foo bit');
    parser.addOption('b', 'bar', '[BAR-FACTOR]', 'Specify bar factor');
    parser.addOption('h', 'help', null, 'Display help');
    args.shift();
    var options = parser.parse(args);
    if (options.help) {
        writeln(BLUE, BOLD, 'Options:');
        writeln(BLUE, parser.help());
    } else {
        if (options.foo) {
            writeln(RED, 'Foo:', BOLD, YELLOW, options.foo);
        }
        if (options.bar) {
            writeln(BLUE, 'Bar factor:', BOLD, options.bar);
        }
    }
    if (!Object.keys(options).length) {
        writeln(BOLD, "Run with -h/--help to see available options");
    }
       
}

if (require.main === module) {
    main(system.args);
}
