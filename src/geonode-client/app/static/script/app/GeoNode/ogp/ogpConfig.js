Ext.namespace("GeoNode");

Ext.onReady(function(){

  GeoNode.queryTerms = {
    intx: "product(max(0,sub(min(180,MaxX),max(-180,MinX))),max(0,sub(min(90,MaxY),max(-90,MinY))))",
    sort: "score desc",
    qf: "LayerDisplayNameSynonyms^0.2 ThemeKeywordsSynonymsIso^0.1 ThemeKeywordsSynonymsLcsh^0.1 PlaceKeywordsSynonyms^0.1 Publisher^0.1 Originator^0.1 Abstract^0.2",
    wt: "json",
    defType: "edismax",
    fl: "Name,Institution,Access,DataType,LayerDisplayName,Publisher,GeoReferenced,Originator,Location,MinX,MaxX,MinY,MaxY,ContentDate,LayerId,score,WorkspaceName,CollectionId,ServiceType,Availability,Abstract",
    q: "*",
    fq: [
        "{!frange l=0 incl=false cache=false}$intx",
        "Institution:Harvard OR Access:Public"
    ]
  };

  GeoNode.solrBackend = 'http://54.83.116.189:8983/solr/wmdata/select';

  var solr = new GeoNode.Solr();
  solr.enableHeatmap();
  GeoNode.solr = solr;

});



