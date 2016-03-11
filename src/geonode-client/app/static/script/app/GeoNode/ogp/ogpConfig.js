Ext.namespace("GeoNode");

Ext.onReady(function(){

  GeoNode.queryTerms = {
    intx: "product(max(0,sub(min(180,MaxX),max(-180,MinX))),max(0,sub(min(90,MaxY),max(-90,MinY))))",
    sort: "score desc",
    qf: "LayerTitleSynonyms^0.2 ThemeKeywordsSynonymsIso^0.1 ThemeKeywordsSynonymsLcsh^0.1 PlaceKeywordsSynonyms^0.1 Publisher^0.1 Originator^0.1 Abstract^0.2",
    wt: "json",
    defType: "edismax",
    q: "*",
    fq: [
        "{!frange l=0 incl=false cache=false}$intx"
    ]
  };

  GeoNode.solrBackend = 'http://54.83.116.189:8983/solr/search/select';

  var solr = new GeoNode.Solr();
  solr.enableHeatmap();
  GeoNode.solr = solr;

});



