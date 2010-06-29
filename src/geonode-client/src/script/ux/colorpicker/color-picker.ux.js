// Create user extensions namespace (Ext.ux)
Ext.namespace('Ext.ux');

/**
 * Ext.ux.ColorPicker Extension Class for ExtJs 2.0
 *
 * @author Amon
 * @version 2.0
 *
 * Webpage: http://colorpicker.theba.hu
 *
 * @class Ext.ux.ColorPicker
 * @extends Ext.util.Observable
 * @constructor
 * Creates new ColorPicker
 * @param {Object} config Config Object
 * @cfg {Boolean} hidePanel true to hide the inputs (defaults to false)
 * @cfg {Boolean/Object} animate Moving pickers with this animate or false to no animation (defaults to false)
 * @cfg {Object} rgb (optional) Add initial color with rgb format eg.: { r:255, g:128, b:10 }
 * @cfg {Object} hsv (optional) Add initial color with hsv format eg.: { h:100, s:60, v:50 }
 * @cfg {String} color (optional) Add initial color with hexa format eg.: 'A3CF6D'
 * @cfg {Object} pickerHotPoint (optional) If you change the picker image, you can change the point of pick. ( defaults to { x:3, y:3 } )
 * @cfg {Object} captions labels of inputs (defaults to { red: 'R', green: 'G', blue: 'B', hue: 'H°', saturation: 'S%', brightness: 'V%', hexa: 'Color', websafe: 'Websafe' })
 */
