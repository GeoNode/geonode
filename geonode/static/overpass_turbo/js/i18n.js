// global i18n object

var i18n = new(function() {
  function browser_locale() {
    /* taken from https://github.com/maxogden/browser-locale by Max Ogden, BSD licensed */
    var lang
    
    if (navigator.languages) {
      // chrome does not currently set navigator.language correctly https://code.google.com/p/chromium/issues/detail?id=101138
      // but it does set the first element of navigator.languages correctly
      lang = navigator.languages[0]
    } else if (navigator.userLanguage) {
      // IE only
      lang = navigator.userLanguage
    } else {
      // as of this writing the latest version of firefox + safari set this correctly
      lang = navigator.language
    }
    
    return lang
  }

  var default_lng = "en";
  var languages = {
    // translations found in locale/*.json
    "en":    "English",
    "ca":    "Catalan",
    "da":    "Danish",
    "de":    "German",
    "el":    "Greek",
    "es":    "Spanish",
    "et":    "Estonian",
    "fr":    "French",
    "hr":    "Croatian",
    "it":    "Italian",
    "ja":    "Japanese",
    "nl":    "Dutch",
    "no":    "Norwegian",
    "pl":    "Polish",
    "pt-BR": "Portuguese (Brazil)",
    "ru":    "Russian",
    "sl":    "Slovenian",
    "uk":    "Ukrainian",
    "vi":    "Vietnamese",
    "zh-TW": "Chinese (Taiwan)"
  };
  var supported_lngs = _.keys(languages);
  this.getSupportedLanguages = function() {
    return supported_lngs;
  }
  this.getSupportedLanguagesDescriptions = function() {
    return languages;
  }
  this.getLanguage = function(lng) {
    lng = lng || settings.ui_language;
    if (lng == "auto") {
      // get user agent's language
      try {
        lng = browser_locale().toLowerCase();
      } catch(e) {}
      // hardcode some language fallbacks
      if (lng === "nb") lng = "no"; // Norwegian Bokmål
      // sanitize inconsistent use of lower and upper case spelling
      var parts;
      if (parts = lng.match(/(.*)-(.*)/))
        lng = parts[1]+'-'+parts[2].toUpperCase();
      // fall back to generic language file if no country-specific i18n is found
      if ($.inArray(lng,supported_lngs) == -1)
        lng = lng.replace(/-.*/,"");
    }
    return lng;
  }
  this.translate = function(lng) {
    lng = i18n.getLanguage(lng);

    if ($.inArray(lng,supported_lngs) == -1) {
      console.log("unsupported language: "+lng+" switching back to: "+default_lng);
      lng = default_lng;
    }

    // load language pack
    var lng_file = STATIC_FOLDER_URL+"locales/"+lng+".json";
    console.log(lng_file);
    try {
      $.ajax(lng_file,{async:false,dataType:"json"}).success(function(data){
        td = data;
        i18n.translate_ui();
        // todo: nicer implementation
      }).error(function(){
        console.log("failed to load language file: "+lng_file);
      });
    } catch(e) {
      console.log("failed to load language file: "+lng_file);
    }
  }
  this.translate_ui = function(element) {
    // if a DOM object is provided, only translate that one, otherwise
    // look for all object with the class "t"
    $(element || ".t").each(function(nr,element) {
      // get translation term(s)
      var terms = $(element).attr("data-t");
      terms = terms.split(";");
      for (var i=0; i<terms.length; i++) {
        var term = terms[i];
        var tmp = term.match(/^(\[(.*)\])?(.*)$/);
        var what = tmp[2];
        var key  = tmp[3];
        var val = i18n.t(key);
        if (what === "html") {
          $(element).html(val);
        } else if (what !== undefined) {
          $(element).attr(what,val);
        } else {
          $(element).text(val);
        }
      }
    });
  }
  this.t = function(key) {
    return td[key] || "/missing translation/";
  }

  // translated texts
  var td;
})(); // end create i18n object

