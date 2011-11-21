var set_thumbnail = Ext.get("set_thumbnail");
function promptThumbnail() {
    var img = '<img src="?thumbnail">';
    Ext.MessageBox.show({
       title:'Generate Thumbnail?',
       msg: 'This will generate a new thumbnail. The existing one is shown below.<div>' + img + '</div>',
       buttons: Ext.MessageBox.OKCANCEL,
       fn: function(buttonId) {
           if (buttonId == 'ok') {
               updateThumbnail();
           }
       },
       icon: Ext.MessageBox.QUESTION
    });
}

function updateThumbnail() {
    var map = Ext.get(Ext.query(".olMapViewport")[0]);
    var html = Ext.DomHelper.markup({
       style: {
                    width: map.getWidth(), height:map.getHeight()
                },
                html: map.dom.innerHTML
    });
    Ext.MessageBox.wait("Generating Thumbnail","Please wait while the thumbnail is generated.");
    Ext.Ajax.request({
      url : "?thumbnail",
      method : "POST",
      xmlData: html,
      success: function() {
          Ext.MessageBox.show({
             title : "Thumbnail Updated",
             msg : '<img src="?thumbnail&_=' + Math.random() + '">',
             buttons: Ext.MessageBox.OK
          });
      }
    });
}
if (set_thumbnail) {
    set_thumbnail.on("click",function(ev) {
       ev.stopEvent();
       promptThumbnail();
    });
}