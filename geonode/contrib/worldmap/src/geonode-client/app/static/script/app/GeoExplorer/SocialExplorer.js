/**
 * 
 */


GeoExplorer.SocialExplorer = function(target)
{
    var se_url = 'http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402';  //Default
    if (target.config.social_explorer && target.config.social_explorer[0]) {
        se_url = target.config.social_explorer[0].url;
    }


    var jumpstore = new Ext.data.SimpleStore({
                    fields: ['dataFieldName', 'displayFieldName'],
                    data: [[0, 'Yelp'],
                           [1, 'Bing Map'],
                           [2, 'Social Explorer']
                          ],
                    autoLoad: false
                  });

    var jumpBar = new Ext.form.ComboBox({
    id: 'jumpbar',
    store: jumpstore,
    displayField: 'displayFieldName',   // what the user sees in the popup
    valueField: 'dataFieldName',        // what is passed to the 'change' event
    typeAhead: true,
    forceSelection: true,
    fieldLabel: 'ComboBox',
    emptyText:'Jump to...',
    mode: 'local',
    triggerAction: 'all',
    selectOnFocus: true,
    editable: true,
    listeners: {

     /**'select' will be fired as soon as an item in the ComboBox is selected.
      *1) get the bbox or center point
      *2) parse the bbox or center point
      *3) go to the web pages
      *reference: http://www.hutten.org/bill/extjs/
      **/
     select: function(combo, record, index){
       displayProjection = new OpenLayers.Projection("EPSG:4326");
       if (record.data.dataFieldName == 0)
       {
          //http://www.yelp.com/search?find_desc=&find_loc=Boston%2C+MA&ns=1&rpp=10#bbox=-71.1611938477%2C42.2823890429%2C-70.9538269043%2C42.4356201565&sortby=category

          var bounds = target.mapPanel.map.getExtent();
          var extents= bounds.transform(target.mapPanel.map.getProjectionObject(),displayProjection);
          window.open ('http://www.yelp.com/search?find_desc=&ns=1&rpp=10#l=g:'+extents.left+'%2C'+extents.bottom+'%2C'+extents.right+'%2C'+extents.top+'&sortby=category');
       }
       else if (record.data.dataFieldName == 1){
          //http://www.bing.com/maps/default.aspx?v=2&FORM=LMLTCP&cp=42.353216~-70.989532&style=r&lvl=12&tilt=-90&dir=0&alt=-1000&phx=0&phy=0&phscl=1&encType=1

          var point = target.mapPanel.map.getCenter();
          var lonlat = point.transform(target.mapPanel.map.getProjectionObject(), displayProjection);
          window.open ('http://www.bing.com/maps/default.aspx?v=2&FORM=LMLTCP&cp='+ lonlat.lat +'~'+ lonlat.lon +'&style=r&lvl='+target.mapPanel.map.getZoom()+'&tilt=-90&dir=0&alt=-1000&phx=0&phy=0&phscl=1&encType=1');

       }
       else if (record.data.dataFieldName == 2){
          //http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402&l=2507554.70420796&r=2572371.78398336&t=5433997.44009869&b=5403894.11016116&rndi=1
          var bounds = target.mapPanel.map.getExtent();
          var extents= bounds.transform(target.mapPanel.map.getProjectionObject(),displayProjection);
          window.open(se_url + '&l='+extents.left+'&r='+extents.right+'&t='+extents.top+'&b='+extents.bottom+'&rndi=1');
       } else {}

     }
    }
    });
    
    return jumpBar;

}





function ConvertLonToAlbersEqArea(dLon) 
{

    //compute LON
    //Earth radius = 5,269,308.57789304
    //pi = 3.1415
    //cos(38)/180 = 0.00530596468915164
    //Earth Radius * pi = 16553532.89745098516 * cos(38)/180 = 87832.461034585
    return roundNumber(87832.461034585 * (dLon + 100), 2);
};

function ConvertLatToAlbersEqArea(dLat)
{
    //compute LAT
    var e = 0.0818191955335;    //eccentricity
    var es = .00669438075774911;  //e^2
    var one_es = 0.993305619242251; //1-es
    var k0 = .0000001237057815;       //general scaling factor 
    var pi = 3.14159265358979;      //our old friend
    
    var dRadsLat = (pi * dLat) / 180;  //angle in radians
    var dSinLat = Math.sin(dRadsLat);     //sin(lat in radians)
    var dCon = e * dSinLat; 
    return roundNumber(0.5 * (one_es * (dSinLat / (1 - dCon * dCon) - (0.5 / e) * Math.log((1 - dCon) / (1 + dCon)))) / k0, 2);
};


//  roundNumber function from:  http://www.mediacollege.com/internet/javascript/number/round.html
function roundNumber(rnum, rlength) 
{
  if (rnum > 8191 && rnum < 10485) 
  {
    rnum = rnum-5000;
    var newnumber = Math.round(rnum*Math.pow(10,
rlength))/Math.pow(10,rlength);
    return newnumber+5000;
  } 
  else 
    return Math.round(rnum*Math.pow(10,rlength))/Math.pow(10,rlength);
};