Ext.ux.ColorPicker = function( config ) {
    config.bodyStyle = {'padding':'3px'};
    Ext.ux.ColorPicker.superclass.constructor.call( this, config );
    this.initialize( config );
}
// extend Ext.ux.ColorPicker with Ext.util.Observable
Ext.extend(Ext.ux.ColorPicker, Ext.util.Observable, {

    // help for convert hexa
    HCHARS: '0123456789ABCDEF',

    // initialization
    initialize: function( config ) {
        this.events = {};
        this.config = this.config || config;
        this.config.captions = this.config.captions || {};
        this.config.pickerHotPoint = this.config.pickerHotPoint || { x:3, y:3 };
        this._HSV = { h: 0, s: 100, v: 100 };
        this._RGB = { r: 255, g: 255, b: 255 };
        this._HEX = '000000';
        this.lastXYRgb = { x: 0, y: 0 };
        this.lastYHue = 0;
        this.domElement = this.config.renderTo || Ext.DomHelper.append( document.body, {}, true );
        this.domElement.addClass( 'x-cp-panel' );
        this.cpCreateDomObjects();
        if( this.config.hidePanel ) { this.formContainer.hide(); }
        // init internal events
        this.rgbPicker.on( 'mousedown', this.rgbPickerClick.createDelegate( this ), this );
        this.huePicker.on( 'mousedown', this.huePickerClick.createDelegate( this ), this );
        this.wsColorContainer.on( 'mousedown', this.setColorFromWebsafe.createDelegate( this ), this );
        this.inColorContainer.on( 'mousedown', this.setColorFromInvert.createDelegate( this ), this );
        Ext.getCmp( 'redValue' + this.domElement.id ).on( 'change', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'greenValue' + this.domElement.id ).on( 'change', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'blueValue' + this.domElement.id ).on( 'change', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'hueValue' + this.domElement.id ).on( 'change', this.changeHSVField.createDelegate( this ) );
        Ext.getCmp( 'saturationValue' + this.domElement.id ).on( 'change', this.changeHSVField.createDelegate( this ) );
        Ext.getCmp( 'brightnessValue' + this.domElement.id ).on( 'change', this.changeHSVField.createDelegate( this ) );
        Ext.getCmp( 'colorValue' + this.domElement.id ).on( 'change', this.changeHexaField.createDelegate( this ) );

        Ext.getCmp( 'redValue' + this.domElement.id ).on( 'specialkey', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'greenValue' + this.domElement.id ).on( 'specialkey', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'blueValue' + this.domElement.id ).on( 'specialkey', this.changeRGBField.createDelegate( this ) );
        Ext.getCmp( 'hueValue' + this.domElement.id ).on( 'specialkey', this.changeHSVField.createDelegate( this ) );
        Ext.getCmp( 'saturationValue' + this.domElement.id ).on( 'specialkey', this.changeHSVField.createDelegate( this ) );
        Ext.getCmp( 'brightnessValue' + this.domElement.id ).on( 'specialkey', this.changeHSVField.createDelegate( this ) );

        // let the user hit enter or tab away when they are changing the color field
        Ext.getCmp( 'colorValue' + this.domElement.id ).on({
            'specialkey': function(field, evt) {
                if (evt.getKey() === evt.ENTER) {
                    this.changeHexaField(field, field.getValue());                    
                }
            }, 
            scope: this
        });

        // initial color check
        this.checkConfig();
        // register events
        this.addEvents({
            /**
             * @event pickcolor
             * Fires when a new color selected
             * @param {Ext.util.ColorPicker} this
             * @param {String} color
             */
            pickcolor: true,
            /**
             * @event changergb
             * Fires when change rgb input
             * @param {Ext.util.ColorPicker} this
             * @param {Object} color ({ r: redvalue, g: greenvalue, b: bluevalue })
             */
            changergb: true,
            /**
             * @event changehsv
             * Fires when change hsv input
             * @param {Ext.util.ColorPicker} this
             * @param {Object} color ({ h: huevalue, s: saturationvalue, v: brightnessvalue })
             */
            changehsv: true,
            /**
             * @event changehexa
             * Fires when change hexa input
             * @param {Ext.util.ColorPicker} this
             * @param {String} color
             */
            changehexa: true
        });
    },
    // create internal DOM objects
    cpCreateDomObjects: function() {
        this.rgbPicker = Ext.DomHelper.append( this.domElement, {
            tag: 'div',
            cls: 'x-cp-rgb-msk'
        }, true );
        this.rgbPointer = Ext.DomHelper.append( this.rgbPicker, {
            tag: 'div',
            cls: 'x-cp-rgb-picker'
        }, true );
        this.rgbPointer.setXY( [ this.rgbPicker.getLeft()-this.config.pickerHotPoint.x, this.rgbPicker.getTop()-this.config.pickerHotPoint.y ] );
        this.huePicker = Ext.DomHelper.append( this.domElement, {
            tag: 'div',
            cls: 'x-cp-hue-msk'
        }, true );
        this.huePointer = Ext.DomHelper.append( this.huePicker, {
            tag: 'div',
            cls: 'x-cp-hue-picker'
        }, true );
        this.huePointer.setXY( [ this.huePicker.getLeft()+(this.huePointer.getWidth() / 2)+1, this.huePicker.getTop()-this.config.pickerHotPoint.y ] );
        this.formContainer = Ext.DomHelper.append( Ext.DomHelper.append( this.domElement, {
            tag: 'div',
            cls: 'x-cp-control-container x-unselectable'
        }, true ), {
            tag: 'div',
            cls: 'x-cp-rgb-container x-unselectable',
            style: 'clear:both'
        }, true );
        this.colorContainer = Ext.DomHelper.append( this.formContainer, {
            cls: 'x-cp-coloro-container x-unselectable'
        }, true ).update( this.config.captions.color || 'Color' );
        this.form = new Ext.FormPanel({
            frame:true,
            width: 'auto',
            height: 227,
            cls: 'x-cp-form',
            labelWidth: 12,
            items: [{
                xtype:'fieldset',
                title: 'RGB',
                autoHeight:true,
                style: 'padding: 2px',
                defaultType: 'numberfield',
                items :[{
                        fieldLabel: 'Red',
                        id: 'redValue' + this.domElement.id
                    },{
                        fieldLabel: 'Green',
                        id: 'greenValue' + this.domElement.id
                    },{
                        fieldLabel: 'Blue',
                        id: 'blueValue' + this.domElement.id
                    }
                ]
            },{
                xtype:'fieldset',
                title: 'HSV',
                autoHeight:true,
                style: 'padding: 2px',
                defaultType: 'numberfield',
                items :[{
                        fieldLabel: 'Hue',
                        id: 'hueValue' + this.domElement.id
                    },{
                        fieldLabel: 'Satur.',
                        id: 'saturationValue' + this.domElement.id
                    },{
                        fieldLabel: 'Bright.',
                        id: 'brightnessValue' + this.domElement.id
                    }
                ]
            },{
                xtype:'fieldset',
                title: 'Color',
                autoHeight:true,
                style: 'padding: 2px',
                defaultType: 'textfield',
                items :[{
                        fieldLabel: 'Color',
                        id: 'colorValue' + this.domElement.id
                    }
                ]
            }]
        });

        this.form.render(this.formContainer);
        var temp = Ext.DomHelper.append( this.form.body, {
            cls: 'x-cp-colors-container x-unselectable'
        }, true);
        this.wsColorContainer = Ext.DomHelper.append( temp, {
            cls: 'x-cp-color-container x-unselectable'
        }, true ).update( this.config.captions.websafe || 'Websafe' );
        this.inColorContainer = Ext.DomHelper.append( temp, {
            cls: 'x-cp-color-container x-unselectable'
        }, true ).update( this.config.captions.inverse || 'Inverse' );
        Ext.DomHelper.append( temp, { tag: 'div', style: 'height:0px;border:none;clear:both;font-size:1px;' });
        this.form.render( this.formContainer );
        Ext.DomHelper.append( this.domElement, { tag: 'div', style: 'height:0px;border:none;clear:both;font-size:1px;' });
    },
    /**
     * Convert a float to decimal
     * @param {Float} n
     * @return {Integer}
     */
    realToDec: function( n ) {
        return Math.min( 255, Math.round( n * 256 ) );
    },
    /**
     * Convert HSV color format to RGB color format
     * @param {Integer/Array( h, s, v )} h
     * @param {Integer} s (optional)
     * @param {Integer} v (optional)
     * @return {Array}
     */
    hsvToRgb: function( h, s, v ) {
        if( h instanceof Array ) { return this.hsvToRgb.call( this, h[0], h[1], h[2] ); }
        var r, g, b, i, f, p, q, t;
        i = Math.floor( ( h / 60 ) % 6 );
        f = ( h / 60 ) - i;
        p = v * ( 1 - s );
        q = v * ( 1 - f * s );
        t = v * ( 1 - ( 1 - f ) * s );
        switch(i) {
            case 0: r=v; g=t; b=p; break;
            case 1: r=q; g=v; b=p; break;
            case 2: r=p; g=v; b=t; break;
            case 3: r=p; g=q; b=v; break;
            case 4: r=t; g=p; b=v; break;
            case 5: r=v; g=p; b=q; break;
        }
        return [this.realToDec( r ), this.realToDec( g ), this.realToDec( b )];
    },
    /**
     * Convert RGB color format to HSV color format
     * @param {Integer/Array( r, g, b )} r
     * @param {Integer} g (optional)
     * @param {Integer} b (optional)
     * @return {Array}
     */
    rgbToHsv: function( r, g, b ) {
        if( r instanceof Array ) { return this.rgbToHsv.call( this, r[0], r[1], r[2] ); }
        r = r / 255;
        g = g / 255;
        b = b / 255;
        var min, max, delta, h, s, v;
        min = Math.min( Math.min( r, g ), b );
        max = Math.max( Math.max( r, g ), b );
        delta = max - min;
        switch (max) {
            case min: h = 0; break;
            case r:   h = 60 * ( g - b ) / delta;
                      if ( g < b ) { h += 360; }
                      break;
            case g:   h = ( 60 * ( b - r ) / delta ) + 120; break;
            case b:   h = ( 60 * ( r - g ) / delta ) + 240; break;
        }
        s = ( max === 0 ) ? 0 : 1 - ( min / max );
        return [Math.round( h ), s, max];
    },
    /**
     * Convert RGB color format to Hexa color format
     * @param {Integer/Array( r, g, b )} r
     * @param {Integer} g (optional)
     * @param {Integer} b (optional)
     * @return {String}
     */
    rgbToHex: function( r, g, b ) {
        if( r instanceof Array ) { return this.rgbToHex.call( this, r[0], r[1], r[2] ); }
        return this.decToHex( r ) + this.decToHex( g ) + this.decToHex( b );
    },
    /**
     * Convert an integer to hexa
     * @param {Integer} n
     * @return {String}
     */
    decToHex: function( n ) {
        n = parseInt(n, 10);
        n = ( !isNaN( n )) ? n : 0;
        n = (n > 255 || n < 0) ? 0 : n;
        return this.HCHARS.charAt( ( n - n % 16 ) / 16 ) + this.HCHARS.charAt( n % 16 );
    },
    /**
     * Return with position of a character in this.HCHARS string
     * @private
     * @param {Char} c
     * @return {Integer}
     */
    getHCharPos: function( c ) {
        return this.HCHARS.indexOf( c.toUpperCase() );
    },
    /**
     * Convert a hexa string to decimal
     * @param {String} hex
     * @return {Integer}
     */
    hexToDec: function( hex ) {
        var s = hex.split('');
        return ( ( this.getHCharPos( s[0] ) * 16 ) + this.getHCharPos( s[1] ) );
    },
    /**
     * Convert a hexa string to RGB color format
     * @param {String} hex
     * @return {Array}
     */
    hexToRgb: function( hex ) {
        return [ this.hexToDec( hex.substr(0, 2) ), this.hexToDec( hex.substr(2, 2) ), this.hexToDec( hex.substr(4, 2) ) ];
    },
    /**
     * Not documented yet
     */
    checkSafeNumber: function( v ) {
        if ( !isNaN( v ) ) {
            v = Math.min( Math.max( 0, v ), 255 );
            var i, next;
            for( i=0; i<256; i=i+51 ) {
                next = i + 51;
                if ( v>=i && v<=next ) { return ( v - i > 25 ) ? next : i; }
            }
        }
        return v;
    },
    /**
     * Not documented yet
     */
    websafe: function( r, g, b ) {
        if( r instanceof Array ) { return this.websafe.call( this, r[0], r[1], r[2] ); }
        return [this.checkSafeNumber( r ), this.checkSafeNumber( g ), this.checkSafeNumber( b )];
    },
    /**
     * Not documented yet
     */
    invert: function( r, g, b ) {
        if( r instanceof Array ) { return this.invert.call( this, r[0], r[1], r[2] ); }
        return [255-r,255-g,255-b];
    },
    /**
     * Convert Y coordinate to HUE value
     * @private
     * @param {Integer} y
     * @return {Integer}
     */
    getHue: function( y ) {
        var hue = 360 - Math.round( ( ( this.huePicker.getHeight() - y ) / this.huePicker.getHeight() ) * 360 );
        return hue === 360 ? 0 : hue;
    },
    /**
     * Convert HUE value to Y coordinate
     * @private
     * @param {Integer} hue
     * @return {Integer}
     */
    getHPos: function( hue ) {
        //return this.huePicker.getHeight() - ( ( hue * this.huePicker.getHeight() ) / 360 );
        return hue * ( this.huePicker.getHeight() / 360 );
    },
    /**
     * Convert X coordinate to Saturation value
     * @private
     * @param {Integer} x
     * @return {Integer}
     */
    getSaturation: function( x ) {
        return x / this.rgbPicker.getWidth();
    },
    /**
     * Convert Saturation value to Y coordinate
     * @private
     * @param {Integer} saturation
     * @return {Integer}
     */
    getSPos: function( saturation ) {
        return saturation * this.rgbPicker.getWidth();
    },
    /**
     * Convert Y coordinate to Brightness value
     * @private
     * @param {Integer} y
     * @return {Integer}
     */
    getValue: function( y ) {
        return ( this.rgbPicker.getHeight() - y ) / this.rgbPicker.getHeight();
    },
    /**
     * Convert Brightness value to Y coordinate
     * @private
     * @param {Integer} value
     * @return {Integer}
     */
    getVPos: function( value ) {
        return this.rgbPicker.getHeight() - ( value * this.rgbPicker.getHeight() );
    },
    /**
     * Update colors from the position of picker
     */
    updateColorsFromRGBPicker: function() {
        this._HSV = { h: this._HSV.h, s: this.getSaturation( this.lastXYRgb.x ), v: this.getValue( this.lastXYRgb.y ) };
    },
    /**
     * Update colors from the position of HUE picker
     */
    updateColorsFromHUEPicker: function() {
        this._HSV.h = this.getHue( this.lastYHue );
        var temp = this.hsvToRgb( this._HSV.h, 1, 1 );
        temp =  this.rgbToHex( temp[0], temp[1], temp[2] );
        this.rgbPicker.setStyle( { backgroundColor: '#' + temp } );
    },
    /**
     * Update colors from RGB input fields
     */
    updateColorsFromRGBFields: function() {
        var temp = this.rgbToHsv( Ext.getCmp( 'redValue' + this.domElement.id ).getValue(), Ext.getCmp( 'greenValue' + this.domElement.id ).getValue(), Ext.getCmp( 'blueValue' + this.domElement.id ).getValue() );
        this._HSV = { h: temp[0], s: temp[1], v: temp[2] };
    },
    /**
     * Update colors from HEXA input fields
     */
    updateColorsFromHexaField: function() {
        var temp = this.hexToRgb( this._HEX );
        this._RGB = { r: temp[0], g: temp[1], b: temp[2] };
        temp = this.rgbToHsv( temp[0], temp[1], temp[2] );
        this._HSV = { h: temp[0], s: temp[1], v: temp[2] };
    },
    /**
     * Update colors from HSV input fields
     */
    updateColorsFromHSVFields: function() {
        var temp = this.hsvToRgb( this._HSV.h, this._HSV.s, this._HSV.v );
        this._RGB = { r: temp[0], g: temp[1], b: temp[2] };
    },
    /**
     * Update RGB color from HSV color
     */
    updateRGBFromHSV: function() {
        var temp = this.hsvToRgb( this._HSV.h, this._HSV.s, this._HSV.v );
        this._RGB = { r: temp[0], g: temp[1], b: temp[2] };
    },
    /**
     * Update all inputs from internal color
     */
    updateInputFields: function() {
        Ext.getCmp( 'redValue' + this.domElement.id ).setValue( this._RGB.r );
        Ext.getCmp( 'greenValue' + this.domElement.id ).setValue( this._RGB.g );
        Ext.getCmp( 'blueValue' + this.domElement.id ).setValue( this._RGB.b );
        Ext.getCmp( 'hueValue' + this.domElement.id ).setValue( this._HSV.h );
        Ext.getCmp( 'saturationValue' + this.domElement.id ).setValue( Math.round( this._HSV.s * 100 ) );
        Ext.getCmp( 'brightnessValue' + this.domElement.id ).setValue( Math.round( this._HSV.v * 100 ) );
        Ext.getCmp( 'colorValue' + this.domElement.id ).setValue( this._HEX );
    },
    /**
     * Update color container
     */
    updateColor: function() {
        // update hexa
        this._HEX = this.rgbToHex( this._RGB.r, this._RGB.g, this._RGB.b );
        // update color container
        this.colorContainer.setStyle( { backgroundColor: '#'+this._HEX } );
        this.colorContainer.set({ title: '#'+this._HEX });
        // update websafe color
        var temp = this.rgbToHex( this.websafe( this._RGB.r, this._RGB.g, this._RGB.b ) );
        this.wsColorContainer.setStyle( { backgroundColor: '#'+temp } );
        this.wsColorContainer.set({ title: '#'+temp });
        this.wsColorContainer.setStyle( { color: '#'+this.rgbToHex( this.invert( this.websafe( this._RGB.r, this._RGB.g, this._RGB.b ) ) ) } );
        // update invert color
        var temp = this.rgbToHex( this.invert( this._RGB.r, this._RGB.g, this._RGB.b ) );
        this.inColorContainer.setStyle( { backgroundColor: '#'+temp } );
        this.inColorContainer.setStyle( { color: '#'+this._HEX } );
        this.inColorContainer.set({ title: '#'+temp });
        this.colorContainer.setStyle( { color: '#'+temp } );
        // update input boxes
        this.updateInputFields();
        // fire the pickcolor event
        this.fireEvent( 'pickcolor', this, this._HEX );
    },
    /**
     * Update position of both picker from the internal color
     */
    updatePickers: function() {
        this.lastXYRgb = { x: this.getSPos( this._HSV.s ), y: this.getVPos( this._HSV.v ) };
        this.rgbPointer.setXY( [this.lastXYRgb.x-this.config.pickerHotPoint.x + this.rgbPicker.getLeft(), this.lastXYRgb.y-this.config.pickerHotPoint.y+this.rgbPicker.getTop()], this.config.animate );
        this.lastYHue = this.getHPos( this._HSV.h );
        this.huePointer.setXY( [this.huePicker.getLeft()+(this.huePointer.getWidth() / 2)+1, this.lastYHue + this.huePicker.getTop()-this.config.pickerHotPoint.y ], this.config.animate );
        var temp = this.hsvToRgb( this._HSV.h, 1, 1 );
        temp =  this.rgbToHex( temp[0], temp[1], temp[2] );
        this.rgbPicker.setStyle( { backgroundColor: '#' + temp } );
    },
    /**
     * Internal event
     * Catch the RGB picker click
     */
    rgbPickerClick: function( event, cp ) {
        this.lastXYRgb = { x: event.getPageX() - this.rgbPicker.getLeft(), y: event.getPageY() - this.rgbPicker.getTop() };
        this.rgbPointer.setXY( [event.getPageX()-this.config.pickerHotPoint.x, event.getPageY()-this.config.pickerHotPoint.y], this.config.animate );
        this.updateColorsFromRGBPicker();
        this.updateRGBFromHSV();
        this.updateColor();
    },
    /**
     * Internal event
     * Catch the HUE picker click
     */
    huePickerClick: function( event, cp ) {
        this.lastYHue = event.getPageY() - this.huePicker.getTop();
        this.huePointer.setY( [event.getPageY()-3], this.config.animate );
        this.updateColorsFromHUEPicker();
        this.updateRGBFromHSV();
        this.updateColor();
    },
    /**
     * Internal event
     * Catch the change event of RGB input fields
     */
    changeRGBField: function( element, newValue, oldValue ) {
        if( !(newValue instanceof String) ) { newValue = element.getValue(); }
        if( newValue < 0 ) { newValue = 0; }
        if( newValue > 255 ) { newValue = 255; }

        if( element == Ext.getCmp( 'redValue' + this.domElement.id ) ) { this._RGB.r = newValue; }
        else if( element == Ext.getCmp( 'greenValue' + this.domElement.id ) ) { this._RGB.g = newValue; }
        else if( element == Ext.getCmp( 'blueValue' + this.domElement.id ) ) { this._RGB.b = newValue; }
        this.updateColorsFromRGBFields();
        this.updateColor();
        this.updatePickers();
        // fire the changergb event
        this.fireEvent( 'changergb', this, this._RGB );
    },
    /**
     * Internal event
     * Catch the change event of HSV input fields
     */
    changeHSVField: function( element, newValue, oldValue ) {
        if( !(newValue instanceof String) ) { newValue = element.getValue(); }
        if( element == Ext.getCmp( 'hueValue' + this.domElement.id ) ) {
            if( newValue < 0 ) { newValue = 0; }
            if( newValue > 360 ) { newValue = 360; }
            this._HSV.h = newValue;
        } else {
            if( newValue < 0 ) { newValue = 0; }
            if( newValue > 100 ) { newValue = 100; }
            if( element == Ext.getCmp( 'saturationValue' + this.domElement.id ) ) { this._HSV.s = ( newValue / 100 ); }
            else if( element == Ext.getCmp( 'brightnessValue' + this.domElement.id ) ) { this._HSV.v = ( newValue / 100 ); }
        }
        this.updateColorsFromHSVFields();
        this.updateColor();
        this.updatePickers();
        // fire the changehsv event
        this.fireEvent( 'changehsv', this, this._HSV );
    },
    /**
     * Internal event
     * Catch the change event of HEXA input field
     */
    changeHexaField: function( element, newValue, oldValue ) {
        newValue = newValue.trim().substring(0, 6);
        if (newValue.length === 3) {
            // convert values like ABC to AABBCC
            newValue = newValue[0] + newValue[0] + newValue[1] + newValue[1] + newValue[2] + newValue[2];
        }
        if (!newValue.match(/^[0-9a-f]{6}$/i)) {
            newValue = "000000"; 
        }
        this._HEX = newValue;
        this.updateColorsFromHexaField();
        this.updateColor();
        this.updatePickers();
        // fire the changehexa event
        this.fireEvent( 'changehexa', this, this._HEX );
    },
    /**
     *
     */
    setColorFromWebsafe: function() {
        this.setColor( this.wsColorContainer.getColor( 'backgroundColor','','' ) );
    },
    /**
     *
     */
    setColorFromInvert: function() {
        this.setColor( this.inColorContainer.getColor( 'backgroundColor','','' ) );
    },
    /**
     * Set initial color if config contains
     * @private
     */
    checkConfig: function() {
        if( this.config ) {
            if( this.config.color ) { this.setColor( this.config.color ); }
            else if( this.config.hsv ) { this.setHSV( this.config.hsv ); }
            else if( this.config.rgb ) { this.setRGB( this.config.rgb ); }
        }
    },

    // PUBLIC methods

    /**
     * Change color with hexa value
     * @param {String} hexa (eg.: 9A4D5F )
     */
    setColor: function( hexa ) {
        var temp = this.hexToRgb( hexa );
        this._RGB = { r:temp[0], g:temp[1], b:temp[2] }
        var temp = this.rgbToHsv( temp );
        this._HSV = { h:temp[0], s:temp[1], v:temp[2] };
        this.updateColor();
        this.updatePickers();
    },
    /**
     * Change color with a RGB Object
     * @param {Object} rgb (eg.: { r:255, g:200, b:111 })
     */
    setRGB: function( rgb ) {
        this._RGB = rgb;
        var temp = this.rgbToHsv( rgb.r, rgb.g, rgb.b );
        this._HSV = { h: temp[0], s: temp[1], v: temp[2] };
        this.updateColor();
        this.updatePickers();
    },
    /**
     * Change color with a HSV Object
     * @param {Object} hsv (eg.: { h:359, s:10, v:100 })
     */
    setHSV: function( hsv ) {
        this._HSV = { h: hsv.h, s: ( hsv.s / 100 ), v: ( hsv.v / 100 ) };
        var temp = this.hsvToRgb( hsv.h, ( hsv.s / 100 ), ( hsv.v / 100 ) );
        this._RGB = { r: temp[0], g: temp[1], b: temp[2] };
        this.updateColor();
        this.updatePickers();
    },
    /**
     * Get the color from the internal store
     * @param {Boolean} hash If it is true, the color prepended with '#'
     * @return {String} hexa color format
     */
    getColor: function( hash ) {
        return ( hash ? '' : '#' ) + this._HEX;
    },
    /**
     * Get the color from the internal store in RGB object format
     * @return {Object} format: { r: redvalue, g: greenvalue, b: bluevalue }
     */
    getRGB: function() {
        return this._RGB;
    },
    /**
     * Get the color from the internal store in HSV object format
     * @return {Object} format: { h: huevalue, s: saturationvalue, v: brightnessvalue }
     */
    getHSV: function() {
        return this._HSV;
    },
    /**
     * Make input panel visible/hidden
     * @param {Boolean} show Turns panel hidden or visible
     * @param {Boolean/Object} animate Show/hide with animation or not
     */
    setPanelVisible: function( show, animate ) {
        return this.formContainer.setVisible( show, animate );
    },
    /**
     * Returns with boolean, input panel is visible or not
     * @return {Boolean}
     */
    isPanelVisible: function() {
        return this.formContainer.isDisplayed();
    },
    /**
     * Make ColorPicker visible if it is not
     * note: in ColorDialog it changed to the show method of BasicDialog
     */
    showPicker: function() {
        this.domElement.show();
    },
    /**
     * Make ColorPicker hidden if it is visible
     * note: in ColorDialog it changed to the hide method of BasicDialog
     */
    hidePicker: function() {
        this.domElement.hide();
    }
});
/**
 * @class Ext.ux.ColorPanel
 * @extends Ext.util.ColorPicker,
 * @constructor
 * Creates new ColorPanel
 * @param {Object} config Config Object (see the Ext.Panel config too!)
 * @cfg {Boolean} hidePanel true to hide the inputs (defaults to false)
 * @cfg {Boolean/Object} animate Moving pickers with this animate or false to no animation (defaults to false)
 * @cfg {Object} rgb (optional) Add initial color with rgb format eg.: { r:255, g:128, b:10 }
 * @cfg {Object} hsv (optional) Add initial color with hsv format eg.: { h:100, s:60, v:50 }
 * @cfg {String} color (optional) Add initial color with hexa format eg.: 'A3CF6D'
 * @cfg {Object} pickerHotPoint (optional) If you change the picker image, you can change the point of pick. ( defaults to { x:3, y:3 } )
 * @cfg {Object} captions labels of inputs (defaults to { red: 'R', green: 'G', blue: 'B', hue: 'H°', saturation: 'S%', brightness: 'V%', hexa: 'Color', websafe: 'Websafe' })
 */

