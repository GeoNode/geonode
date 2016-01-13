Ext.namespace("GeoNode");

Ext.onReady(function(){

  GeoNode.queryTerms = {
    intx: "product(max(0,sub(min(180,MaxX),max(-180,MinX))),max(0,sub(min(90,MaxY),max(-90,MinY))))",
    sort: "score desc",
    'qf': "LayerDisplayNameSynonyms^0.2 ThemeKeywordsSynonymsIso^0.1 ThemeKeywordsSynonymsLcsh^0.1 PlaceKeywordsSynonyms^0.1 Publisher^0.1 Originator^0.1",
    'wt': "json",
    'defType': "edismax",
    'fl': "Name,Institution,Access,DataType,LayerDisplayName,Publisher,GeoReferenced,Originator,Location,MinX,MaxX,MinY,MaxY,ContentDate,LayerId,score,WorkspaceName,CollectionId,ServiceType,Availability",
    'q': "*",
    'bf': [
    "recip(sum(abs(sub(Area,64800)),.01),1,1000,1000)^70",
    "product(sum(map(sum(map(sub(-90,MinX),0,400,1,0),map(sub(-90,MaxX),-400,0,1,0),map(sub(-45,MinY),0,400,1,0),map(sub(-45,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(-90,MinX),0,400,1,0),map(sub(-90,MaxX),-400,0,1,0),map(sub(0,MinY),0,400,1,0),map(sub(0,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(-90,MinX),0,400,1,0),map(sub(-90,MaxX),-400,0,1,0),map(sub(45,MinY),0,400,1,0),map(sub(45,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(0,MinX),0,400,1,0),map(sub(0,MaxX),-400,0,1,0),map(sub(-45,MinY),0,400,1,0),map(sub(-45,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(0,MinX),0,400,1,0),map(sub(0,MaxX),-400,0,1,0),map(sub(0,MinY),0,400,1,0),map(sub(0,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(0,MinX),0,400,1,0),map(sub(0,MaxX),-400,0,1,0),map(sub(45,MinY),0,400,1,0),map(sub(45,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(90,MinX),0,400,1,0),map(sub(90,MaxX),-400,0,1,0),map(sub(-45,MinY),0,400,1,0),map(sub(-45,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(90,MinX),0,400,1,0),map(sub(90,MaxX),-400,0,1,0),map(sub(0,MinY),0,400,1,0),map(sub(0,MaxY),-400,0,1,0)),4,4,1,0),map(sum(map(sub(90,MinX),0,400,1,0),map(sub(90,MaxX),-400,0,1,0),map(sub(45,MinY),0,400,1,0),map(sub(45,MaxY),-400,0,1,0)),4,4,1,0)),0.1111111111111111)^30",
    "sum(recip(abs(sub(product(sum(MinX,MaxX),.5),0)),1,1000,1000),recip(abs(sub(product(sum(MinY,MaxY),.5),0)),1,1000,1000))^15",
    "if(and(exists(MinX),exists(MaxX),exists(MinY),exists(MaxY)),map(sum(map(MinX,-180,180,1,0),map(MaxX,-180,180,1,0),map(MinY,-90,90,1,0),map(MaxY,-90,90,1,0)),4,4,1,0),0)^80"
    ],
    'fq': [
        "{!frange l=0 incl=false cache=false}$intx",
        "Institution:Harvard OR Access:Public"
    ]
  };

  GeoNode.solrBackend = 'http://54.83.116.189:8983/solr/wmdata/select';

  var solr = new GeoNode.Solr();
  solr.enableHeatmap();
  GeoNode.solr = solr;

});



