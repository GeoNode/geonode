{% load search_tags %}
{% raw %}
<article class="{{type}} {{storeType}}" data-category="{{category_slug}}" data-modified="{{last_modified}}" data-modified-date="{{last_modified_date}}" data-popular="{{popular}}" data-keywords="{{keywords}}" data-title="{{title}}">
  <h6>{{display_type}}</h6>
  <a href="{{url}}">
      <div class="img-placeholder pl-153-113">{{image}}</div>
  </a>
  <div class="details">
    <a href="{{url}}"><h5>{{title}}</h5></a>
    <div class="meta">by <a href="{{owner_url}}">{{owner}}</a>, {{owner_timestamp}}</div>
    <p>{{description}}</p>
    <p class="actions"><a href="#download-layer"  data-toggle="modal" class="btn btn-small strong">Download Data</a> <a href=""   data-toggle="modal" class="btn btn-small strong">Create Map</a></p>
  </div>
</article>
{% endraw %}