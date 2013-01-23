{% load search_tags %}
{% raw %}
<article id="article-{{id}}" class="{{type}} {{storeType}}" data-category="{{category_slug}}" data-modified="{{last_modified}}" data-modified-date="{{last_modified_date}}" data-popular="{{popular}}" data-keywords="{{keywords}}" data-title="{{title}}" data-relevance="{{relevance}}">
  <h6>{{display_type}}</h6>
  <a href="{{url}}">
      <div class="img-placeholder pl-153-113">{{image}}</div>
  </a>
  <div class="details">
    <a href="{{url}}"><h5>{{title}}</h5></a>
    <div class="meta">by <a href="{{owner_url}}">{{owner}}</a>, {{owner_timestamp}}</div>
    <p>{{description}}</p>
    <p class="actions"><a href="#download-{{id}}"  data-toggle="modal" class="btn btn-small strong">Download Data</a> <a href="/maps/new?layer={{typename}}"   data-toggle="modal" class="btn btn-small strong">Create Map</a></p>
  </div>
</article>
<div class="modal custom hide" id="download-{{id}}">
    <div class="modal-header">
      <button class="close" data-dismiss="modal">×</button>
      <h2><i class="icon-download-alt"></i>  "Download Layer {{title}}"</h2>
    </div>
    <div class="modal-body">
    </div>
    <div class="modal-footer">
      <div class="span2 offset1">
        <ul class="unstyled">
          <li class="vector"><a href="{{zip}}">Zipped Shapefile</a></li>
          <li><a href="{{jpg}}">JPEG</a></li>
          <li class="vector"><a href="{{gml}}">GML 2.0</a></li>
          <li><a href="{{pdf}}">PDF</a></li>
          <li class="vector"><a href="{{gml}}">GML 3.1.1</a></li>
          <li><a href="{{png}}">PNG</a></li>
        </ul>
      </div>
      <div class="span2">
        <ul class="unstyled">
          <li class="vector"><a href="{{csv}}">CSV</a></li>
          <li><a href="{{kml}}">KML</a></li>
          <li class="vector"><a href="{{excel}}">Excel</a></li>
          <li class="vector"><a href="{{json}}">GeoJSON</a></li>
          <li><a href="{{kml}}">View in Google Earth</a></li>
          <li class="raster"><a href="{{GeoTIFF}}">GeoTIFF</a></li>
          <li><a href="{{tiles}}">TILES</a></li>
        </ul>
      </div>
    </div>
  </div>
{% endraw %}