var Cookie=function(document,name){
	var me={};
	me.$document=document;
	me.$name=name;
	me.$path="/";
	me.$expiration=new Date((new Date()).getTime()+50000000*36);
	
	me.store=function(){
		var cookieval="";
		for(var prop in this){
			if((prop.charAt(0)=='$') || (typeof this[prop]) == 'function')
				continue;
			if(cookieval != "")cookieval += '&';
			cookieval +=prop+':'+escape(this[prop]);//this is where the $ is necessary
		}
		var cookie=me.$name+'='+cookieval;
		if(me.$expiration)
			cookie+=';expires='+me.$expiration.toGMTString();
		if(me.$domain)cookie+=';domain='+me.$domain;
		if(me.$secure)cookie+=';secure';
		me.$document.cookie=cookie;
	}

	me.load=function(){
		var allcookies=me.$document.cookie;
		if(allcookies=="")return false;
		var start=allcookies.indexOf(me.$name+'=');
		if(start==-1){
			return false;//
		}
		start+=me.$name.length+1;
		var end=allcookies.indexOf(';',start);
		if(end==-1)end=allcookies.length;
		var cookieval=allcookies.substring(start,end);
		var a=cookieval.split('&');
		for(var i=0;i<a.length;i++)
			a[i]=a[i].split(':');
		
		for(var i=0;i<a.length;i++)
			this[a[i][0]]=unescape(a[i][1]);
		
		return true;
	}
	
	me.remove=function(){
		var cookie;
		cookie=me.$name+'=';
		if(me.$path)cookie+=';path='+me.$path;
		if(me.$domain)cookie+=';domain='+me.$domain;
		cookie+=';expires=Fri, 02-Jan-1970 00:00:00 GMT';
		me.$document.cookie=cookie;
	}
	return me;
}
