/*jshint esversion: 6 */

module.exports = function(grunt) {
  /* include the dependency definitions */
  let fileHandling = grunt.file.readJSON('static_dependencies.json');

  /* rewirte the path from node_modules to lib/ */
  let assetsMinifiedJs = fileHandling["assets.min.js"].map (
    fileSegment => 'lib/js/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );
  let leafletPluginsMinifiedJs = fileHandling["leaflet-plugins.min.js"].map (
    fileSegment => 'lib/js/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );
  let assetsMinifiedCss = fileHandling["assets.min.css"].map (
    fileSegment => 'lib/css/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );
  let leafletMinifiedCss = fileHandling["leaflet.plugins.min.css"].map (
    fileSegment => 'lib/css/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    jshint: {
      // files to lint
      files: ['gruntfile.js'],
      // configure JSHint (see http://www.jshint.com/docs/)
      options: {
        globals: {
          jQuery: true,
          console: true,
          module: true
        }
      }
    },

    clean: {
      lib: ['lib/']
    },

    less: {
      development: {
        options: {
          paths: [
            'geonode/less'
          ]
        },
        files: [
          {
            'geonode/css/base.css': 'geonode/less/base.less'
          }
        ]
      },
      production: {
        options: {
          paths: [
            'geonode/less',
            'node_modules/bootstrap/less'
          ],
          yuicompress: true
        },
        files: [
          {
            'geonode/css/base.css': 'geonode/less/base.less'
          }
        ]
      }
    },

    concat: {
      bootstrap: {
          files: [{
            expand: true,
            flatten: true,
            cwd: 'node_modules',
            dest: 'lib/js',
            src: fileHandling.concatBootstrap
        }]
      }
    },

    copy: {
      default: {
        files: [{
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/css',
          src: [fileHandling["assets.min.css"], fileHandling["leaflet.plugins.min.css"]]
        }, {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/img',
          src: fileHandling.images
        }, {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/js',
          src: [fileHandling["assets.min.js"], fileHandling.other_dependencies, fileHandling["leaflet-plugins.min.js"]]
        }]
      }
    },

    replace: {
      default: {
        src: ['lib/css/*.css'],
        overwrite: true,
        /*
         * We separate each pattern so it will be easy for us to read
         * and recognize
         */
        replacements: [
          /*
           * Pattern:
           * url('img/image _.png') or url("img/image _.png")
           */
          {
            from: /url\([\"\']?(img\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$2")'
          },
          /*
           * Pattern:
           * url('images/image _.png') or url("images/image _.png")
           */
          {
            from: /url\([\"\']?(images\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$2")'
          },
          /*
           * Pattern:
           * url('image/image _.png') or url("image/image _.png")
           */
          {
            from: /url\([\"\']?(image\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$2")'
          },
          /*
           * Pattern:
           * url('./image _.png') or url("./image _.png")
           */
          /*{
            from: /url\([\"\']?(\.\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$2")'
          },*/
          /*
           * Pattern:
           * url('image _.png') or url("image _.png")
           */
          /*{
            from: /url\([\"\']?([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$1")'
          },*/
          /*
           * Pattern:
           * url('../images/image _.png') or url("../images/image _.png")
           */
          {
            from: /url\([\"\']?(\.\.\/images\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$1")'
          },
          /*
           * Pattern:
           * url('../image/image _.png') or url("../image/image _.png")
           */
          {
            from: /url\([\"\']?(\.\.\/image\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$1")'
          }
        ]
      }
    },

    cssmin: {
      default: {
        options: {
          // the banner is inserted at the top of the output
          banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n',
          cwd: 'l'
        },
        files: {
          'lib/css/assets.min.css': assetsMinifiedCss,
          'lib/css/leaflet-plugins.min.css': leafletMinifiedCss
        }
      }
    },

    uglify: {
      options: {
        // the banner is inserted at the top of the output
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      development: {
        options: {
          beautify: true,
          compress: false,
          mangle: false
        },
        files: {
          'lib/js/assets.min.js': assetsMinifiedJs,
          'lib/js/leaflet-plugins.min.js': leafletPluginsMinifiedJs
        }
      },
      production: {
        options: {
          beautify: false,
          compress: true,
          mangle: false
        },
        files: {
          'lib/js/assets.min.js': assetsMinifiedJs,
          'lib/js/leaflet-plugins.min.js': leafletPluginsMinifiedJs
        }
      }
    },

    // automated build on file change during development
    watch: {
      less: {
        files: ['geonode/less/*.less'],
        tasks: ['less:development']
      }
    }
  });

  // Load libs
  require('load-grunt-tasks')(grunt);

  // test
  grunt.registerTask('test', ['jshint']);

  // build development
  grunt.registerTask('development', ['jshint', 'clean:lib', 'less:development', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:development']);

  // build production
  grunt.registerTask('production', ['jshint', 'clean:lib', 'less:production', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:production']);

};
