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
  let openlayersPluginsMinifiedJs = fileHandling["openlayers-plugins.min.js"].map(
    fileSegment => 'lib/js/' + fileSegment.substring(fileSegment.lastIndexOf('/') + 1)
  );
  let assetsMinifiedCss = fileHandling["assets.min.css"].map (
    fileSegment => 'lib/css/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );
  let leafletMinifiedCss = fileHandling["leaflet.plugins.min.css"].map (
    fileSegment => 'lib/css/' + fileSegment.substring(fileSegment.lastIndexOf('/')+1)
  );
  let openlayersMinifiedCss = fileHandling["openlayers.plugins.min.css"].map(
    fileSegment => 'lib/css/' + fileSegment.substring(fileSegment.lastIndexOf('/') + 1)
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
            'geonode/css/base.css': 'geonode/less/base.less',
            'geonode/css/crop_widget.css': 'geonode/less/crop_widget.less',
            'geonode/css/geonode-rtl.css': 'geonode/less/geonode-rtl.less'
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
            'geonode/css/base.css': 'geonode/less/base.less',
            'geonode/css/crop_widget.css': 'geonode/less/crop_widget.less',
            'geonode/css/geonode-rtl.css': 'geonode/less/geonode-rtl.less'
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
          src: [fileHandling["assets.min.css"], fileHandling["leaflet.plugins.min.css"], fileHandling["openlayers.plugins.min.css"]]
        }, {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/img',
          src: fileHandling.images
        },
        {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/fonts',
          src: fileHandling.lib_fonts
        },{
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/css/fonts',
          src: fileHandling.lib_css_fonts
        },{
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/css/assets',
          src: fileHandling.lib_css_assets
        }, {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/css',
          src: fileHandling.lib_css_png
        }, {
          expand: true,
          flatten: true,
          nonull: true,
          cwd: 'node_modules',
          dest: 'lib/js',
          src: [fileHandling["assets.min.js"], fileHandling.other_dependencies, fileHandling["leaflet-plugins.min.js"], fileHandling["openlayers-plugins.min.js"]]
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
          'lib/css/leaflet-plugins.min.css': leafletMinifiedCss,
          'lib/css/openlayers-plugins.min.css': openlayersMinifiedCss,
          'geonode/css/geonode-rtl.min.css': ['geonode/css/geonode-rtl.css']
        }
      }
    },

    babel: {
      options: {
          sourceMap: true,
          presets: ['@babel/preset-env']
      },
      dist: {
          files: {
              'geonode/js/crop_widget/crop_widget_es5.js': 'geonode/js/crop_widget/crop_widget.js',
              'geonode/js/messages/message_recipients_autocomplete_es5.js': 'geonode/js/messages/message_recipients_autocomplete.js'
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
          'lib/js/leaflet-plugins.min.js': leafletPluginsMinifiedJs,
          'lib/js/openlayers-plugins.min.js': openlayersPluginsMinifiedJs
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
          'lib/js/leaflet-plugins.min.js': leafletPluginsMinifiedJs,
          'lib/js/openlayers-plugins.min.js': openlayersPluginsMinifiedJs
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
  grunt.registerTask('development', ['jshint', /*'clean:lib',*/ 'less:development', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:development', 'babel']);
  grunt.registerTask('build-less-dev', ['less:development']);
  // build production
  grunt.registerTask('production', ['jshint', /*'clean:lib',*/ 'less:production', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:production', 'babel']);
  grunt.registerTask('build-less-prod', ['less:production']);

};
