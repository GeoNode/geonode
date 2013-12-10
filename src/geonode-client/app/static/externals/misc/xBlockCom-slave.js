"use strict";

(function($) {
    $.QueryString = (function(a) {
        if (a == "") return {};
        var b = {};
        for (var i = 0; i < a.length; ++i)
        {
            var p=a[i].split('=');
            if (p.length != 2) continue;
            b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
        }
        return b;
    })(window.location.search.substr(1).split('&'))
})(jQuery);

/** MESSAGING is a singleton for easy access **/
var MESSAGING = (function Messaging() { // declare 'Singleton' as the return value of a self-executing anonymous function
    var _instance = null;
    var _constructor = function() {
        var a = $('<a>', { href:document.referrer } )[0];
        this.referringHost = a.protocol+"//"+a.hostname+":"+(a.port ? a.port : "80")+"/";
        this.handlers = [];
        this.uniqueId = CryptoJS.MD5(" "+location.href+(Math.random()*(new Date().getTime()))).toString(CryptoJS.enc.Base64);
        this.isMasterSlave = false;
    };
    _constructor.prototype = { // *** prototypes will be "public" methods available to the instance
        initialize: function() {
            console.log("client sending 'init' message to master");
            this.send(new Message("init",{}),true);
        },
        setMasterSlave: function(b) { this.isMasterSlave = b; },
        getReferringHost: function() {
            return this.referringHost;
        },
        setOpener: function(o) {
            this.opener = o;
            if( !this.opener ) this.isMasterSlave = false;
        },
        send: function(msg, force) {
            force = typeof force !== 'undefined'?force:false;
            if( (force && this.opener) || this.isMasterSlave) {
                console.log("sending message: type="+msg.type+", message = "+msg.message);
                this.opener.postMessage({xblockId:$.QueryString["xblockId"], uniqueClientId:this.uniqueId, message: msg}, this.getReferringHost());
            } else {
                console.log("not sending message, type="+msg.type+",  message="+msg.message);
            }
        },
        registerHandler: function(t,h) {
            this.handlers[t] = h;
        },
        handleMessageEvent: function(event) {
            var data = JSON.parse(event.data);
            if( data.type == "master-acknowledge" || this.isMasterSlave ) {
                var a = $('<a>', { href:event.origin})[0];
                var originHost = a.protocol+"//"+a.hostname+":"+(a.port?a.port:"80")+"/";
                if( originHost == this.referringHost) { //SECURITY: we only listen to messages from our referring host
                    if( this.handlers[data.type] ) {
                        var msg = new Message(data.type, JSON.parse(data.message)); //data.message is a JSON string
                        this.handlers[data.type]( msg );
                    }
                }
            }
        }
    };
    return {
        // because getInstance is defined within the same scope, it can access the "private" '_instance' and '_constructor' vars
        getInstance: function() {
            if( !_instance ) {
                console.log("creating Messaging singleton");
                _instance = new _constructor();
            }
            return _instance;
        }
    }
})();


function Message(t,m) {
    this.type = t;
    this.message = JSON.stringify(m);
}
Message.prototype = {
    constructor: Message,
    getType: function() { return this.type; },
    getMessage: function() { return JSON.parse(this.message); },
    getMessageStr: function() { return this.message; }
};

var loadHandler = function(event){
    console.log("DOMContentLoaded handler called");
    var parentWindow =  event.currentTarget.opener ? event.currentTarget.opener : window.parent;
    MESSAGING.getInstance().setOpener(parentWindow);
    MESSAGING.getInstance().registerHandler("master-acknowledge",
        function(msg) {
            console.log("handler for master-acknowledge called  type="+msg.getType()+",   message="+msg.getMessage());
            if( msg.getType() === "master-acknowledge" && msg.getMessage()===MESSAGING.getInstance().uniqueId) {
                console.log("master-acknowledge: masterSlave = true");
                MESSAGING.getInstance().setMasterSlave(true);
            }
        });
    MESSAGING.getInstance().initialize();

    window.addEventListener(
        'message',
        function(event){
            MESSAGING.getInstance().handleMessageEvent(event);
        },
        false
    );
}
window.addEventListener('DOMContentLoaded', loadHandler, false);

//Register a handler for an "info" message
//   MESSAGING.getInstance().registerHandler("info", function(m) { alert("the client code received this 'info' message: "+m.getMessage()); });