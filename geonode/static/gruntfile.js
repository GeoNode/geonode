module.exports = function(grunt) {

  'use strict';

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

    less: {
      development: {
        options: {
          paths: [
            '.components/bootstrap/less',
            'geonode/less'
          ],
        },
        files: [
          {
            'lib/css/bootstrap.css': ['.components/bootstrap/less/bootstrap.less'],
            'geonode/css/base.css': 'geonode/less/base.less'

          }
        ]
      },
      production: {
        options: {
          paths: ['.components/bootstrap/less'],
          yuicompress: true
        },
        files: [
          {
            'lib/css/bootstrap.css': ['.components/bootstrap/less/bootstrap.less'],
            'geonode/css/base.css': 'geonode/less/base.less'
          }
        ]
      }
    },

    concat: {
      bootstrap_js: {
        files: {
          // TODO: order of concatenated bootstrap scripts seems important
          // TODO: does GeoNode require all of them?
          'lib/js/bootstrap.js': '.components/bootstrap/js/*.js'
        }
      }
    },

    copy: {
      development: {
        files: [{
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/css',
          src: [
            'datatables/media/css/jquery.dataTables.css'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/img',
          src: [
            'bootstrap/img/*.png'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/images',
          src: [
            'datatables/media/images/*.png'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/css',
          src: [
            'select2/*.png', 'select2/select2.css'
          ]
        }, {
          'lib/js/jquery.js': ['.components/jquery/jquery.js']
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/js',
          src: [
            'jquery/jquery.js',
            'datatables/media/js/jquery.dataTables.js',
            'jquery-timeago/jquery.timeago.js',
            'json2/json2.js',
            'select2/select2.js'
          ]
        }]
      }
    },

    cssmin: {
      production: {
        options: {
          // the banner is inserted at the top of the output
          banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
        },
        files: {
          'lib/css/assets.min.css': [
            'lib/css/bootstrap.css', 
            'lib/css/jquery.dataTables.css', 
            'lib/css/select2.css'
          ]
        }
      }
    },

    uglify: {
      options: {
        // the banner is inserted at the top of the output
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      production: {
        files: {
          'lib/js/assets.min.js': [
            'lib/js/jquery.js',
            'lib/js/jquery.timeago.js',
            'lib/js/jquery.dataTables.js',
            'lib/js/json2.js',
            'lib/js/select2.js'
            // TODO: see note in concat command
            // 'lib/js/bootstrap.js',
          ]
        }
      }
    }
  });

  // Load libs
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-cssmin');

  // test
  grunt.registerTask('test', ['jshint']);

  // build development
  grunt.registerTask('default', ['jshint', 'less:development', 'concat:bootstrap_js', 'copy']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:bootstrap_js', 'copy', 'cssmin', 'uglify', ]);

};