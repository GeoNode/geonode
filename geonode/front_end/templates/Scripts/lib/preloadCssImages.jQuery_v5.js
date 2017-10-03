/**
 * jQuery-Plugin "preloadCssImages"
 * by Scott Jehl, scott@filamentgroup.com
 * http://www.filamentgroup.com
 * reference article: http://www.filamentgroup.com/lab/update_automatically_preload_images_from_css_with_jquery/
 * demo page: http://www.filamentgroup.com/examples/preloadImages/index_v2.php
 * 
 * Copyright (c) 2008 Filament Group, Inc
 * Dual licensed under the MIT (filamentgroup.com/examples/mit-license.txt) and GPL (filamentgroup.com/examples/gpl-license.txt) licenses.
 *
 * Version: 5.0, 10.31.2008
 * Changelog:
 * 	02.20.2008 initial Version 1.0
 *    06.04.2008 Version 2.0 : removed need for any passed arguments. Images load from any and all directories.
 *    06.21.2008 Version 3.0 : Added options for loading status. Fixed IE abs image path bug (thanks Sam Pohlenz).
 *    07.24.2008 Version 4.0 : Added support for @imported CSS (credit: http://marcarea.com/). Fixed support in Opera as well. 
 *    10.31.2008 Version: 5.0 : Many feature and performance enhancements from trixta
 * --------------------------------------------------------------------
 */

;jQuery.preloadCssImages = function(settings){
	settings = jQuery.extend({
		statusTextEl: null,
		statusBarEl: null,
		errorDelay: 999, // handles 404-Errors in IE
		simultaneousCacheLoading: 2
	}, settings);
	var allImgs = [],
		loaded = 0,
		imgUrls = [],
		thisSheetRules,	
		errorTimer;
	
	function onImgComplete(){
		clearTimeout(errorTimer);
		if (imgUrls && imgUrls.length && imgUrls[loaded]) {
			loaded++;
			if (settings.statusTextEl) {
				var nowloading = (imgUrls[loaded]) ? 
					'Now Loading: <span>' + imgUrls[loaded].split('/')[imgUrls[loaded].split('/').length - 1] : 
					'Loading complete'; // wrong status-text bug fixed
				jQuery(settings.statusTextEl).html('<span class="numLoaded">' + loaded + '</span> of <span class="numTotal">' + imgUrls.length + '</span> loaded (<span class="percentLoaded">' + (loaded / imgUrls.length * 100).toFixed(0) + '%</span>) <span class="currentImg">' + nowloading + '</span></span>');
			}
			if (settings.statusBarEl) {
				var barWidth = jQuery(settings.statusBarEl).width();
				jQuery(settings.statusBarEl).css('background-position', -(barWidth - (barWidth * loaded / imgUrls.length).toFixed(0)) + 'px 50%');
			}
			loadImgs();
		}
	}
	
	function loadImgs(){
		//only load 1 image at the same time / most browsers can only handle 2 http requests, 1 should remain for user-interaction (Ajax, other images, normal page requests...)
		// otherwise set simultaneousCacheLoading to a higher number for simultaneous downloads
		if(imgUrls && imgUrls.length && imgUrls[loaded]){
			var img = new Image(); //new img obj
			img.src = imgUrls[loaded];	//set src either absolute or rel to css dir
			if(!img.complete){
				jQuery(img).bind('error load onreadystatechange', onImgComplete);
			} else {
				onImgComplete();
			}
			errorTimer = setTimeout(onImgComplete, settings.errorDelay); // handles 404-Errors in IE
		}
	}
	
	function parseCSS(sheets, urls) {
		var w3cImport = false,
			imported = [],
			importedSrc = [],
			baseURL;
		var sheetIndex = sheets.length;
		while(sheetIndex--){//loop through each stylesheet
			
			var cssPile = '';//create large string of all css rules in sheet
			
			if(urls && urls[sheetIndex]){
				baseURL = urls[sheetIndex];
			} else {
				var csshref = (sheets[sheetIndex].href) ? sheets[sheetIndex].href : 'window.location.href';
				var baseURLarr = csshref.split('/');//split href at / to make array
				baseURLarr.pop();//remove file path from baseURL array
				baseURL = baseURLarr.join('/');//create base url for the images in this sheet (css file's dir)
				if (baseURL) {
					baseURL += '/'; //tack on a / if needed
				}
			}
			if(sheets[sheetIndex].cssRules || sheets[sheetIndex].rules){
				thisSheetRules = (sheets[sheetIndex].cssRules) ? //->>> http://www.quirksmode.org/dom/w3c_css.html
					sheets[sheetIndex].cssRules : //w3
					sheets[sheetIndex].rules; //ie 
				var ruleIndex = thisSheetRules.length;
				while(ruleIndex--){
					if(thisSheetRules[ruleIndex].style && thisSheetRules[ruleIndex].style.cssText){
						var text = thisSheetRules[ruleIndex].style.cssText;
						if(text.toLowerCase().indexOf('url') != -1){ // only add rules to the string if you can assume, to find an image, speed improvement
							cssPile += text; // thisSheetRules[ruleIndex].style.cssText instead of thisSheetRules[ruleIndex].cssText is a huge speed improvement
						}
					} else if(thisSheetRules[ruleIndex].styleSheet) {
						imported.push(thisSheetRules[ruleIndex].styleSheet);
						w3cImport = true;
					}
					
				}
			}
			//parse cssPile for image urls
			var tmpImage = cssPile.match(/[^\("]+\.(gif|jpg|jpeg|png)/g);//reg ex to get a string of between a "(" and a ".filename" / '"' for opera-bugfix
			if(tmpImage){
				var i = tmpImage.length;
				while(i--){ // handle baseUrl here for multiple stylesheets in different folders bug
					var imgSrc = (tmpImage[i].charAt(0) == '/' || tmpImage[i].match('://')) ? // protocol-bug fixed
						tmpImage[i] : 
						baseURL + tmpImage[i];
					
					if(jQuery.inArray(imgSrc, imgUrls) == -1){
						imgUrls.push(imgSrc);
					}
				}
			}
			
			if(!w3cImport && sheets[sheetIndex].imports && sheets[sheetIndex].imports.length) {
				for(var iImport = 0, importLen = sheets[sheetIndex].imports.length; iImport < importLen; iImport++){
					var iHref = sheets[sheetIndex].imports[iImport].href;
					iHref = iHref.split('/');
					iHref.pop();
					iHref = iHref.join('/');
					if (iHref) {
						iHref += '/'; //tack on a / if needed
					}
					var iSrc = (iHref.charAt(0) == '/' || iHref.match('://')) ? // protocol-bug fixed
						iHref : 
						baseURL + iHref;
					
					importedSrc.push(iSrc);
					imported.push(sheets[sheetIndex].imports[iImport]);
				}
				
				
			}
		}//loop
		if(imported.length){
			parseCSS(imported, importedSrc);
			return false;
		}
		var downloads = settings.simultaneousCacheLoading;
		while( downloads--){
			setTimeout(loadImgs, downloads);
		}
	}
	parseCSS(document.styleSheets);
	return imgUrls;
};