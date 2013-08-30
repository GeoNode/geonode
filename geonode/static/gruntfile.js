module.exports = function(grunt) {

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
            'geonode/less'
          ]
        },
        files: [
          {
            // includes bootstrap.css
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
            // includes bootstrap.css
            'geonode/css/base.css': 'geonode/less/base.less'
          }
        ]
      }
    },

    concat: {
      bootstrap: {
        src: [
          '.components/bootstrap/js/bootstrap-affix.js',
          '.components/bootstrap/js/bootstrap-dropdown.js',
          '.components/bootstrap/js/bootstrap-tooltip.js',
          '.components/bootstrap/js/bootstrap-alert.js',
          '.components/bootstrap/js/bootstrap-modal.js',
          '.components/bootstrap/js/bootstrap-transition.js',
          '.components/bootstrap/js/bootstrap-button.js',
          '.components/bootstrap/js/bootstrap-popover.js',
          '.components/bootstrap/js/bootstrap-typeahead.js',
          '.components/bootstrap/js/bootstrap-carousel.js',
          '.components/bootstrap/js/bootstrap-scrollspy.js',
          '.components/bootstrap/js/bootstrap-collapse.js',
          '.components/bootstrap/js/bootstrap-tab.js'
        ],
        dest: 'lib/js/bootstrap.js'
      }
    },

    copy: {
      // TODO: add production version without copying non-min libs
      development: {
        files: [{
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/css',
          src: [
            'datatables/media/css/jquery.dataTables.css',
            'select2/select2.css', 
            'multi-select/css/multi-select.css',
            'qunit/qunit/qunit.css'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/img',
          src: [
            'bootstrap/img/*.png',
            'select2/*.png', 'select2/spinner.gif',
            'raty/img/*.png',
            'multi-select/img/switch.png',
            'datatables/media/images/*.png'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/js',
          src: [
            'jquery/jquery.js',
            'datatables/media/js/jquery.dataTables.js',
            'jquery-timeago/jquery.timeago.js',
            'tinysort/src/jquery.tinysort.js',
            'raty/js/jquery.raty.js',
            'jquery-waypoints/waypoints.js',
            'jquery-ui/ui/jquery-ui.custom.js',
            'jquery-ajaxprogress/jquery.ajaxprogress.js',
            'jquery.ajaxQueue/dist/jquery.ajaxQueue.min.js',
            'multi-select/js/jquery.multi-select.js',
            'bootstrap-datepicker/js/bootstrap-datepicker.js',
            'json2/json2.js',
            'select2/select2.js',
            'requirejs/require.js',
            'requirejs-text/text.js',
            'underscore/underscore.js',
            'qunit/qunit/qunit.js'
          ]
        }]
      }
    },

    // replace image paths in CSS to match lib/img/
    replace: {
      development: {
        src: ['lib/css/*.css'],
        overwrite: true,
        replacements: [{ 
          from: /url\('(?!\.)/g,
          to: 'url(\'../img/'
        }, {
          from: /url\((?!\')/g, 
          to: 'url(\'../img/'
        }, { 
          from: /..\/images\//g,
          to: '../img/'
        }, {
          from: /(png|gif|jpg)(?=\))/g, 
          to: '$1\''
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
            'lib/css/jquery.dataTables.css',
            'lib/css/select2.css',
            'lib/css/multi-select.css'
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
            'lib/js/jquery.dataTables.js',
            'lib/js/jquery.timeago.js',
            'lib/js/jquery.tinysort.js',
            'lib/js/jquery.raty.js',
            'lib/js/waypoints.js',
            'lib/js/jquery-ui.custom.js',
            'lib/js/jquery.ajaxprogress.js',
            'lib/js/jquery.ajaxQueue.min.js',
            'lib/js/jquery.multi-select.js',
            'lib/js/bootstrap-datepicker.js',
            'lib/js/json2.js',
            'lib/js/select2.js',
            'lib/js/bootstrap.js'
          ],
          'lib/js/require.js': ['lib/js/require.js'],
          'lib/js/text.js': ['lib/js/text.js'],
          'lib/js/underscore.js': ['lib/js/underscore.js']
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
  grunt.loadNpmTasks('grunt-text-replace');

  // test
  grunt.registerTask('test', ['jshint']);

  // build development
  grunt.registerTask('default', ['jshint', 'less:development', 'concat:bootstrap', 'copy', 'replace']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify' ]);

};
