// global ide object

var ide = new(function() {
  // == private members ==
  var attribControl = null;
  var scaleControl = null;
  var queryParser = turbo.query();
  var nominatim = turbo.nominatim();
  var ffs = turbo.ffs();
  // == public members ==
  this.codeEditor = null;
  this.dataViewer = null;
  this.map = null;

  // == helpers ==

  var make_combobox = function(input, options) {
    if (input[0].is_combobox) {
      input.autocomplete("option", {source:options});
      return;
    }
    var wrapper = input.wrap("<span>").parent().addClass("ui-combobox");
    input.autocomplete({
      source: options,
      minLength: 0,
    }).addClass("ui-widget ui-widget-content ui-corner-left ui-state-default");
    $( "<a>" ).attr("tabIndex", -1).attr("title","show all items").appendTo(wrapper).button({
      icons: {primary: "ui-icon-triangle-1-s"}, text:false
    }).removeClass( "ui-corner-all" ).addClass( "ui-corner-right ui-combobox-toggle" ).click(function() {
      // close if already visible
      if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
        input.autocomplete( "close" );
        return;
      }
      // pass empty string as value to search for, displaying all results
      input.autocomplete( "search", "" );
      input.focus();
    });
    input[0].is_combobox = true;
  } // make_combobox()

  // == public sub objects ==

  this.waiter = {
    opened: false,
    frames: "◴◷◶◵",
    open: function(show_info) {
      if (show_info) {
        $(".modal .wait-info h4").text(show_info);
        $(".wait-info").show();
      } else {
        $(".wait-info").hide();
      }
      $("body").addClass("loading");
      document.title = ide.waiter.frames[0] + " " + ide.waiter._initialTitle;
      var f = 0;
      ide.waiter.interval = setInterval(function() {
        document.title = ide.waiter.frames[++f % ide.waiter.frames.length] + " " + ide.waiter._initialTitle;
      }, 250);
      ide.waiter.opened = true;
    },
    close: function() {
      clearInterval(ide.waiter.interval);
      document.title = ide.waiter._initialTitle;
      $("body").removeClass("loading");
      $(".wait-info ul li").remove();
      delete ide.waiter.onAbort;
      ide.waiter.opened = false;
    },
    addInfo: function(txt, abortCallback) {
      $("#aborter").remove(); // remove previously added abort button, which cannot be used anymore.
      $(".wait-info ul li:nth-child(n+1)").css("opacity",0.5);
      $(".wait-info ul li span.ui-icon").addClass("ui-icon-check");
      $(".wait-info ul li:nth-child(n+4)").hide();
      var li = $('<li><span class="ui-icon ui-icon-arrowthick-1-e" style="display:inline-block; margin-bottom:-2px; margin-right:3px;"></span>'+txt+"</li>");
      if (typeof abortCallback == "function") {
        ide.waiter.onAbort = abortCallback;
        li.append('<span id="aborter">&nbsp;(<a href="#" onclick="ide.waiter.abort(); return false;">abort</a>)</span>');
      }
      $(".wait-info ul").prepend(li);
    },
    abort: function() {
      if (typeof ide.waiter.onAbort == "function") {
        ide.waiter.addInfo("aborting");
        ide.waiter.onAbort(ide.waiter.close);
      }
    },
  };
  this.waiter._initialTitle = document.title;

  // == public methods ==

  this.init = function() {
    ide.waiter.addInfo("ide starting up");
    // (very raw) compatibility check <- TODO: put this into its own function
    if (jQuery.support.cors != true ||
        //typeof localStorage  != "object" ||
        typeof (function() {var ls=undefined; try{localStorage.setItem("startup_localstorage_quota_test",123);localStorage.removeItem("startup_localstorage_quota_test");ls=localStorage;}catch(e){}; return ls;})() != "object" ||
        false) {
      // the currently used browser is not capable of running the IDE. :(
      ide.not_supported = true;
      $('#warning-unsupported-browser').dialog({modal:true});
    }
    // load settings
    ide.waiter.addInfo("load settings");
    settings.load();
    // translate ui
    ide.waiter.addInfo("translate ui");
    i18n.translate();
    // set up additional libraries
    moment.locale(i18n.getLanguage());
    // parse url string parameters
    ide.waiter.addInfo("parse url parameters");
    var args = turbo.urlParameters(location.search);
    // set appropriate settings
    if (args.has_coords) { // map center coords set via url
      settings.coords_lat = args.coords.lat;
      settings.coords_lon = args.coords.lng;
    }
    if (args.has_zoom) { // map zoom set via url
      settings.coords_zoom = args.zoom;
    }
    if (args.run_query) { // query autorun activated via url
      ide.run_query_on_startup = true;
    }
    settings.save();
    if (typeof history.replaceState == "function")
      history.replaceState({}, "", "."); // drop startup parameters

    ide.waiter.addInfo("initialize page");
    // init page layout
    var isInitialAspectPortrait = $(window).width() / $(window).height() < 0.8;
    if (settings.editor_width != "" && !isInitialAspectPortrait) {
      $("#editor").css("width",settings.editor_width);
      $("#dataviewer").css("left",settings.editor_width);
    }
    if (isInitialAspectPortrait) {
      $("#editor, #dataviewer").addClass('portrait');
    }
    // make panels resizable
    $("#editor").resizable({
      handles: isInitialAspectPortrait ? "s" : "e",
      minWidth: isInitialAspectPortrait ? undefined : "200",
      resize: function(ev) {
        if (!isInitialAspectPortrait) {
          $(this).next().css('left', $(this).outerWidth() + 'px');
        } else {
          var top = $(this).offset().top + $(this).outerHeight();
          $(this).next().css('top', top + 'px');
        }
        ide.map.invalidateSize(false);
      },
      stop:function() {
        if (isInitialAspectPortrait) return;
        settings.editor_width = $("#editor").css("width");
        settings.save();
      }
    });
    $("#editor").prepend("<span class='ui-resizable-handle ui-resizable-se ui-icon ui-icon-gripsmall-diagonal-se'/>");

    // init codemirror
    $("#editor textarea")[0].value = settings.code["overpass"];
    if (settings.use_rich_editor) {
      pending=0;
      CodeMirror.defineMIME("text/x-overpassQL", {
        name: "clike",
        keywords: (function(str){var r={}; var a=str.split(" "); for(var i=0; i<a.length; i++) r[a[i]]=true; return r;})(
          "out json xml custom popup timeout maxsize bbox" // initial declarations
          +" date diff adiff" //attic declarations
          +" foreach" // block statements
          +" relation rel way node is_in area around user uid newer changed poly pivot" // queries
          +" out meta body skel tags ids count qt asc" // actions
          +" center bb geom" // geometry types
          //+"r w n br bw" // recursors
        ),
      });
      CodeMirror.defineMIME("text/x-overpassXML",
        "xml"
      );
      CodeMirror.defineMode("xml+mustache", function(config) {
        return CodeMirror.multiplexingMode(
          CodeMirror.multiplexingMode(
            CodeMirror.getMode(config, "xml"),
            {open: "{{", close:"}}",
             mode:CodeMirror.getMode(config, "text/plain"),
             delimStyle: "mustache"}
          ),
          {open: "{{style:", close: "}}",
           mode: CodeMirror.getMode(config, "text/css"),
           delimStyle: "mustache"}
        );
      });
      CodeMirror.defineMode("ql+mustache", function(config) {
        return CodeMirror.multiplexingMode(
          CodeMirror.multiplexingMode(
            CodeMirror.getMode(config, "text/x-overpassQL"),
            {open: "{{", close:"}}",
             mode:CodeMirror.getMode(config, "text/plain"),
             delimStyle: "mustache"}
          ),
          {open: "{{style:", close: "}}",
           mode: CodeMirror.getMode(config, "text/css"),
           delimStyle: "mustache"}
        );
      });
      ide.codeEditor = CodeMirror.fromTextArea($("#editor textarea")[0], {
        //value: settings.code["overpass"],
        lineNumbers: true,
        lineWrapping: true,
        mode: "text/plain",
        onChange: function(e) {
          clearTimeout(pending);
          pending = setTimeout(function() {
            // update syntax highlighting mode
            if (ide.getQueryLang() == "xml") {
              if (e.getOption("mode") != "xml+mustache") {
                e.closeTagEnabled = true;
                e.setOption("matchBrackets",false);
                e.setOption("mode","xml+mustache");
              }
            } else {
              if (e.getOption("mode") != "ql+mustache") {
                e.closeTagEnabled = false;
                e.setOption("matchBrackets",true);
                e.setOption("mode","ql+mustache");
              }
            }
            // check for inactive ui elements
            var bbox_filter = $(".leaflet-control-buttons-bboxfilter");
            if (ide.getRawQuery().match(/\{\{bbox\}\}/)) {
              if (bbox_filter.hasClass("disabled")) {
                bbox_filter.removeClass("disabled");
                $("span",bbox_filter).css("opacity",1.0);
                bbox_filter.css("cursor","");
                bbox_filter.attr("data-t", "[title]map_controlls.select_bbox");
                i18n.translate_ui(bbox_filter[0]);
              }
            } else {
              if (!bbox_filter.hasClass("disabled")) {
                bbox_filter.addClass("disabled");
                $("span",bbox_filter).css("opacity",0.5);
                bbox_filter.css("cursor","default");
                bbox_filter.attr("data-t", "[title]map_controlls.select_bbox_disabled");
                i18n.translate_ui(bbox_filter[0]);
              }
            }
          },500);
          settings.code["overpass"] = e.getValue();
          settings.save();
        },
        closeTagEnabled: true,
        closeTagIndent: ["osm-script","query","union","foreach","difference"],
        extraKeys: {
          "'>'": function(cm) {cm.closeTag(cm, '>');},
          "'/'": function(cm) {cm.closeTag(cm, '/');},
        },
      });
      // fire onChange after initialization
      ide.codeEditor.getOption("onChange")(ide.codeEditor);
    } else { // use non-rich editor
      ide.codeEditor = $("#editor textarea")[0];
      ide.codeEditor.getValue = function() {
        return this.value;
      };
      ide.codeEditor.setValue = function(v) {
        this.value = v;
      };
      ide.codeEditor.lineCount = function() {
        return this.value.split(/\r\n|\r|\n/).length;
      };
      ide.codeEditor.setLineClass = function() {};
      $("#editor textarea").bind("input change", function(e) {
        settings.code["overpass"] = e.target.getValue();
        settings.save();
      });
    }
    // set query if provided as url parameter or template:
    if (args.has_query) { // query set via url
      ide.codeEditor.setValue(args.query);
    }
    // init dataviewer
    ide.dataViewer = CodeMirror($("#data")[0], {
      value:'no data loaded yet',
      lineNumbers: true,
      readOnly: true,
      mode: "javascript",
    });

    // init leaflet
    ide.map = new L.Map("map", {
      attributionControl:false,
      minZoom:0,
      maxZoom:configs.maxMapZoom,
      worldCopyJump:false,
    });
    var tilesUrl = settings.tile_server;
    var tilesAttrib = configs.tileServerAttribution;
    var tiles = new L.TileLayer(tilesUrl,{
      attribution:tilesAttrib,
      noWrap:true,
      maxNativeZoom:19,
      maxZoom:ide.map.options.maxZoom,
    });
    attribControl = new L.Control.Attribution({prefix:""});
    attribControl.addAttribution(tilesAttrib);
    var pos = new L.LatLng(settings.coords_lat,settings.coords_lon);
    ide.map.setView(pos,settings.coords_zoom).addLayer(tiles);
    ide.map.tile_layer = tiles;
    // inverse opacity layer
    ide.map.inv_opacity_layer = L.tileLayer("data:image/gif;base64,R0lGODlhAQABAIAAAP7//wAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==")
      .setOpacity(1-settings.background_opacity)
    if (settings.background_opacity != 1)
      ide.map.inv_opacity_layer.addTo(ide.map);
    scaleControl = new L.Control.Scale({metric:true,imperial:false,});
    scaleControl.addTo(ide.map);
    ide.map.on('moveend', function() {
      settings.coords_lat = ide.map.getCenter().lat;
      settings.coords_lon = ide.map.getCenter().lng;
      settings.coords_zoom = ide.map.getZoom();
      settings.save(); // save settings
    });

    // tabs
    $("#dataviewer > div#data")[0].style.zIndex = -1001;
    $(".tabs a.button").bind("click",function(e) {
      if ($(e.target).hasClass("active")) {
        return;
      } else {
        $("#dataviewer > div#data")[0].style.zIndex = -1*$("#dataviewer > div#data")[0].style.zIndex;
        $(".tabs a.button").toggleClass("active");
      }
    });

    // wait spinner
    $(document).on({
      ajaxStart: function() {
        if (!ide.waiter.opened) {
          ide.waiter.open();
          ide.waiter.ajaxAutoOpened = true;
        }
      },
      ajaxStop: function() {
        if (ide.waiter.ajaxAutoOpened) {
          ide.waiter.close();
          delete ide.waiter.ajaxAutoOpened;
        }
      },
    });

    // keyboard event listener
    $(document).keydown(ide.onKeyPress);

    // leaflet extension: more map controls
    var MapButtons = L.Control.extend({
      options: {
        position:'topleft',
      },
      onAdd: function(map) {
        // create the control container with a particular class name
        var container = L.DomUtil.create('div', 'leaflet-control-buttons leaflet-bar');
        var link = L.DomUtil.create('a', "leaflet-control-buttons-fitdata leaflet-bar-part leaflet-bar-part-top", container);
        $('<span class="ui-icon ui-icon-search"/>').appendTo($(link));
        link.href = '#';
        link.className += " t";
        link.setAttribute("data-t", "[title]map_controlls.zoom_to_data");
        i18n.translate_ui(link);
        L.DomEvent.addListener(link, 'click', function() {
          // hardcoded maxZoom of 18, should be ok for most real-world use-cases
          try {ide.map.fitBounds(overpass.osmLayer.getBaseLayer().getBounds(), {maxZoom: 18}); } catch (e) {}
          return false;
        }, ide.map);
        link = L.DomUtil.create('a', "leaflet-control-buttons-myloc leaflet-bar-part", container);
        $('<span class="ui-icon ui-icon-radio-off"/>').appendTo($(link));
        link.href = '#';
        link.className += " t";
        link.setAttribute("data-t", "[title]map_controlls.localize_user");
        i18n.translate_ui(link);
        L.DomEvent.addListener(link, 'click', function() {
          // One-shot position request.
          try {
            navigator.geolocation.getCurrentPosition(function (position){
              var pos = new L.LatLng(position.coords.latitude,position.coords.longitude);
              ide.map.setView(pos,settings.coords_zoom);
            });
          } catch(e) {}
          return false;
        }, ide.map);
        link = L.DomUtil.create('a', "leaflet-control-buttons-bboxfilter leaflet-bar-part", container);
        $('<span class="ui-icon ui-icon-image"/>').appendTo($(link));
        link.href = '#';
        link.className += " t";
        link.setAttribute("data-t", "[title]map_controlls.select_bbox");
        i18n.translate_ui(link);
        L.DomEvent.addListener(link, 'click', function(e) {
          if ($(e.target).parent().hasClass("disabled")) // check if this button is enabled
            return false;
          if (!ide.map.bboxfilter.isEnabled()) {
            ide.map.bboxfilter.setBounds(ide.map.getBounds().pad(-0.2));
            ide.map.bboxfilter.enable();
          } else {
            ide.map.bboxfilter.disable();
          }
          $(e.target).toggleClass("ui-icon-circlesmall-close").toggleClass("ui-icon-image");
          return false;
        }, ide.map);
        link = L.DomUtil.create('a', "leaflet-control-buttons-fullscreen leaflet-bar-part", container);
        $('<span class="ui-icon ui-icon-arrowthickstop-1-w"/>').appendTo($(link));
        link.href = '#';
        link.className += " t";
        link.setAttribute("data-t", "[title]map_controlls.toggle_wide_map");
        i18n.translate_ui(link);
        L.DomEvent.addListener(link, 'click', function(e) {
          $("#dataviewer").toggleClass("fullscreen");
          ide.map.invalidateSize();
          $(e.target).toggleClass("ui-icon-arrowthickstop-1-e").toggleClass("ui-icon-arrowthickstop-1-w");
          $("#editor").toggleClass("hidden");
          if ($("#editor").resizable("option","disabled"))
            $("#editor").resizable("enable");
          else
            $("#editor").resizable("disable");
          return false;
        }, ide.map);
        link = L.DomUtil.create('a', "leaflet-control-buttons-clearoverlay leaflet-bar-part leaflet-bar-part-bottom", container);
        $('<span class="ui-icon ui-icon-cancel"/>').appendTo($(link));
        link.href = '#';
        link.className += " t";
        link.setAttribute("data-t", "[title]map_controlls.toggle_data");
        i18n.translate_ui(link);
        L.DomEvent.addListener(link, 'click', function(e) {
          e.preventDefault();
          if (ide.map.hasLayer(overpass.osmLayer))
            ide.map.removeLayer(overpass.osmLayer);
          else
            ide.map.addLayer(overpass.osmLayer);
          return false;
        }, ide.map);
        return container;
      },
    });
    ide.map.addControl(new MapButtons());
    // prevent propagation of doubleclicks on map controls
    $(".leaflet-control-buttons > a").bind('dblclick', function(e) {
      e.stopPropagation();
    });
    // add tooltips to map controls
    $(".leaflet-control-buttons > a").tooltip({
      items: "a[title]",
      hide: {
        effect: "fadeOut",
        duration: 100
      },
      position: {
        my: "left+5 center",
        at: "right center"
      }
    });
    // leaflet extension: search box
    var SearchBox = L.Control.extend({
      options: {
        position:'topleft',
      },
      onAdd: function(map) {
        var container = L.DomUtil.create('div', 'leaflet-control-search ui-widget');
        container.style.position = "absolute";
        container.style.left = "40px";
        var inp = L.DomUtil.create('input', '', container);
        $('<span class="ui-icon ui-icon-search" style="position:absolute; right:3px; top:3px; opacity:0.5;"/>').click(function(e) {$(this).prev().autocomplete("search");}).insertAfter(inp);
        inp.id = "search";
        // hack against focus stealing leaflet :/
        inp.onclick = function() {this.focus();}
        // prevent propagation of doubleclicks to map container
        container.ondblclick = function(e) {
          e.stopPropagation();
        };
        // autocomplete functionality
        $(inp).autocomplete({
          source: function(request,response) {
            // ajax (GET) request to nominatim
            $.ajax("//nominatim.openstreetmap.org/search"+"?X-Requested-With="+configs.appname, {
              data:{
                format:"json",
                q: request.term
              },
              success: function(data) {
                // hacky firefox hack :( (it is not properly detecting json from the content-type header)
                if (typeof data == "string") { // if the data is a string, but looks more like a json object
                  try {
                    data = $.parseJSON(data);
                  } catch (e) {}
                }
                response($.map(data,function(item) {
                  return {label:item.display_name, value:item.display_name,lat:item.lat,lon:item.lon,boundingbox:item.boundingbox}
                }));
              },
              error: function() {
                // todo: better error handling
                alert("An error occured while contacting the osm search server nominatim.openstreetmap.org :(");
              },
            });
          },
          minLength: 2,
          select: function(event,ui) {
            if (ui.item.boundingbox && ui.item.boundingbox instanceof Array)
              ide.map.fitBounds(L.latLngBounds([[ui.item.boundingbox[0],ui.item.boundingbox[3]],[ui.item.boundingbox[1],ui.item.boundingbox[2]]]), {maxZoom: 18});
            else
              ide.map.panTo(new L.LatLng(ui.item.lat,ui.item.lon));
            this.value="";
            return false;
          },
          open: function() {
            $(this).removeClass("ui-corner-all").addClass("ui-corner-top");
          },
          close: function() {
            $(this).addClass("ui-corner-all").removeClass("ui-corner-top");
          },
        });
        $(inp).autocomplete("option","delay",2000000000); // do not do this at all
        $(inp).autocomplete().keypress(function(e) {if (e.which==13 || e.which==10) $(this).autocomplete("search");});
        return container;
      },
    });
    ide.map.addControl(new SearchBox());
    // add cross hairs to map
    $('<span class="ui-icon ui-icon-plus" />')
      .addClass("crosshairs")
      .hide()
      .appendTo("#map");
    if (settings.enable_crosshairs)
      $(".crosshairs").show();

    ide.map.bboxfilter = new L.LocationFilter({enable:!true,adjustButton:false,enableButton:false,}).addTo(ide.map);

    ide.map.on("popupopen popupclose",function(e) {
      if (typeof e.popup.layer != "undefined") {
        var layer = e.popup.layer.placeholder || e.popup.layer;
        // re-call style handler to eventually modify the style of the clicked feature
        var stl = overpass.osmLayer._baseLayer.options.style(layer.feature, e.type=="popupopen");
        if (typeof layer.eachLayer != "function") {
          if (typeof layer.setStyle == "function")
            layer.setStyle(stl); // other objects (pois, ways)
        } else
          layer.eachLayer(function(layer) {
            if (typeof layer.setStyle == "function")
              layer.setStyle(stl);
          }); // for multipolygons!
      }
    });

    // init overpass object
    overpass.init();

    // event handlers for overpass object
    overpass.handlers["onProgress"] = function(msg,abortcallback) {
      ide.waiter.addInfo(msg,abortcallback);
    }
    overpass.handlers["onDone"] = function() {
      ide.waiter.close();
      var map_bounds  = ide.map.getBounds();
      var data_bounds = overpass.osmLayer.getBaseLayer().getBounds();
      if (data_bounds.isValid() && !map_bounds.intersects(data_bounds)) {
        // show tooltip for button "zoom to data"
        var prev_content = $(".leaflet-control-buttons-fitdata").tooltip("option","content");
        $(".leaflet-control-buttons-fitdata").tooltip("option","content", "← "+i18n.t("map_controlls.suggest_zoom_to_data"));
        $(".leaflet-control-buttons-fitdata").tooltip("open");
        $(".leaflet-control-buttons-fitdata").tooltip("option", "hide", { effect: "fadeOut", duration: 1000 });
        setTimeout(function(){
          $(".leaflet-control-buttons-fitdata").tooltip("option","content", prev_content);
          $(".leaflet-control-buttons-fitdata").tooltip("close");
          $(".leaflet-control-buttons-fitdata").tooltip("option", "hide", { effect: "fadeOut", duration: 100 });
        },2600);
      }
    }
    overpass.handlers["onEmptyMap"] = function(empty_msg, data_mode) {
      // show warning/info if only invisible data is returned
      if (empty_msg == "no visible data") {
        if (!settings.no_autorepair) {
          var dialog_buttons= {};
          dialog_buttons[i18n.t("dialog.repair_query")] = function() {
            ide.repairQuery("no visible data");
            $(this).dialog("close");
          };
          dialog_buttons[i18n.t("dialog.show_data")] = function() {
            if ($("input[name=hide_incomplete_data_warning]",this)[0].checked) {
              settings.no_autorepair = true;
              settings.save();
            }
            ide.switchTab("Data");
            $(this).dialog("close");
          };
          $('<div title="'+i18n.t("warning.incomplete.title")+'"><p>'+i18n.t("warning.incomplete.expl.1")+'</p><p>'+i18n.t("warning.incomplete.expl.2")+'</p><p><input type="checkbox" name="hide_incomplete_data_warning"/>&nbsp;'+i18n.t("warning.incomplete.not_again")+'</p></div>').dialog({
            modal:true,
            buttons: dialog_buttons,
          });
        }
      }
      // auto tab switching (if only areas are returned)
      if (empty_msg == "only areas returned")
        ide.switchTab("Data");
      // auto tab switching (if nodes without coordinates are returned)
      if (empty_msg == "no coordinates returned")
        ide.switchTab("Data");
      // auto tab switching (if unstructured data is returned)
      if (data_mode == "unknown")
        ide.switchTab("Data");
      // display empty map badge
      $('<div id="map_blank" style="z-index:5; display:block; position:relative; top:42px; width:100%; text-align:center; background-color:#eee; opacity: 0.8;">'+i18n.t("map.intentionally_blank")+' <small>('+empty_msg+')</small></div>').appendTo("#map");
    }
    overpass.handlers["onDataRecieved"] = function(amount, amount_txt, abortCB, continueCB) {
      if (amount > 1000000) { // more than ~1MB of data
        // show warning dialog
        var dialog_buttons= {};
        dialog_buttons[i18n.t("dialog.abort")] = function() {
          $(this).dialog("close");
          abortCB();
        };
        dialog_buttons[i18n.t("dialog.continue_anyway")] = function() {
          $(this).dialog("close");
          continueCB();
        };
        $('<div title="'+i18n.t("warning.huge_data.title")+'"><p>'+i18n.t("warning.huge_data.expl.1").replace("{{amount_txt}}",amount_txt)+'</p><p>'+i18n.t("warning.huge_data.expl.2")+'</p></div>').dialog({
          modal:true,
          buttons: dialog_buttons,
          dialogClass: "huge_data"
        });
      } else
        continueCB();
    }
    overpass.handlers["onAbort"] = function() {
      ide.waiter.close();
    }
    overpass.handlers["onAjaxError"] = function(errmsg) {
      // show error dialog
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
      $('<div title="'+i18n.t("error.ajax.title")+'"><p style="color:red;">'+i18n.t("error.ajax.expl")+'</p>'+errmsg+'</div>').dialog({
        modal:true,
        buttons: dialog_buttons,
      }); // dialog
      // print error text, if present
      if (overpass.resultText)
        ide.dataViewer.setValue(overpass.resultText);
    }
    overpass.handlers["onQueryError"] = function(errmsg) {
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
      $('<div title="'+i18n.t("error.query.title")+'"><p style="color:red;">'+i18n.t("error.query.expl")+'</p>'+errmsg+"</div>").dialog({
        modal:true,
        maxHeight:600,
        buttons: dialog_buttons,
      });
    }
    overpass.handlers["onStyleError"] = function(errmsg) {
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
      $('<div title="'+i18n.t("error.mapcss.title")+'"><p style="color:red;">'+i18n.t("error.mapcss.expl")+'</p>'+errmsg+"</div>").dialog({
        modal:true,
        buttons: dialog_buttons,
      });
    }
    overpass.handlers["onQueryErrorLine"] = function(linenumber) {
      ide.highlightError(linenumber);
    }
    overpass.handlers["onRawDataPresent"] = function() {
      ide.dataViewer.setOption("mode",overpass.resultType);
      ide.dataViewer.setValue(overpass.resultText);
    }
    overpass.handlers["onGeoJsonReady"] = function() {
      // show layer
      ide.map.addLayer(overpass.osmLayer);
      // autorun callback (e.g. zoom to data)
      if (typeof ide.run_query_on_startup === "function") {
        ide.run_query_on_startup();
      }
      // display stats
      if (settings.show_data_stats) {
        var stats = overpass.stats;
        var stats_txt = (
          "<small>"+i18n.t("data_stats.loaded")+"</small>&nbsp;&ndash;&nbsp;"+
          ""+i18n.t("data_stats.nodes")+":&nbsp;"+stats.data.nodes+
          ", "+i18n.t("data_stats.ways")+":&nbsp;"+stats.data.ways+
          ", "+i18n.t("data_stats.relations")+":&nbsp;"+stats.data.relations+
          (stats.data.areas>0 ? ", "+i18n.t("data_stats.areas")+":&nbsp;"+stats.data.areas : "") +
          "<br/>"+
          "<small>"+i18n.t("data_stats.displayed")+"</small>&nbsp;&ndash;&nbsp;"+
          ""+i18n.t("data_stats.pois")+":&nbsp;"+stats.geojson.pois+
          ", "+i18n.t("data_stats.lines")+":&nbsp;"+stats.geojson.lines+
          ", "+i18n.t("data_stats.polygons")+":&nbsp;"+stats.geojson.polys+
          "</small>"
        );
        $(
          '<div id="data_stats" class="stats">'
          +stats_txt
          +'</div>'
        ).insertAfter("#map");
        // show more stats as a tooltip
        var backlogOverpass = function () {
          return moment(overpass.timestamp, moment.ISO_8601).fromNow(true);
          //return Math.round((new Date() - new Date(overpass.timestamp))/1000/60*10)/10;
        };
        var backlogOverpassAreas = function () {
          return moment(overpass.timestampAreas, moment.ISO_8601).fromNow(true);
        };
        var backlogOverpassExceedsLimit = function() {
          var now = moment();
          var ts = moment(overpass.timestamp, moment.ISO_8601);
          return (now.diff(ts, 'hours', true) >= 24);
        };
        var backlogOverpassAreasExceedsLimit = function() {
          var now = moment();
          var ts = moment(overpass.timestampAreas, moment.ISO_8601);
          return (now.diff(ts, 'hours', true) >= 96);
        };
        $("#data_stats").tooltip({
          items: "div",
          tooltipClass: "stats",
          content: function () {
            var str = "<div>";
            if (overpass.timestamp) {
              str += i18n.t("data_stats.lag")+": "
                  +  backlogOverpass()+" <small>"+i18n.t("data_stats.lag.expl")+"</small>"
            }
            if (overpass.timestampAreas) {
              str += "<br>"
                  +  i18n.t("data_stats.lag_areas")+": "
                  +  backlogOverpassAreas()+" <small>"+i18n.t("data_stats.lag.expl")+"</small>"
            }
            str+="</div>";
            return str;
          },
          hide: {
            effect: "fadeOut",
            duration: 100
          },
          position: {
            my: "right bottom-5",
            at: "right top"
          }
        });
        if ((overpass.timestamp && backlogOverpassExceedsLimit()) ||
            (overpass.timestampAreas && backlogOverpassAreasExceedsLimit())) {
          $("#data_stats").css("background-color","yellow");
        }
      }
    }
    overpass.handlers["onPopupReady"] = function(p) {
      p.openOn(ide.map);
    }

    // close startup waiter
    ide.waiter.close();

    // run the query immediately, if the appropriate flag was set.
    if (ide.run_query_on_startup === true) {
      ide.update_map();
      // automatically zoom to data.
      if (!args.has_coords &&
          args.has_query &&
          args.query.match(/\{\{(bbox|center)\}\}/) === null) {
        ide.run_query_on_startup = function() {
          ide.run_query_on_startup = null;
          // hardcoded maxZoom of 18, should be ok for most real-world use-cases
          try {ide.map.fitBounds(overpass.osmLayer.getBaseLayer().getBounds(), {maxZoom: 18}); } catch (e) {}
          // todo: zoom only to specific zoomlevel if args.has_zoom is given
        }
      }
    }
  } // init()

  // returns the current visible bbox as a bbox-query
  this.map2bbox = function(lang) {
    var bbox;
    if (!ide.map.bboxfilter.isEnabled())
      bbox = this.map.getBounds();
    else
      bbox = ide.map.bboxfilter.getBounds();
    var lat1 = Math.min(Math.max(bbox.getSouthWest().lat,-90),90);
    var lat2 = Math.min(Math.max(bbox.getNorthEast().lat,-90),90);
    var lng1 = Math.min(Math.max(bbox.getSouthWest().lng,-180),180);
    var lng2 = Math.min(Math.max(bbox.getNorthEast().lng,-180),180);
    if (lang=="OverpassQL")
      return lat1+','+lng1+','+lat2+','+lng2;
    else if (lang=="xml")
      return 's="'+lat1+'" w="'+lng1+'" n="'+lat2+'" e="'+lng2+'"';
  }
  // returns the current visible map center as a coord-query
  this.map2coord = function(lang) {
    var center = this.map.getCenter();
    if (lang=="OverpassQL")
      return center.lat+','+center.lng;
    else if (lang=="xml")
      return 'lat="'+center.lat+'" lon="'+center.lng+'"';
  }
  this.relativeTime = function(instr, callback) {
    var now = Date.now();
    // very basic differential date
    instr = instr.toLowerCase().match(/(-?[0-9]+) ?(seconds?|minutes?|hours?|days?|weeks?|months?|years?)?/);
    if (instr === null) {
      callback(''); // todo: throw an error. do not silently fail
      return;
    }
    var count = parseInt(instr[1]);
    var interval;
    switch (instr[2]) {
      case "second":
      case "seconds":
      interval=1; break;
      case "minute":
      case "minutes":
      interval=60; break;
      case "hour":
      case "hours":
      interval=3600; break;
      case "day":
      case "days":
      default:
      interval=86400; break;
      case "week":
      case "weeks":
      interval=604800; break;
      case "month":
      case "months":
      interval=2628000; break;
      case "year":
      case "years":
      interval=31536000; break;
    }
    var date = now - count*interval*1000;
    callback((new Date(date)).toISOString());
  }
  function onNominatimError(search,type) {
    // close waiter
    ide.waiter.close();
    // highlight error lines
    var query = ide.getRawQuery();
    query = query.split("\n");
    query.forEach(function(line,i) {
      if (line.indexOf("{{geocode"+type+":"+search+"}}") !== -1)
        ide.highlightError(i+1);
    });
    // show error message dialog
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
    $('<div title="'+i18n.t("error.nominatim.title")+'"><p style="color:red;">'+i18n.t("error.nominatim.expl")+'</p><p><i>'+htmlentities(search)+'</i></p></div>').dialog({
      modal:true,
      buttons: dialog_buttons,
    }); // dialog
  }
  this.geocodeId = function(instr, callback) {
    var lang = ide.getQueryLang();
    function filter(n) {
      return n.osm_type && n.osm_id;
    }
    nominatim.getBest(instr,filter, function(err, res) {
      if (err) return onNominatimError(instr,"Id");
      if (lang=="OverpassQL")
        res = res.osm_type+"("+res.osm_id+")";
      else if (lang=="xml")
        res = 'type="'+res.osm_type+'" ref="'+res.osm_id+'"';
      callback(res);
    });
  }
  this.geocodeArea = function(instr, callback) {
    var lang = ide.getQueryLang();
    function filter(n) {
      return n.osm_type && n.osm_id && n.osm_type!=="node";
    }
    nominatim.getBest(instr,filter, function(err, res) {
      if (err) return onNominatimError(instr,"Area");
      var area_ref = 1*res.osm_id;
      if (res.osm_type == "way")
        area_ref += 2400000000;
      if (res.osm_type == "relation")
        area_ref += 3600000000;
      if (lang=="OverpassQL")
        res = "area("+area_ref+")";
      else if (lang=="xml")
        res = 'type="area" ref="'+area_ref+'"';
      callback(res);
    });
  }
  this.geocodeBbox = function(instr, callback) {
    var lang = ide.getQueryLang();
    nominatim.getBest(instr, function(err, res) {
      if (err) return onNominatimError(instr,"Bbox");
      var lat1 = Math.min(Math.max(res.boundingbox[0],-90),90);
      var lat2 = Math.min(Math.max(res.boundingbox[1],-90),90);
      var lng1 = Math.min(Math.max(res.boundingbox[2],-180),180);
      var lng2 = Math.min(Math.max(res.boundingbox[3],-180),180);
      if (lang=="OverpassQL")
        res = lat1+','+lng1+','+lat2+','+lng2;
      else if (lang=="xml")
        res = 's="'+lat1+'" w="'+lng1+'" n="'+lat2+'" e="'+lng2+'"';
      callback(res);
    });
  }
  this.geocodeCoords = function(instr, callback) {
    var lang = ide.getQueryLang();
    nominatim.getBest(instr, function(err, res) {
      if (err) return onNominatimError(instr,"Coords");
      if (lang=="OverpassQL")
        res = res.lat+','+res.lon;
      else if (lang=="xml")
        res = 'lat="'+res.lat+'" lon="'+res.lon+'"';
      callback(res);
    });
  }
  /* this returns the current raw query in the editor.
   * shortcuts are not expanded. */
  this.getRawQuery = function() {
    return ide.codeEditor.getValue();
  }
  /* this returns the current query in the editor.
   * shortcuts are expanded. */
  this.getQuery = function(callback) {
    var query = ide.getRawQuery();
    var queryLang = ide.getQueryLang();
    // parse query and process shortcuts
    // special handling for global bbox in xml queries (which uses an OverpassQL-like notation instead of n/s/e/w parameters):
    query = query.replace(/(\<osm-script[^>]+bbox[^=]*=[^"'']*["'])({{bbox}})(["'])/,"$1{{__bbox__global_bbox_xml__ezs4K8__}}$3");
    var shortcuts = {
      "bbox": ide.map2bbox(queryLang),
      "center": ide.map2coord(queryLang),
      "__bbox__global_bbox_xml__ezs4K8__": ide.map2bbox("OverpassQL"),
      "date": ide.relativeTime,
      "geocodeId": ide.geocodeId,
      "geocodeArea": ide.geocodeArea,
      "geocodeBbox": ide.geocodeBbox,
      "geocodeCoords": ide.geocodeCoords,
      // legacy
      "nominatimId": queryLang=="xml" ? ide.geocodeId : function(instr,callback) {
        ide.geocodeId(instr, function(result) { callback(result+';'); });
      },
      "nominatimArea": queryLang=="xml" ? ide.geocodeArea : function(instr,callback) {
        ide.geocodeArea(instr, function(result) { callback(result+';'); });
      },
      "nominatimBbox": ide.geocodeBbox,
      "nominatimCoords": ide.geocodeCoords,
    };
    queryParser.parse(query, shortcuts, function(query) {
      // parse mapcss declarations
      var mapcss = "";
      if (queryParser.hasStatement("style"))
        mapcss = queryParser.getStatement("style");
      ide.mapcss = mapcss;
      // parse data-source statements
      var data_source = null;
      if (queryParser.hasStatement("data")) {
        data_source = queryParser.getStatement("data");
        data_source = data_source.split(',');
        var data_mode = data_source[0].toLowerCase();
        data_source = data_source.slice(1);
        var options = {};
        for (var i=0; i<data_source.length; i++) {
          var tmp = data_source[i].split('=');
          options[tmp[0]] = tmp[1];
        }
        data_source = {
          mode: data_mode,
          options: options
        };
      }
      ide.data_source = data_source;
      // call result callback
      callback(query);
    });
  }
  this.setQuery = function(query) {
    ide.codeEditor.setValue(query);
  }
  this.getQueryLang = function() {
    if ($.trim(ide.getRawQuery().replace(/{{.*?}}/g,"")).match(/^</))
      return "xml";
    else
      return "OverpassQL";
  }
  /* this is for repairig obvious mistakes in the query, such as missing recurse statements */
  this.repairQuery = function(repair) {
    // - preparations -
    var q = ide.getRawQuery(), // get original query
        lng = ide.getQueryLang();
    var autorepair = turbo.autorepair(q, lng);
    // - repairs -
    if (repair == "no visible data") {
      // repair missing recurse statements
      autorepair.recurse();
    } else if (repair == "xml+metadata") {
      // repair output for OSM editors
      autorepair.editors();
    }
    // - set repaired query -
    ide.setQuery(autorepair.getQuery());
  }
  this.highlightError = function(line) {
    ide.codeEditor.setLineClass(line-1,null,"errorline");
  }
  this.resetErrors = function() {
    for (var i=0; i<ide.codeEditor.lineCount(); i++)
      ide.codeEditor.setLineClass(i,null,null);
  }

  this.switchTab = function(tab) {
    $("#navs .tabs a."+tab).click();
  }

  this.loadExample = function(ex) {
    if (typeof settings.saves[ex] != "undefined")
      ide.setQuery(settings.saves[ex].overpass);
  }
  this.removeExample = function(ex,self) {
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.delete")] = function() {
      delete settings.saves[ex];
      settings.save();
      $(self).parent().remove();
      $(this).dialog( "close" );
    };
    dialog_buttons[i18n.t("dialog.cancel")] = function() {$(this).dialog("close");};
    $('<div title="'+i18n.t("dialog.delete_query.title")+'"><p><span class="ui-icon ui-icon-alert" style="float:left; margin:1px 7px 20px 0;"></span>'+i18n.t("dialog.delete_query.expl")+': &quot;<i>'+ex+'</i>&quot;?</p></div>').dialog({
      modal: true,
      buttons: dialog_buttons,
    });
  }

  // Event handlers
  this.onLoadClick = function() {
    $("#load-dialog ul").html(""); // reset example lists
    // load example list
    var has_saved_query = false;
    for(var example in settings.saves) {
      var type = settings.saves[example].type;
      if (type == 'template') continue;
      $('<li>'+
          '<a href="" onclick="ide.loadExample(\''+htmlentities(example).replace(/'/g,"\\'")+'\'); $(this).parents(\'.ui-dialog-content\').dialog(\'close\'); return false;">'+example+'</a>'+
          '<a href="" onclick="ide.removeExample(\''+htmlentities(example).replace(/'/g,"\\'")+'\',this); return false;" title="'+i18n.t("load.delete_query")+'" class="delete-query"><span class="ui-icon ui-icon-close" style="display:inline-block;"/></a>'+
        '</li>').appendTo("#load-dialog ul."+type);
      if (type == "saved_query")
        has_saved_query = true;
    }
    if (!has_saved_query)
      $('<li>'+i18n.t("load.no_saved_query")+'</li>').appendTo("#load-dialog ul.saved_query");
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.cancel")] = function() {$(this).dialog("close");};
    $("#load-dialog").dialog({
      modal:true,
      buttons: dialog_buttons,
    });
    $("#load-dialog").accordion({active: has_saved_query ? 0 : 1});
  }
  this.onSaveClick = function() {
    // combobox for existing saves.
    var saves_names = new Array();
    for (var key in settings.saves)
      if (settings.saves[key].type != "template")
        saves_names.push(key);
    make_combobox($("#save-dialog input[name=save]"), saves_names);
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.save")] = function() {
      var name = $("input[name=save]",this)[0].value;
      settings.saves[htmlentities(name)] = {
        "overpass": ide.getRawQuery(),
        "type": "saved_query"
      };
      settings.save();
      $(this).dialog("close");
    };
    dialog_buttons[i18n.t("dialog.cancel")] = function() {$(this).dialog("close");};
    $("#save-dialog").dialog({
      modal:true,
      buttons: dialog_buttons,
    });
  }
  this.onRunClick = function() {
    ide.update_map();
  }
  this.compose_share_link = function(query,compression,coords,run) {
    var share_link = "";
    if (!compression) { // compose uncompressed share link
      share_link += "?Q="+encodeURIComponent(query);
      if (coords)
        share_link += "&C="+L.Util.formatNum(ide.map.getCenter().lat)+";"+L.Util.formatNum(ide.map.getCenter().lng)+";"+ide.map.getZoom();
      if (run)
        share_link += "&R";
    } else { // compose compressed share link
      share_link += "?q="+encodeURIComponent(Base64.encode(lzw_encode(query)));
      if (coords) {
        var encode_coords = function(lat,lng) {
          var coords_cpr = Base64.encodeNum( Math.round((lat+90)*100000) + Math.round((lng+180)*100000)*180*100000 );
          return "AAAAAAAA".substring(0,9-coords_cpr.length)+coords_cpr;
        }
        share_link += "&c="+encode_coords(ide.map.getCenter().lat, ide.map.getCenter().lng)+Base64.encodeNum(ide.map.getZoom());
      }
      if (run)
        share_link += "&R";
    }
    return share_link;
  }
  this.updateShareLink = function() {
    var baseurl=location.protocol+"//"+location.host+location.pathname;
    var query = ide.getRawQuery();
    var compress = ((settings.share_compression == "auto" && query.length > 300) ||
        (settings.share_compression == "on"))
    var inc_coords = $("div#share-dialog input[name=include_coords]")[0].checked;
    var run_immediately = $("div#share-dialog input[name=run_immediately]")[0].checked;

    var shared_query = ide.compose_share_link(query,compress,inc_coords,run_immediately);
    var share_link = baseurl+shared_query;

    var warning = '';
    if (share_link.length >= 2000)
      warning = '<p class="warning">'+i18n.t("warning.share.long")+'</p>';
    if (share_link.length >= 4000)
      warning = '<p class="warning severe">'+i18n.t("warning.share.very_long")+'</p>';

    $("div#share-dialog #share_link_warning").html(warning);

    $("div#share-dialog #share_link_a")[0].href=share_link;
    $("div#share-dialog #share_link_textarea")[0].value=share_link;

    // automatically minify urls if enabled
    if (configs.short_url_service != "") {
      $.get(configs.short_url_service+encodeURIComponent(share_link), function(data) {
        $("div#share-dialog #share_link_a")[0].href=data;
        $("div#share-dialog #share_link_textarea")[0].value=data;
      });
    }
  }
  this.onShareClick = function() {
    $("div#share-dialog input[name=include_coords]")[0].checked = settings.share_include_pos;
    ide.updateShareLink();
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
    $("div#share-dialog").dialog({
      modal:true,
      buttons: dialog_buttons,
    });
  }
  this.onExportClick = function() {
   // prepare export dialog
   ide.getQuery(function(query) {
    var baseurl=location.protocol+"//"+location.host+location.pathname.match(/.*\//)[0];
    var server = (ide.data_source &&
                  ide.data_source.mode == "overpass" &&
                  ide.data_source.options.server) ?
                ide.data_source.options.server : settings.server;
    var queryWithMapCSS = query;
    if (queryParser.hasStatement("style"))
      queryWithMapCSS += "{{style: "+queryParser.getStatement("style")+" }}";
    if (queryParser.hasStatement("data"))
      queryWithMapCSS += "{{data:"+queryParser.getStatement("data")+"}}";
    else if (settings.server !== configs.defaultServer)
      queryWithMapCSS += "{{data:overpass,server="+settings.server+"}}";
    //$("#export-dialog a#export-interactive-map")[0].href = baseurl+"map.html?Q="+encodeURIComponent(queryWithMapCSS);
    // encoding exclamation marks for better command line usability (bash)
    //$("#export-dialog a#export-overpass-api")[0].href = server+"interpreter?data="+encodeURIComponent(query).replace(/!/g,"%21").replace(/\(/g,"%28").replace(/\)/g,"%29");
    //$("#export-dialog a#export-text")[0].href = "data:text/plain;charset="+(document.characterSet||document.charset)+";base64,"+Base64.encode(query,true);
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
    $("#export-dialog a#export-map-state").unbind("click").bind("click",function() {
      $('<div title="'+i18n.t("export.map_view.title")+'">'+
        '<h4>'+i18n.t("export.map_view.permalink")+'</h4>'+'<p><a href="//www.openstreetmap.org/#map='+ide.map.getZoom()+'/'+L.Util.formatNum(ide.map.getCenter().lat)+'/'+L.Util.formatNum(ide.map.getCenter().lng)+'" target="_blank">'+i18n.t("export.map_view.permalink_osm")+'</a></p>'+
        '<h4>'+i18n.t("export.map_view.center")+'</h4><p>'+L.Util.formatNum(ide.map.getCenter().lat)+', '+L.Util.formatNum(ide.map.getCenter().lng)+' <small>('+i18n.t("export.map_view.center_expl")+')</small></p>'+
        '<h4>'+i18n.t("export.map_view.bounds")+'</h4><p>'+L.Util.formatNum(ide.map.getBounds().getSouthWest().lat)+', '+L.Util.formatNum(ide.map.getBounds().getSouthWest().lng)+', '+L.Util.formatNum(ide.map.getBounds().getNorthEast().lat)+', '+L.Util.formatNum(ide.map.getBounds().getNorthEast().lng)+'<br /><small>('+i18n.t("export.map_view.bounds_expl")+')</small></p>'+
        (ide.map.bboxfilter.isEnabled() ?
          '<h4>'+i18n.t("export.map_view.bounds_selection")+'</h4><p>'+L.Util.formatNum(ide.map.bboxfilter.getBounds().getSouthWest().lat)+', '+L.Util.formatNum(ide.map.bboxfilter.getBounds().getSouthWest().lng)+', '+L.Util.formatNum(ide.map.bboxfilter.getBounds().getNorthEast().lat)+', '+L.Util.formatNum(ide.map.bboxfilter.getBounds().getNorthEast().lng)+'<br /><small>('+i18n.t("export.map_view.bounds_expl")+')</small></p>':
          ''
        ) +
        '<h4>'+i18n.t("export.map_view.zoom")+'</h4><p>'+ide.map.getZoom()+'</p>'+
        '</div>').dialog({
        modal:true,
        buttons: dialog_buttons,
      });
      return false;
    });
    $("#export-dialog a#export-image").unbind("click").on("click", function() {
      ide.onExportImageClick();
      $(this).parents('.ui-dialog-content').dialog('close');
      return false;
    });
    function constructGeojsonString(geojson) {
      var geoJSON_str;
      if (!geojson)
        geoJSON_str = i18n.t("export.geoJSON.no_data");
      else {
        console.log(new Date());
        var gJ = {
          type: "FeatureCollection",
          generator: configs.appname,
          copyright: overpass.copyright,
          timestamp: overpass.timestamp,
          //TODO: make own copy of features array (re-using geometry) instead of deep copy?
          features: _.clone(geojson.features, true), // makes deep copy
        }
        gJ.features.forEach(function(f) {
          var p = f.properties;
          f.id = p.type+"/"+p.id;
          f.properties = {
            "@id": f.id
          };
          for (var m in p.tags||{})
             // escapes tags beginning with an @ with another @
            f.properties[m.replace(/^@/,"@@")] = p.tags[m];
          for (var m in p.meta||{})
            f.properties["@"+m] = p.meta[m];
          // expose internal properties:
          // * tainted: indicates that the feature's geometry is incomplete
          if (p.tainted)
            f.properties["@tainted"] = p.tainted;
          // * geometry: indicates that the feature's geometry is approximated via the Overpass geometry types "center" or "bounds"
          if (p.geometry)
            f.properties["@geometry"] = p.geometry;
          // expose relation membership (complex data type)
          if (p.relations && p.relations.length > 0)
            f.properties["@relations"] = p.relations;
          // todo: expose way membership for nodes?
        });
        geoJSON_str = JSON.stringify(gJ, undefined, 2);
      }
      return geoJSON_str;
    }
    $("#export-dialog a#export-geoJSON").unbind("click").on("click", function() {
      var geoJSON_str = constructGeojsonString(overpass.geojson);
      var d = $("#export-geojson-dialog");
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
      d.dialog({
        modal:true,
        width:500,
        buttons: dialog_buttons,
      });
      $("textarea",d)[0].value=geoJSON_str;
      // make content downloadable as file
      if (overpass.geojson) {
        var blob = new Blob([geoJSON_str], {type: "application/json;charset=utf-8"});
        saveAs(blob, "export.geojson");
      }
      return false;
    });
    $("#export-dialog a#export-geoJSON-gist").unbind("click").on("click", function() {
      var geoJSON_str = constructGeojsonString(overpass.geojson);
      $.ajax("https://api.github.com/gists", {
        method: "POST",
        data: JSON.stringify({
          description: "data exported by overpass turbo", // todo:descr
          public: true,
          files: {
            "overpass.geojson": { // todo:name
              content: geoJSON_str
            }
          }
        })
      }).success(function(data,textStatus,jqXHR) {
        var dialog_buttons= {};
        dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
        $('<div title="'+i18n.t("export.geoJSON_gist.title")+'">'+
          '<p>'+i18n.t("export.geoJSON_gist.gist")+'&nbsp;<a href="'+data.html_url+'" target="_blank" class="external">'+data.id+'</a></p>'+
          '<p>'+i18n.t("export.geoJSON_gist.geojsonio")+'&nbsp;<a href="http://geojson.io/#id=gist:anonymous/'+data.id+'" target="_blank" class="external">'+i18n.t("export.geoJSON_gist.geojsonio_link")+'</a></p>'+
          '</div>').dialog({
          modal:true,
          buttons: dialog_buttons,
        });
        // data.html_url;
      }).error(function(jqXHR,textStatus,errorStr) {
        alert("an error occured during the creation of the overpass gist:\n"+JSON.stringify(jqXHR));
      });
      return false;
    });
    $("#export-dialog a#export-GPX").unbind("click").on("click", function() {
      var gpx_str;
      var geojson = overpass.geojson;
      if (!geojson)
        gpx_str = i18n.t("export.GPX.no_data");
      else {
        gpx_str = togpx(geojson, {
          creator: configs.appname,
          metadata: {
            "copyright": overpass.copyright,
            "desc": "Filtered OSM data converted to GPX by overpass turbo",
            "time": overpass.timestamp
          },
          featureTitle: function(props) {
            if (props.tags) {
              if (props.tags.name)
                return props.tags.name;
              if (props.tags.ref)
                return props.tags.ref;
              if (props.tags["addr:housenumber"] && props.tags["addr:street"])
                return props.tags["addr:street"] + " " + props.tags["addr:housenumber"];
            }
            return props.type + "/" + props.id;
          },
          //featureDescription: function(props) {},
          featureLink: function(props) {
            return "http://osm.org/browse/"+props.type+"/"+props.id;
          }
        });
      }
      var d = $("#export-gpx-dialog");
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
      d.dialog({
        modal:true,
        width:500,
        buttons: dialog_buttons,
      });
      $("textarea",d)[0].value=gpx_str;
      // make content downloadable as file
      if (geojson) {
        var blob = new Blob([gpx_str], {type: "application/xml;charset=utf-8"});
        saveAs(blob, "export.gpx");
      }
      return false;
    });
    $("#export-dialog a#export-KML").unbind("click").on("click", function() {
      var geojson = overpass.geojson && JSON.parse(constructGeojsonString(overpass.geojson));
      if (!geojson)
        kml_str = i18n.t("export.KML.no_data");
      else {
        var kml_str = tokml(geojson, {
          documentName: "overpass-turbo.eu export",
          documentDescription: "Filtered OSM data converted to KML by overpass turbo.\n"+
                               "Copyright: "+overpass.copyright+"\n"+
                               "Timestamp: "+overpass.timestamp,
          name: "name",
          description: "description"
        });
      }
      var d = $("#export-kml-dialog");
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
      d.dialog({
        modal:true,
        width:500,
        buttons: dialog_buttons,
      });
      $("textarea",d)[0].value=kml_str;
      // make content downloadable as file
      if (geojson) {
        var blob = new Blob([kml_str], {type: "application/xml;charset=utf-8"});
        saveAs(blob, "export.kml");
      }
      return false;
    });
    $("#export-dialog a#export-raw").unbind("click").on("click", function() {
      var raw_str, raw_type;
      var geojson = overpass.geojson;
      if (!geojson)
        raw_str = i18n.t("export.raw.no_data");
      else {
        var data = overpass.data;
        if (data instanceof XMLDocument) {
          raw_str = (new XMLSerializer()).serializeToString(data);
          raw_type = raw_str.match(/<osm/)?"osm":"xml";
        } else if (data instanceof Object) {
          raw_str = JSON.stringify(data, undefined, 2);
          raw_type = "json";
        } else {
          try {
            raw_str = data.toString();
          } catch(e) {
            raw_str = "Error while exporting the data";
          }
        }
      }
      var d = $("#export-raw-dialog");
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
      d.dialog({
        modal:true,
        width:500,
        buttons: dialog_buttons,
      });
      $("textarea",d)[0].value=raw_str;
      // make content downloadable as file
      if (geojson) {
        if (raw_type == "osm" || raw_type == "xml") {
          var blob = new Blob([raw_str], {type: "application/xml;charset=utf-8"});
          saveAs(blob, "export."+raw_type);
        } else if (raw_type == "json") {
          var blob = new Blob([raw_str], {type: "application/json;charset=utf-8"});
          saveAs(blob, "export.json");
        } else {
          var blob = new Blob([raw_str], {type: "application/octet-stream;charset=utf-8"});
          saveAs(blob, "export.dat");
        }
      }
      return false;
    });
    //$("#export-dialog a#export-convert-xml")[0].href = server+"convert?data="+encodeURIComponent(query)+"&target=xml";
    //$("#export-dialog a#export-convert-ql")[0].href = server+"convert?data="+encodeURIComponent(query)+"&target=mapql";
    //$("#export-dialog a#export-convert-compact")[0].href = server+"convert?data="+encodeURIComponent(query)+"&target=compact";

    // OSM editors
    // first check for possible mistakes in query.
    var validEditorQuery = turbo.autorepair.detect.editors(ide.getRawQuery(), ide.getQueryLang());
    // * Level0
    var exportToLevel0 = $("#export-dialog a#export-editors-level0");
    exportToLevel0.unbind("click");
    function constructLevel0Link(query) {
      return "http://level0.osmz.ru/?url="+
              encodeURIComponent(
                server+"interpreter?data="+encodeURIComponent(query)
              );
    }
//    if (validEditorQuery) {
//      exportToLevel0[0].href = constructLevel0Link(query);
//    } else {
//      exportToLevel0[0].href = "";
//      exportToLevel0.bind("click", function() {
//        var dialog_buttons= {};
//        dialog_buttons[i18n.t("dialog.repair_query")] = function() {
//          ide.repairQuery("xml+metadata");
//          var message_dialog = $(this);
//          ide.getQuery(function(query) {
//            exportToLevel0.unbind("click");
//            exportToLevel0[0].href = constructLevel0Link(query);
//            message_dialog.dialog("close");
//          });
//        };
//        dialog_buttons[i18n.t("dialog.continue_anyway")] = function() {
//          exportToLevel0.unbind("click");
//          exportToLevel0[0].href = constructLevel0Link(query);
//          $(this).dialog("close");
//        };
//        $('<div title="'+i18n.t("warning.incomplete.title")+'"><p>'+i18n.t("warning.incomplete.remote.expl.1")+'</p><p>'+i18n.t("warning.incomplete.remote.expl.2")+'</p></div>').dialog({
//          modal:true,
//          buttons: dialog_buttons,
//        });
//        return false;
//      });
//    }
    // * JOSM
    $("#export-dialog a#export-editors-josm").unbind("click").on("click", function() {
      var export_dialog = $(this).parents("div.ui-dialog-content").first();
      var send_to_josm = function(query) {
        var JRC_url="http://127.0.0.1:8111/";
        if (location.protocol === "https:") JRC_url = "https://127.0.0.1:8112/"
        $.getJSON(JRC_url+"version")
        .success(function(d,s,xhr) {
          if (d.protocolversion.major == 1) {
            $.get(JRC_url+"import", {
              url:
                // JOSM doesn't handle protocol-less links very well
                server.replace(/^\/\//,location.protocol+"//")+
                "interpreter?data="+
                encodeURIComponent(query),
            }).error(function(xhr,s,e) {
              alert("Error: Unexpected JOSM remote control error.");
            }).success(function(d,s,xhr) {
              console.log("successfully invoked JOSM remote constrol");
            });
          } else {
            var dialog_buttons= {};
            dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
            $('<div title="'+i18n.t("error.remote.title")+'"><p>'+i18n.t("error.remote.incompat")+': '+d.protocolversion.major+"."+d.protocolversion.minor+" :(</p></div>").dialog({
              modal:true,
              width:350,
              buttons: dialog_buttons,
            });
          }
        }).error(function(xhr,s,e) {
          var dialog_buttons= {};
          dialog_buttons[i18n.t("dialog.dismiss")] = function() {$(this).dialog("close");};
          $('<div title="'+i18n.t("error.remote.title")+'"><p>'+i18n.t("error.remote.not_found")+'</p></div>').dialog({
            modal:true,
            width:350,
            buttons: dialog_buttons,
          });
        });
      }
      // first check for possible mistakes in query.
      var valid = turbo.autorepair.detect.editors(ide.getRawQuery(), ide.getQueryLang());
      if (valid) {
        // now send the query to JOSM via remote control
        send_to_josm(query);
        return false;
      } else {
        var dialog_buttons= {};
        dialog_buttons[i18n.t("dialog.repair_query")] = function() {
          ide.repairQuery("xml+metadata");
          var message_dialog = $(this);
          ide.getQuery(function(query) {
            send_to_josm(query);
            message_dialog.dialog("close");
            export_dialog.dialog("close");
          });
        };
        dialog_buttons[i18n.t("dialog.continue_anyway")] = function() {
          send_to_josm(query);
          $(this).dialog("close");
          export_dialog.dialog("close");
        };
        $('<div title="'+i18n.t("warning.incomplete.title")+'"><p>'+i18n.t("warning.incomplete.remote.expl.1")+'</p><p>'+i18n.t("warning.incomplete.remote.expl.2")+'</p></div>').dialog({
          modal:true,
          buttons: dialog_buttons,
        });
        return false;
      }
    });
    // open the export dialog
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.done")] = function() {$(this).dialog("close");};
    $("#export-dialog").dialog({
      modal:true,
      width:350,
      buttons: dialog_buttons,
    });
    $("#export-dialog").accordion();
   });
  }
  this.onExportImageClick = function() {
    ide.waiter.open(i18n.t("waiter.export_as_image"));
    // 1. render canvas from map tiles
    // hide map controlls in this step :/
    // todo: also hide popups?
    ide.waiter.addInfo("prepare map");
    $("#map .leaflet-control-container .leaflet-top").hide();
    $("#data_stats").hide();
    if (settings.export_image_attribution) attribControl.addTo(ide.map);
    if (!settings.export_image_scale) scaleControl.removeFrom(ide.map);
    // try to use crossOrigin image loading. osm tiles should be served with the appropriate headers -> no need of bothering the proxy
    ide.waiter.addInfo("rendering map tiles");
    $("#map").html2canvas({
      useCORS: true,
      allowTaint: false,
      proxy: configs.html2canvas_use_proxy ? "/html2canvas_proxy/" : undefined, // use own proxy if necessary and available
    onrendered: function(canvas) {
      if (settings.export_image_attribution) attribControl.removeFrom(ide.map);
      if (!settings.export_image_scale) scaleControl.addTo(ide.map);
      if (settings.show_data_stats)
        $("#data_stats").show();
      $("#map .leaflet-control-container .leaflet-top").show();
      ide.waiter.addInfo("rendering map data");
      // 2. render overlay data onto canvas
      canvas.id = "render_canvas";
      var ctx = canvas.getContext("2d");
      // get geometry for svg rendering
      var height = $("#map .leaflet-overlay-pane svg").height();
      var width  = $("#map .leaflet-overlay-pane svg").width();
      var tmp = $("#map .leaflet-map-pane")[0].style.cssText.match(/.*?(-?\d+)px.*?(-?\d+)px.*/);
      var offx   = +tmp[1];
      var offy   = +tmp[2];
      if ($("#map .leaflet-overlay-pane").html().length > 0)
        ctx.drawSvg($("#map .leaflet-overlay-pane").html(),offx,offy,width,height);
      ide.waiter.addInfo("converting to png image");
      // 3. export canvas as html image
      var imgstr = canvas.toDataURL("image/png");
      var attrib_message = "";
      if (!settings.export_image_attribution)
        attrib_message = '<p style="font-size:smaller; color:orange;">Make sure to include proper attributions when distributing this image!</p>';
      var dialog_buttons= {};
      dialog_buttons[i18n.t("dialog.done")] = function() {
        $(this).dialog("close");
        // free dialog from DOM
        $("#export_image_dialog").remove();
      };
      $('<div title="'+i18n.t("export.image.title")+'" id="export_image_dialog"><p><img src="'+imgstr+'" alt="'+i18n.t("export.image.alt")+'" width="480px"/><br><!--<a href="'+imgstr+'" download="export.png" target="_blank">'+i18n.t("export.image.download")+'</a>--></p>'+attrib_message+'</div>').dialog({
        modal:true,
        width:500,
        position:["center",60],
        open: function() {
          // close progress indicator
          ide.waiter.close();
        },
        buttons: dialog_buttons,
      });
      canvas.toBlob(function(blob) {
        saveAs(blob, "export.png");
      });
    }});
  }
  this.onFfsClick = function() {
    $("#ffs-dialog #ffs-dialog-parse-error").hide();
    $("#ffs-dialog #ffs-dialog-typo").hide();
    var build_query = function(autorun) {
      // build query and run it immediately
      var ffs_result = ide.update_ffs_query();
      if (ffs_result === true) {
        $(this).dialog("close");
        if (autorun !== false)
          ide.onRunClick();
      } else {
        if (_.isArray(ffs_result)) {
          // show parse error message
          $("#ffs-dialog #ffs-dialog-parse-error").hide();
          $("#ffs-dialog #ffs-dialog-typo").show();
          var correction = ffs_result.join("");
          var correction_html = ffs_result.map(function(ffs_result_part,i) {
            if (i%2===1)
              return "<b>"+ffs_result_part+"</b>";
            else
              return ffs_result_part;
          }).join("");
          $("#ffs-dialog #ffs-dialog-typo-correction").html(correction_html);
          $("#ffs-dialog #ffs-dialog-typo-correction").unbind("click").bind("click", function(e) {
            $("#ffs-dialog input[type=text]").val(correction);
            $(this).parent().hide();
            e.preventDefault();
          });
          $("#ffs-dialog #ffs-dialog-typo").effect("shake", {direction:"right",distance:10,times:2}, 300);
        } else {
          // show parse error message
          $("#ffs-dialog #ffs-dialog-typo").hide();
          $("#ffs-dialog #ffs-dialog-parse-error").show();
          $("#ffs-dialog #ffs-dialog-parse-error").effect("shake", {direction:"right",distance:10,times:2}, 300);
        }
      }
    };
    $("#ffs-dialog input[type=text]").unbind("keypress").bind("keypress", function(e) {
      if (e.which==13 || e.which==10) {
        build_query.bind(this.parentElement.parentElement)();
        e.preventDefault();
      }
    });
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.wizard_build")] = function() { build_query.bind(this, false)(); }
    dialog_buttons[i18n.t("dialog.wizard_run")] = build_query;
    dialog_buttons[i18n.t("dialog.cancel")] = function() {$(this).dialog("close");};
    $("#ffs-dialog").dialog({
      modal:true,
      minWidth:350,
      buttons: dialog_buttons,
    });
  }
  this.onSettingsClick = function() {
    $("#settings-dialog input[name=ui_language]")[0].value = settings.ui_language;
    var lngDescs = i18n.getSupportedLanguagesDescriptions();
    make_combobox(
      $("#settings-dialog input[name=ui_language]"),
      (["auto"].concat(i18n.getSupportedLanguages())).map(function(lng) {
        return {
          value: lng,
          label: lng=="auto" ? "auto" : lng+' - '+lngDescs[lng]
        }
      })
    );
    $("#settings-dialog input[name=server]")[0].value = settings.server;
    make_combobox($("#settings-dialog input[name=server]"), configs.suggestedServers);
    $("#settings-dialog input[name=force_simple_cors_request]")[0].checked = settings.force_simple_cors_request;
    $("#settings-dialog input[name=no_autorepair]")[0].checked = settings.no_autorepair;
    // editor options
    $("#settings-dialog input[name=use_rich_editor]")[0].checked = settings.use_rich_editor;
    $("#settings-dialog input[name=editor_width]")[0].value = settings.editor_width;
    // sharing options
    $("#settings-dialog input[name=share_include_pos]")[0].checked = settings.share_include_pos;
    $("#settings-dialog input[name=share_compression]")[0].value = settings.share_compression;
    make_combobox($("#settings-dialog input[name=share_compression]"),["auto","on","off"]);
    // map settings
    $("#settings-dialog input[name=tile_server]")[0].value = settings.tile_server;
    make_combobox($("#settings-dialog input[name=tile_server]"), configs.suggestedTiles);
    $("#settings-dialog input[name=background_opacity]")[0].value = settings.background_opacity;
    $("#settings-dialog input[name=enable_crosshairs]")[0].checked = settings.enable_crosshairs;
    $("#settings-dialog input[name=disable_poiomatic]")[0].checked = settings.disable_poiomatic;
    $("#settings-dialog input[name=show_data_stats]")[0].checked = settings.show_data_stats;
    // export settings
    $("#settings-dialog input[name=export_image_scale]")[0].checked = settings.export_image_scale;
    $("#settings-dialog input[name=export_image_attribution]")[0].checked = settings.export_image_attribution;
    // open dialog
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.save")] = function() {
      // save settings
      var new_ui_language = $("#settings-dialog input[name=ui_language]")[0].value;
      // reload ui if language has been changed
      if (settings.ui_language != new_ui_language) {
        i18n.translate(new_ui_language);
        moment.locale(new_ui_language);
        ffs.invalidateCache();
      }
      settings.ui_language = new_ui_language;
      settings.server = $("#settings-dialog input[name=server]")[0].value;
      settings.force_simple_cors_request = $("#settings-dialog input[name=force_simple_cors_request]")[0].checked;
      settings.no_autorepair    = $("#settings-dialog input[name=no_autorepair]")[0].checked;
      settings.use_rich_editor  = $("#settings-dialog input[name=use_rich_editor]")[0].checked;
      var prev_editor_width = settings.editor_width;
      settings.editor_width     = $("#settings-dialog input[name=editor_width]")[0].value;
      // update editor width (if changed)
      if (prev_editor_width != settings.editor_width) {
        $("#editor").css("width",settings.editor_width);
        $("#dataviewer").css("left",settings.editor_width);
      }
      settings.share_include_pos = $("#settings-dialog input[name=share_include_pos]")[0].checked;
      settings.share_compression = $("#settings-dialog input[name=share_compression]")[0].value;
      var prev_tile_server = settings.tile_server;
      settings.tile_server = $("#settings-dialog input[name=tile_server]")[0].value;
      // update tile layer (if changed)
      if (prev_tile_server != settings.tile_server)
        ide.map.tile_layer.setUrl(settings.tile_server);
      var prev_background_opacity = settings.background_opacity;
      settings.background_opacity = +$("#settings-dialog input[name=background_opacity]")[0].value;
      // update background opacity layer
      if (settings.background_opacity != prev_background_opacity)
        if (settings.background_opacity == 1)
          ide.map.removeLayer(ide.map.inv_opacity_layer);
        else
          ide.map.inv_opacity_layer.setOpacity(1-settings.background_opacity).addTo(ide.map);
      settings.enable_crosshairs = $("#settings-dialog input[name=enable_crosshairs]")[0].checked;
      settings.disable_poiomatic = $("#settings-dialog input[name=disable_poiomatic]")[0].checked;
      settings.show_data_stats = $("#settings-dialog input[name=show_data_stats]")[0].checked;
      $(".crosshairs").toggle(settings.enable_crosshairs); // show/hide crosshairs
      settings.export_image_scale = $("#settings-dialog input[name=export_image_scale]")[0].checked;
      settings.export_image_attribution = $("#settings-dialog input[name=export_image_attribution]")[0].checked;
      settings.save();
      $(this).dialog("close");
    };
    $("#settings-dialog").dialog({
      modal:true,
      width:400,
      buttons: dialog_buttons,
    });
    $("#settings-dialog").accordion();
  }
  this.onHelpClick = function() {
    var dialog_buttons= {};
    dialog_buttons[i18n.t("dialog.close")] = function() {$(this).dialog("close");};
    $("#help-dialog").dialog({
      modal:false,
      width:450,
      buttons: dialog_buttons,
    });
    $("#help-dialog").accordion({heightStyle: "content"});
  }
  this.onKeyPress = function(event) {
    if ((event.which == 120 && event.charCode == 0) || // F9
        ((event.which == 13 || event.which == 10) && (event.ctrlKey || event.metaKey))) { // Ctrl+Enter
      ide.onRunClick(); // run query
      event.preventDefault();
    }
    if ((String.fromCharCode(event.which).toLowerCase() == 's') && (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey ) { // Ctrl+S
      ide.onSaveClick();
      event.preventDefault();
    }
    if ((String.fromCharCode(event.which).toLowerCase() == 'o') && (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey ) { // Ctrl+O
      ide.onLoadClick();
      event.preventDefault();
    }
    if ((String.fromCharCode(event.which).toLowerCase() == 'h') && (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey ) { // Ctrl+H
      ide.onHelpClick();
      event.preventDefault();
    }
    if (((String.fromCharCode(event.which).toLowerCase() == 'i') && (event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey ) || // Ctrl+I
        ((String.fromCharCode(event.which).toLowerCase() == 'f') && (event.ctrlKey || event.metaKey) &&  event.shiftKey && !event.altKey ) ) { // Ctrl+Shift+F
      ide.onFfsClick();
      event.preventDefault();
    }
    // todo: more shortcuts
  }
  this.update_map = function() {
    ide.waiter.open(i18n.t("waiter.processing_query"));
    ide.waiter.addInfo("resetting map");
    $("#data_stats").remove();
    // resets previously highlighted error lines
    this.resetErrors();
    // reset previously loaded data and overlay
    ide.dataViewer.setValue("");
    if (typeof overpass.osmLayer != "undefined")
      ide.map.removeLayer(overpass.osmLayer);
    $("#map_blank").remove();

    ide.waiter.addInfo("building query");
    // run the query via the overpass object
    ide.getQuery(function(query) {
      var query_lang = ide.getQueryLang();
      overpass.run_query(query,query_lang);
    });
  }
  this.update_ffs_query = function(s) {
    var search = s || $("#ffs-dialog #dropdown_select").val();
    query = ffs.construct_query(search);
    if (query === false) {
      var repaired = ffs.repair_search(search);
      if (repaired) {
        return repaired;
      } else {
        if (s) return false;
        // try to parse as generic ffs search
        return this.update_ffs_query('"'+search+'"');
      }
    }
    ide.setQuery(query);
    return true;
  }

})(); // end create ide object
