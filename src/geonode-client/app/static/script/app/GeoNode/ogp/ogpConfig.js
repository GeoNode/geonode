Ext.namespace("GeoNode");

Ext.onReady(function(){

  GeoNode.queryTerms = {
    intx: "product(max(0,sub(min(180,max_x),max(-180,min_x))),max(0,sub(min(90,max_y),max(-90,min_y))))",
    sort: "score desc",
    //qf: "LayerTitleSynonyms^0.2 ThemeKeywordsSynonymsIso^0.1 ThemeKeywordsSynonymsLcsh^0.1 PlaceKeywordsSynonyms^0.1 Publisher^0.1 layer_originator^0.1 Abstract^0.2",
    qf: "title_txt^1 abstract_txt^0.2 originator_txt",
    wt: "json",
    defType: "edismax",
    q: "*",
    fq: [
        "{!frange l=0 incl=false cache=false}$intx"
    ]
  };


  GeoNode.solrBackend = 'http://worldmap.harvard.edu/solr/hypermap/select';

  var solr = new GeoNode.Solr();
  solr.enableHeatmap();
  GeoNode.solr = solr;

});
