/*	
 *	CSSrefresh v1.0.1
 *	
 *	Copyright (c) 2012 Fred Heusschen
 *	www.frebsite.nl
 *
 *	Dual licensed under the MIT and GPL licenses.
 *	http://en.wikipedia.org/wiki/MIT_License
 *	http://en.wikipedia.org/wiki/GNU_General_Public_License
 */

(function() {

	var phpjs = {

		array_filter: function( arr, func )
		{
			var retObj = {}; 
			for ( var k in arr )
			{
				if ( func( arr[ k ] ) )
				{
					retObj[ k ] = arr[ k ];
				}
			}
			return retObj;
		},
		filemtime: function( file )
		{
			var headers = this.get_headers( file, 1 );
			return ( headers && headers[ 'Last-Modified' ] && Date.parse( headers[ 'Last-Modified' ] ) / 1000 ) || false;
	    },
	    get_headers: function( url, format )
	    {
			var req = window.ActiveXObject ? new ActiveXObject( 'Microsoft.XMLHTTP' ) : new XMLHttpRequest();
			if ( !req )
			{
				throw new Error('XMLHttpRequest not supported.');
			}

			var tmp, headers, pair, i, j = 0;

			try
			{
				req.open( 'HEAD', url, false );
				req.send( null ); 
				if ( req.readyState < 3 )
				{
					return false;
				}
				tmp = req.getAllResponseHeaders();
				tmp = tmp.split( '\n' );
				tmp = this.array_filter( tmp, function ( value )
				{
					return value.toString().substring( 1 ) !== '';
				});
				headers = format ? {} : [];
	
				for ( i in tmp )
				{
					if ( format )
					{
						pair = tmp[ i ].toString().split( ':' );
						headers[ pair.splice( 0, 1 ) ] = pair.join( ':' ).substring( 1 );
					}
					else
					{
						headers[ j++ ] = tmp[ i ];
					}
				}
	
				return headers;
			}
			catch ( err )
			{
				return false;
			}
		}
	};

	var cssRefresh = function() {

		this.reloadFile = function( links )
		{
			for ( var a = 0, l = links.length; a < l; a++ )
			{
				var link = links[ a ],
					newTime = phpjs.filemtime( this.getRandom( link.href ) );

				//	has been checked before
				if ( link.last )
				{
					//	has been changed
					if ( link.last != newTime )
					{
						//	reload
						link.elem.setAttribute( 'href', this.getRandom( this.getHref( link.elem ) ) );
					}
				}

				//	set last time checked
				link.last = newTime;
			}
			setTimeout( function()
			{
				this.reloadFile( links );
			}, 1000 );
		};

		this.getHref = function( f )
		{
			return f.getAttribute( 'href' ).split( '?' )[ 0 ];
		};
		this.getRandom = function( f )
		{
			return f + '?x=' + Math.random();
		};


		var files = document.getElementsByTagName( 'link' ),
			links = [];

		for ( var a = 0, l = files.length; a < l; a++ )
		{			
			var elem = files[ a ],
				rel = elem.rel;
			if ( typeof rel != 'string' || rel.length == 0 || rel == 'stylesheet' )
			{
				links.push({
					'elem' : elem,
					'href' : this.getHref( elem ),
					'last' : false
				});
			}
		}
		this.reloadFile( links );
	};


	cssRefresh();

})();