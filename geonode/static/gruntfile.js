module.exports = function(grunt) {

  'use strict';

  grunt.initConfig({

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
            'lib/css/bootstrap.css': ['.components/bootstrap/less/bootstrap.less', '.components/bootstrap/less/responsive.less'],
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
            'lib/css/bootstrap.css': ['.components/bootstrap/less/bootstrap.less', '.components/bootstrap/less/responsive.less'],
            'geonode/css/base.css': 'geonode/less/base.less'
          }
        ]
      }
    },

    concat: {
      options: {
        // define a string to put between each file in the concatenated output
        separator: ';'
      },
      development: {
        files: {
          'lib/js/bootstrap.js': '.components/bootstrap/js/*.js'
        }
      },
      production: {
        files: [
          { 'lib/js/bootstrap.js': ['.components/bootstrap/js/*.js']},
          { 'lib/css/assets.css': ['lib/css/*.css'] }
        ]
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

    uglify: {
      options: {
        // the banner is inserted at the top of the output
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          'lib/js/assets.min.js': ['lib/js/*.js']
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

  // test
  grunt.registerTask('test', ['jshint']);

  // build development
  grunt.registerTask('default', ['jshint', 'less:development', 'concat:development', 'copy']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:production', 'copy', 'uglify']);

};