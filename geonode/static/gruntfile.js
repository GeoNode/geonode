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
          paths: ['node_modules/bootstrap/less'],
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
          files: [{
            expand: true,
            flatten: true,
            cwd: 'node_modules',
            dest: 'lib/js',
            src: [
              'bootstrap/dist/js/bootstrap.js',
              'bootstrap/js/affix.js',
              'bootstrap/js/alert.js',
              'bootstrap/js/button.js',
              'bootstrap/js/carousel.js',
              'bootstrap/js/collapse.js',
              'bootstrap/js/dropdown.js',
              'bootstrap/js/modal.js',
              'bootstrap/js/popover.js',
              'bootstrap/js/scrollspy.js',
              'bootstrap/js/tab.js',
              'bootstrap/js/tooltip.js',
              'bootstrap/js/transition.js'
            ]
        }]
      }
    },

    copy: {
      default: {
        files: [{
          expand: true,
          flatten: true,
          cwd: 'node_modules',
          dest: 'lib/css',
          src: [
            'datatables/media/css/jquery.dataTables.min.css',
            'select2/dist/css/select2.min.css',
            'multi-select/dist/bundles/multi-select.css',
            'jquery-ui/themes/base/*.css',
            'raty-js/lib/jquery.raty.css',
            'bootstrap/dist/css/bootstrap.min.css',
            'leaflet-fullscreen/dist/leaflet.fullscreen.css',
            'leaflet.control.opacity/dist/L.Control.Opacity.css',
            'leaflet-measure/dist/leaflet-measure.css',
            'leaflet-navbar/Leaflet.NavBar.css',
            'eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
            'bootstrap-tokenfield/dist/css/bootstrap-tokenfield.min.css',
            'bootstrap-select/dist/css/bootstrap-select.min.css',
            'bootstrap-multiselect/dist/css/bootstrap-multiselect.css',
            // 'bootstrap3-wysihtml5-npm/dist/bootstrap3-wysihtml5.min.css',
            // '@bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.min.css',
            'bootstrap-table/dist/bootstrap-table.min.css',
            'bootstrap-toggle/css/bootstrap-toggle.min.css',
            'fastselect/dist/fastselect.css',
            'leaflet-easybutton/src/easy-button.css',
            'leaflet.locatecontrol/dist/L.Control.Locate.min.css',
            'leaflet.pancontrol/src/L.Control.Pan.css',
            'patternfly-bootstrap-treeview/dist/bootstrap-treeview.min.css'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: 'node_modules',
          dest: 'lib/img',
          src: [
            'bootstrap/img/*.png',
            'select2/select2*.png',
            'select2/select2*.gif',
            'raty-js/lib/img/*.png',
            'jquery-ui/themes/base/images/*',
            'leaflet-fullscreen/dist/*.png',
            'leaflet-opacity/lib/opacity/images/*',
            'leaflet-opacity/lib/jquery/images/*',
            'leaflet-measure/dist/assets/*',
            'leaflet-navbar/img/*',
            'leaflet.pancontrol/src/images/*',
            'datatables/media/images/*.png',
            'timeago/*.png',
            'zeroclipboard/dist/ZeroClipboard.swf'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: 'node_modules',
          dest: 'lib/js',
          src: [
            'angular/angular.js',
            'angular/angular.min.js',
            'angular-cookies/angular-cookies.js',
            'angular-cookies/angular-cookies.min.js',
            'angular-leaflet-directive/dist/angular-leaflet-directive.js',
            'angular-leaflet-directive/dist/angular-leaflet-directive.min.js',

            'bootstrap/dist/js/bootstrap.js',
            'bootstrap/dist/js/bootstrap.min.js',
            'bootstrap-tokenfield/dist/bootstrap-tokenfield.js',
            'bootstrap-tokenfield/dist/bootstrap-tokenfield.min.js',
            'bootstrap-select/dist/js/bootstrap-select.js',
            'bootstrap-select/dist/js/bootstrap-select.min.js',
            'bootstrap-multiselect/dist/js/bootstrap-multiselect.js',
            // 'bootstrap3-wysihtml5-npm/dist/bootstrap3-wysihtml5.min.js',
            // '@bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.min.js',
            'bootstrap-table/dist/bootstrap-table.js',
            'bootstrap-table/dist/bootstrap-table.min.js',
            'bootstrap-toggle/js/bootstrap-toggle.js',
            'bootstrap-toggle/js/bootstrap-toggle.min.js',
            'bootstrap-typeahead/bootstrap-typeahead.js',

            'clipboard/dist/clipboard.js',
            'clipboard/dist/clipboard.min.js',
            'datatables/media/js/jquery.dataTables.js',

            'eonasdan-bootstrap-datetimepicker/src/js/bootstrap-datetimepicker.js',
            'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
            'fastselect/dist/fastselect.standalone.js',
            'fastselect/dist/fastselect.standalone.min.js',
            'handlebars/dist/handlebars.js',
            'handlebars/dist/handlebars.min.js',
            'json2/lib/JSON2/static/json2.js',

            'jquery/dist/jquery.js',
            'jquery/dist/jquery.min.js',
            'jquery-ui/dist/jquery-ui.js',
            'jquery-waypoints/waypoints.js',
            'jquery-waypoints/waypoints.min.js',
            'jq-ajax-progress/src/jq-ajax-progress.js',
            'jq-ajax-progress/src/jq-ajax-progress.min.js',

            'moment/min/moment-with-locales.min.js',
            'moment-timezone/builds/moment-timezone-with-data.min.js',

            'leaflet-fullscreen/dist/Leaflet.fullscreen.min.js',
            'leaflet-measure/dist/leaflet-measure.js',
            'leaflet-navbar/index.js',
            'leaflet-easybutton/src/easy-button.js',
            'leaflet.control.opacity/dist/L.Control.Opacity.js',
            'leaflet.locatecontrol/dist/L.Control.Locate.min.js',
            'leaflet.pancontrol/src/L.Control.Pan.js',

            'patternfly-bootstrap-treeview/dist/bootstrap-treeview.js',
            'patternfly-bootstrap-treeview/dist/bootstrap-treeview.min.js',

            'raty-js/lib/jquery.raty.js',
            'requirejs/require.js',
            'requirejs-text/text.js',
            'select/dist/select.js',
            'select2/dist/js/select2.full.js',
            'select2/dist/js/select2.full.min.js',
            'timeago/jquery.timeago.js',
            'tree-multiselect/dist/jquery.tree-multiselect.min.js',
            'underscore/underscore-min.js',
            'zeroclipboard/dist/ZeroClipboard.min.js'
          ]
        }]
      }
    },

    replace: {
      development: {
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
          banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
        },
        files: {
          'lib/css/assets.min.css': [
            'lib/css/bootstrap.min.css',
            'lib/css/bootstrap-datetimepicker.min.css',
            'lib/css/bootstrap-tokenfield.min.css',
            'lib/css/bootstrap-select.min.css',
            'lib/css/bootstrap-multiselect.css',
            // 'lib/css/bootstrap3-wysihtml5.min.css',
            'lib/css/bootstrap-table.min.css',
            'lib/css/bootstrap-toggle.min.css',
            'lib/css/all.css',  // jquery-ui.theme.base.css
            'lib/css/jquery.dataTables.css',
            'lib/css/jquery.raty.css',
            'lib/css/L.Control.Locate.min.css',
            'lib/css/L.Control.Pan.css',
            'lib/css/multi-select.css',
            'lib/css/select2.min.css',
            'lib/css/fastselect.css',
            'lib/css/bootstrap-treeview.min.css'
          ],
          'lib/css/leaflet-plugins.min.css': [
            'lib/css/leaflet.fullscreen.css',
            'lib/css/Leaflet.NavBar.css',
            'lib/css/leaflet-measure.css',
            'lib/css/L.Control.Opacity.css',
            'lib/css/easy-button.css'
          ]
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
          'lib/js/assets.min.js': [
            'lib/js/jquery.js',

            'lib/js/moment-with-locales.min.js',
            'lib/js/moment-timezone-with-data.min.js',

            'lib/js/angular.js',
            'lib/js/angular-cookies.js',
            'lib/js/angular-leaflet-directive.min.js',

            'lib/js/bootstrap.js',
            'lib/js/bootstrap-datetimepicker.js',
            'lib/js/bootstrap-tokenfield.js',
            'lib/js/bootstrap-select.js',
            'lib/js/bootstrap-multiselect.js',
            // 'lib/js/bootstrap3-wysihtml5.min.js',
            'lib/js/bootstrap-table.js',
            'lib/js/bootstrap-toggle.js',
            'lib/js/bootstrap-typeahead.js',
            'lib/js/bootstrap-treeview.js',

            'lib/js/clipboard.js',
            'lib/js/fastselect.standalone.js',
            'lib/js/handlebars.js',
            'lib/js/json2.js',
            'lib/js/jquery-ui.js',
            'lib/js/jquery.dataTables.js',
            'lib/js/jquery.raty.js',
            'lib/js/jquery.timeago.js',
            'lib/js/jq-ajax-progress.min.js',
            'lib/js/jquery.tree-multiselect.min.js',
            'lib/js/multi-select.js',
            'lib/js/select.js',
            'lib/js/select2.full.js',
            'lib/js/waypoints.js',
            'lib/js/underscore.js',
            'lib/js/ZeroClipboard.min.js'
          ],
          'lib/js/jquery.js': ['lib/js/jquery.js'],
          'lib/js/require.js': ['lib/js/require.js'],
          'lib/js/text.js': ['lib/js/text.js'],
          'lib/js/underscore.js': ['lib/js/underscore-min.js'],
          'lib/js/leaflet-plugins.min.js': [
            'lib/js/Leaflet.fullscreen.min.js',
            'lib/js/index.js',
            'lib/js/leaflet-measure.js',
            'lib/js/L.Control.Opacity.js',
            'lib/js/easy-button.js'
          ]
        }
      },
      production: {
        files: {
          'lib/js/assets.min.js': [
            'lib/js/jquery.min.js',

            'lib/js/angular.js',
            'lib/js/angular-cookies.js',
            'lib/js/angular-leaflet-directive.min.js',

            'lib/js/moment-with-locales.min.js',
            'lib/js/moment-timezone-with-data.min.js',

            'lib/js/bootstrap.min.js',
            'lib/js/bootstrap-datetimepicker.min.js',
            'lib/js/bootstrap-tokenfield.min.js',
            'lib/js/bootstrap-select.min.js',
            'lib/js/bootstrap-multiselect.js',
            // 'lib/js/bootstrap3-wysihtml5.min.js',
            'lib/js/bootstrap-table.min.js',
            'lib/js/bootstrap-toggle.min.js',
            'lib/js/bootstrap-typeahead.js',
            'lib/js/bootstrap-treeview.min.js',

            'lib/js/clipboard.min.js',
            'lib/js/fastselect.standalone.min.js',
            'lib/js/handlebars.min.js',
            'lib/js/json2.js',
            'lib/js/jquery-ui.js',
            'lib/js/jquery.dataTables.js',
            'lib/js/jquery.raty.js',
            'lib/js/jquery.timeago.js',
            'lib/js/jq-ajax-progress.min.js',
            'lib/js/jquery.tree-multiselect.min.js',
            'lib/js/multi-select.js',
            'lib/js/select.js',
            'lib/js/select2.full.min.js',
            'lib/js/waypoints.min.js',
            'lib/js/underscore.js',
            'lib/js/ZeroClipboard.min.js'
          ],
          'lib/js/jquery.js': ['lib/js/jquery.min.js'],
          'lib/js/require.js': ['lib/js/require.js'],
          'lib/js/text.js': ['lib/js/text.js'],
          'lib/js/underscore.js': ['lib/js/underscore-min.js'],
          'lib/js/leaflet-plugins.min.js': [
            'lib/js/Leaflet.fullscreen.min.js',
            'lib/js/index.js',
            'lib/js/leaflet-measure.js',
            'lib/js/L.Control.Opacity.js',
            'lib/js/easy-button.js'
          ]
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
  grunt.registerTask('development', ['jshint', 'less:development', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:development']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify:production']);

};
