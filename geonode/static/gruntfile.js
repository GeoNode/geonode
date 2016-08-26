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
            'jquery-ui/themes/smoothness/jquery-ui.css',
            'bootstrap/dist/css/bootstrap.min.css',
            'leaflet-fullscreen/dist/leaflet.fullscreen.css',
            'leaflet-fullscreen/dist/fullscreen@2x.png',
            'leaflet-fullscreen/dist/fullscreen.png',
            'eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.css',
            'bootstrap-treeview/dist/bootstrap-treeview.min.css',
            'bootstrap-tokenfield/dist/css/bootstrap-tokenfield.css'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/img',
          src: [
            'bootstrap/img/*.png',
            'select2/*.png', 'select2/spinner.gif',
            'raty/lib/img/*.png',
            'multi-select/img/switch.png',
            'datatables/media/images/*.png',
            'jquery-ui/themes/smoothness/images/animated-overlay.gif',
            'zeroclipboard/dist/ZeroClipboard.swf'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/js',
          src: [
            'jquery/dist/jquery.min.js',
            'datatables/media/js/jquery.dataTables.js',
            'jquery-timeago/jquery.timeago.js',
            'tinysort/src/jquery.tinysort.js',
            'raty/lib/jquery.raty.js',
            'jquery-waypoints/waypoints.js',
            'jquery-ui/ui/jquery-ui.custom.js',
            'jquery-ajaxprogress/jquery.ajaxprogress.js',
            'jquery.ajaxQueue/dist/jquery.ajaxQueue.js',
            'multi-select/js/jquery.multi-select.js',
            'json2/json2.js',
            'select2/select2.js',
            'requirejs/require.js',
            'requirejs-text/text.js',
            'underscore/underscore.js',
            'qunit/qunit/qunit.js',
            'angular/angular.js',
            'angular-leaflet-directive/dist/angular-leaflet-directive.min.js',
            'bootstrap/dist/js/bootstrap.min.js',
            'zeroclipboard/dist/ZeroClipboard.min.js',
            'leaflet-fullscreen/dist/Leaflet.fullscreen.min.js',
            'moment/min/moment-with-locales.min.js',
            'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
            'bootstrap-treeview/dist/bootstrap-treeview.min.js',
            'bootstrap-tokenfield/js/bootstrap-tokenfield.js'
          ]
        }]
      }
    },

    /*! 
     * change image paths in CSS to match url('../lib/img/image.png')
     * regex should cover following url patterns:
     * /url\("?images\//g          url("images/animated-overlay.gif")
     *                             url(images/ui-bg_flat_75_ffffff_40x100.png)
     * /url\('(?!(images|\.))/g    url('select2.png')
     *                             url('spinner.gif')
     * /url\((?!('|"))/g           url(select2x2.png)
     * must not change             url('../img/switch.png')
     * /url\('\.\.\/images\//g     url('../images/back_enabled.png')
     * must not change             alpha(opacity=25)
     * 
     * TODO: write testcase
     * var urls = ['url("images/animated-overlay.gif")', 'url(images/ui-bg_flat_75_ffffff_40x100.png)', "url('select2.png')", "url('spinner.gif')", "url(select2x2.png)", "url('../img/switch.png')", "url('../images/back_enabled.png')", "alpha(opacity=25)"],
     * urlsClean = [];
     * urls.forEach(function(elem) {
     *   var urlClean = elem.replace(/url\((("?images\/)|('(?!(images|\.)))|(?!('|"))|('\.\.\/images\/))/g, 'url(\'../img/').replace(/(png|gif|jpg)?(\)|'\)|"\))/g, '$1\')');
     *   urlsClean.push(urlClean);
     * });
     * console.log(urlsClean);
     */
    
    replace: {
      development: {
        src: ['lib/css/*.css'],
        overwrite: true,
        replacements: [{ 
          from: /url\((("?images\/)|('(?!(images|\.)))|(?!('|"))|('\.\.\/images\/))/g,
          to: 'url(\'../img/'
        }, {
          from: /(png|gif|jpg)+(\)|'\)|"\))/g, 
          to: '$1\')'
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
            'lib/css/bootstrap.min.css',
            'lib/css/jquery-ui.css',
            'lib/css/bootstrap-datetimepicker.css',
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
            'lib/js/jquery.min.js',
            'lib/js/jquery.dataTables.js',
            'lib/js/jquery.timeago.js',
            'lib/js/jquery.tinysort.js',
            'lib/js/jquery.raty.js',
            'lib/js/waypoints.js',
            'lib/js/jquery-ui.custom.js',
            'lib/js/jquery.ajaxprogress.js',
            'lib/js/jquery.ajaxQueue.js',
            'lib/js/jquery.multi-select.js',
            'lib/js/json2.js',
            'lib/js/select2.js',
            'lib/js/bootstrap.min.js',
            'lib/js/angular.js',
            'lib/js/angular-leaflet-directive.min.js',
            'lib/js/ZeroClipboard.min.js',
            'lib/js/moment-with-locales.min.js',
            'lib/js/bootstrap-datetimepicker.min.js'
          ],
          'lib/js/require.js': ['lib/js/require.js'],
          'lib/js/text.js': ['lib/js/text.js'],
          'lib/js/underscore.js': ['lib/js/underscore.js']
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
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-text-replace');

  // test
  grunt.registerTask('test', ['jshint']);

  // build development
  grunt.registerTask('default', ['jshint', 'less:development', 'concat:bootstrap', 'copy', 'replace']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:bootstrap', 'copy', 'cssmin', 'uglify' ]);

};
