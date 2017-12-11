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
          files: [{
            expand: true,
            flatten: true,
            cwd: '.components',
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
            'jquery-tree-multiselect/dist/jquery.tree-multiselect.min.css',
            'bootstrap/dist/css/bootstrap.min.css',
            'leaflet-fullscreen/dist/leaflet.fullscreen.css',
            'leaflet-opacity/lib/opacity/Control.Opacity.css',
            'leaflet-measure/dist/leaflet-measure.css',
            'leaflet-navbar/src/Leaflet.NavBar.css',
            'eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
            'bootstrap-treeview/dist/bootstrap-treeview.min.css',
            'bootstrap-tokenfield/dist/css/bootstrap-tokenfield.min.css',
            'bootstrap-tokenfield/dist/css/tokenfield-typeahead.min.css',
            'bootstrap-select/dist/css/bootstrap-select.min.css',
            'bootstrap-wysiwyghtml5/dist/bootstrap-wysihtml5-0.0.2.css',
            'bootstrap-table/dist/bootstrap-table.min.css',
            'bootstrap-toggle/css/bootstrap-toggle.min.css',
            'fastselect/dist/fastselect.min.css',
            'Leaflet.EasyButton/src/easy-button.css'
          ]
        }, {
          expand: true,
          flatten: true,
          cwd: '.components',
          dest: 'lib/img',
          src: [
            'bootstrap/img/*.png',
            'select2/select2*.png',
            'select2/select2*.gif',
            'raty/lib/img/*.png',
            'jquery-ui/themes/base/images/*',
            'leaflet-fullscreen/dist/*.png',
            'leaflet-opacity/lib/opacity/images/*',
            'leaflet-opacity/lib/jquery/images/*',
            'leaflet-measure/dist/images/*',
            'leaflet-navbar/src/img/*',
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
            'jquery-tree-multiselect/dist/jquery.tree-multiselect.min.js',
            'json2/json2.js',
            'select2/select2.js',
            'requirejs/require.js',
            'requirejs-text/text.js',
            'underscore/underscore-min.js',
            'qunit/qunit/qunit.js',
            'angular/angular.js',
            'angular-cookies/angular-cookies.js',
            'angular-leaflet-directive/dist/angular-leaflet-directive.min.js',
            'bootstrap/dist/js/bootstrap.min.js',
            'zeroclipboard/dist/ZeroClipboard.min.js',
            'leaflet-fullscreen/dist/Leaflet.fullscreen.min.js',
            'leaflet-opacity/lib/opacity/Control.Opacity.js',
            'leaflet-measure/dist/leaflet-measure.js',
            'leaflet-navbar/src/Leaflet.NavBar.js',
            'moment/min/moment-with-locales.min.js',
            'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
            'bootstrap-treeview/dist/bootstrap-treeview.min.js',
            'bootstrap-tokenfield/dist/bootstrap-tokenfield.min.js',
            'bootstrap-select/dist/js/bootstrap-select.min.js',
            'bootstrap-wysiwyghtml5/dist/bootstrap-wysihtml5-0.0.2.min.js',
            'bootstrap-table/dist/bootstrap-table.min.js',
            'bootstrap-toggle/js/bootstrap-toggle.min.js',
            'fastselect/dist/fastselect.standalone.min.js',
            'clipboard/dist/clipboard.js',
            'Leaflet.EasyButton/src/easy-button.js'
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
          {
            from: /url\([\"\']?(\.\/)([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$2")'
          },
          /*
           * Pattern:
           * url('image _.png') or url("image _.png")
           */
          {
            from: /url\([\"\']?([\w-\.\s@]+)[\"\']?\)/g,
            to: 'url("../img/$1")'
          },
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
      production: {
        options: {
          // the banner is inserted at the top of the output
          banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
        },
        files: {
          'lib/css/assets.min.css': [
            'lib/css/bootstrap.min.css',
            'lib/css/bootstrap-datetimepicker.min.css',
            'lib/css/bootstrap-treeview.min.css',
            'lib/css/bootstrap-tokenfield.min.css',
            'lib/css/bootstrap-select.min.css',
            'lib/css/bootstrap-wysihtml5-0.0.2.css',
            'lib/css/bootstrap-table.min.css',
            'lib/css/bootstrap-toggle.min.css',
            'lib/css/fastselect.min.css',
            'lib/css/jquery-ui.css',
            'lib/css/jquery.dataTables.css',
            'lib/css/jquery.tree-multiselect.min.css',
            'lib/css/jquery.treefilter.css',
            'lib/css/L.Control.Pan.css',
            'lib/css/multi-select.css',
            'lib/css/select2.css'
          ],
          'lib/css/leaflet-plugins.min.css': [
            'lib/css/leaflet.fullscreen.css',
            'lib/css/Leaflet.NavBar.css',
            'lib/css/leaflet-measure.css',
            'lib/css/Control.Opacity.css',
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
      production: {
        files: {
          'lib/js/assets.min.js': [
            'lib/js/jquery.min.js',
            'lib/js/jquery-ui.custom.js',
            'lib/js/jquery.dataTables.js',
            'lib/js/jquery.raty.js',
            'lib/js/jquery.timeago.js',
            'lib/js/json2.js',
            'lib/js/waypoints.js',
            'lib/js/select2.min.js',
            'lib/js/moment-with-locales.min.js',
            'lib/js/fastselect.standalone.min.js',
            'lib/js/bootstrap.min.js',
            'lib/js/bootstrap-datetimepicker.min.js',
            'lib/js/bootstrap-tokenfield.min.js',
            'lib/js/bootstrap-treeview.min.js',
            'lib/js/bootstrap-select.min.js',
            'lib/js/bootstrap-wysihtml5-0.0.2.min.js',
            'lib/js/bootstrap-table.min.js',
            'lib/js/bootstrap-toggle.min.js',
            'lib/js/jquery.ajaxprogress.js',
            'lib/js/jquery.ajaxQueue.js',
            'lib/js/jquery.multi-select.js',
            'lib/js/jquery.tree-multiselect.min.js',
            'lib/js/jquery.treefilter-min.js',
            'lib/js/angular.js',
            'lib/js/angular-cookies.js',
            'lib/js/angular-leaflet-directive.min.js',
            'lib/js/ZeroClipboard.min.js',
            'lib/js/clipboard.js'
          ],
          'lib/js/jquery.js': ['lib/js/jquery.min.js'],
          'lib/js/require.js': ['lib/js/require.js'],
          'lib/js/text.js': ['lib/js/text.js'],
          'lib/js/underscore.js': ['lib/js/underscore-min.js'],
          'lib/js/leaflet-plugins.min.js': [
            'lib/js/Leaflet.fullscreen.min.js',
            'lib/js/Leaflet.NavBar.js',
            'lib/js/leaflet-measure.js',
            'lib/js/Control.Opacity.js',
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
  grunt.registerTask('default', ['jshint', 'less:development', 'concat:bootstrap', 'copy', 'replace']);

  // build production
  grunt.registerTask('production', ['jshint', 'less:production', 'concat:bootstrap', 'copy', 'replace', 'cssmin', 'uglify' ]);

};