Ext.ux.ColorPanel = function( config ) {
    this.config = config;
    this.config.renderTo = this.config.renderTo || Ext.DomHelper.append( document.body, {}, true );
    Ext.ux.ColorPanel.superclass.constructor.call( this, config );
    this.domElement = Ext.get( this.config.renderTo );
    this.render( this.domElement );
    this.config.renderTo = this.body;
    this.initialize( this.config );
    this.getEl().addClass( 'x-cp-panel' );
    this.domElement.removeClass( 'x-cp-panel' )
    this.body.setStyle({ 'padding': '5px' });
}
Ext.extend( Ext.ux.ColorPanel, Ext.Panel );
Ext.applyIf( Ext.ux.ColorPanel.prototype, Ext.ux.ColorPicker.prototype );
/**
 * @class Ext.ux.ColorDialog
 * @extends Ext.util.ColorPicker,
 * @constructor
 * Creates new ColorDialog
 * @param {Object} config Config Object (see the Ext.Window config too!)
 * @cfg {Boolean} hidePanel true to hide the inputs (defaults to false)
 * @cfg {Boolean/Object} animate Moving pickers with this animate or false to no animation (defaults to false)
 * @cfg {Object} rgb (optional) Add initial color with rgb format eg.: { r:255, g:128, b:10 }
 * @cfg {Object} hsv (optional) Add initial color with hsv format eg.: { h:100, s:60, v:50 }
 * @cfg {String} color (optional) Add initial color with hexa format eg.: 'A3CF6D'
 * @cfg {Object} pickerHotPoint (optional) If you change the picker image, you can change the point of pick. ( defaults to { x:3, y:3 } )
 * @cfg {Object} captions labels of inputs (defaults to { red: 'R', green: 'G', blue: 'B', hue: 'H°', saturation: 'S%', brightness: 'V%', hexa: 'Color', websafe: 'Websafe' })
 */
Ext.ux.ColorDialog = function( config ) {
    this.config = config;
    this.config.resizable = false;
    this.config.renderTo = this.config.renderTo || Ext.DomHelper.append( document.body, {}, true );
    Ext.ux.ColorDialog.superclass.constructor.call( this, config );
    this.domElement = Ext.get( this.config.renderTo );
    this.render( this.domElement );
    this.config.renderTo = this.body;
    this.initialize( this.config );
    this.body.addClass( 'x-cp-panel' )
    this.body.setStyle({ padding: '5px' });
    this.setSize( 398, 300 );
}
Ext.extend( Ext.ux.ColorDialog, Ext.Window );
Ext.applyIf( Ext.ux.ColorDialog.prototype, Ext.ux.ColorPicker.prototype );