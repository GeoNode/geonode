/**
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Igor Vladyka <igor.vladyka@gmail.com> (https://github.com/Igor-Vladyka/leaflet.browser.print)
**/

/* Portrait mode sizes in mm for 0 lvl*/
L.Control.BrowserPrint.Size =  {
	A: {
		Width: 840,
		Height: 1188
	},
	B: {
		Width: 1000,
		Height: 1414
	}
};

L.Control.BrowserPrint.Mode = function(mode, title, pageSize, action, invalidateBounds) {
	if (!mode) {
		throw 'Print mode should be specified.';
	}

	this.Mode = mode;
	this.Title = title || mode;
	this.PageSize = (pageSize || 'A4').toUpperCase();
	this.PageSeries = this.PageSize[0];
	this.PageSeriesSize = parseInt(this.PageSize.substring(1));
	this.Action = action || function(context) { return context['_print' + mode]; };
	this.InvalidateBounds = invalidateBounds;
};

L.Control.BrowserPrint.Mode.Landscape = "Landscape";
L.Control.BrowserPrint.Mode.Portrait = "Portrait";
L.Control.BrowserPrint.Mode.Auto = "Auto";
L.Control.BrowserPrint.Mode.Custom = "Custom";

L.Control.BrowserPrint.Mode.prototype.getPageMargin = function(){
	var size = this.getPaperSize();
	return Math.floor((size.Width + size.Height) / 40) + 'mm';
};

L.Control.BrowserPrint.Mode.prototype.getPaperSize = function(){
	var series = L.Control.BrowserPrint.Size[this.PageSeries];
	var w = series.Width;
	var h = series.Height;
	var switchSides = false;
	if (this.PageSeriesSize) {
		switchSides = this.PageSeriesSize % 2 === 1;
		if (switchSides) {
			w = w / (this.PageSeriesSize - 1 || 1);
			h = h / (this.PageSeriesSize + 1);
		} else {
			w = w / this.PageSeriesSize;
			h = h / this.PageSeriesSize;
		}
	}

	return {
		Width: switchSides ? h : w,
		Height: switchSides ? w : h
	};
};

L.Control.BrowserPrint.Mode.prototype.getSize = function(){
	var size = this.getPaperSize();
	var margin = parseInt(this.getPageMargin());

	var calculateMargin = function(s) {
		if (margin) {
			return s - (margin * 2);
		}

		return s;
	}

	size.Width = Math.floor(calculateMargin(size.Width)) + 'mm';
	size.Height = Math.floor(calculateMargin(size.Height)) + 'mm';

	return size;
};

L.control.browserPrint.mode = function(mode, title, type, action, invalidateBounds){
	return new L.Control.BrowserPrint.Mode(mode, title, type, action, invalidateBounds);
}

L.control.browserPrint.mode.portrait = function(title, pageSize, action) {
	return L.control.browserPrint.mode(L.Control.BrowserPrint.Mode.Portrait, title, pageSize, action, false);
};

L.control.browserPrint.mode.landscape = function(title, pageSize, action) {
	return L.control.browserPrint.mode(L.Control.BrowserPrint.Mode.Landscape, title, pageSize, action, false);
};

L.control.browserPrint.mode.auto = function(title, pageSize, action) {
	return L.control.browserPrint.mode(L.Control.BrowserPrint.Mode.Auto, title, pageSize, action, true);
};

L.control.browserPrint.mode.custom = function(title, pageSize, action) {
	return L.control.browserPrint.mode(L.Control.BrowserPrint.Mode.Custom, title, pageSize, action, true);
};
