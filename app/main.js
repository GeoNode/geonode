#!/usr/bin/env ringo

// main script to start application
// when run from the command line, assume debug mode (scripts not compressed)
if (require.main == module) {
    java.lang.System.setProperty("READYGXP_DEBUG", 1);
    require("ringo/webapp").main(module.directory);
}
