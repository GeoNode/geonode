This GeoNode contrib module was contributed by the MapStory project.

Function of the module:
Allow user to favorite content in Document, Layer, Map detail pages.
  - If user is not logged in, tell them to log in if want to use favorites.
  - If user is logged in, provide an 'Add Favorite' button, or a 'Delete Favorite' button.
Allow user to view a favorites list page with delete link for each.
Allow user to link to user favorites list page from each detail and user profile page and user modal list.

-----

To enable the module:
This contribution was initially contributed with hooks in the core GeoNode code so that enabling this module involved only one change in settings.py file.
Per GeoNode developer input, the core hooks have been removed and these instructions have been added.
It is up to the installing developer to add these to enable this module.

Steps to enable Favorites in GeoNode:

1. add the module to the geonode.settings.py file.

    # GeoNode Contrib Apps
    # 'geonode.contrib.dynamic',
    'geonode.contrib.favorite',

2. add Favorites urls to the geonode/urls.py.

    urlpatterns += patterns('',
                            (r'^favorite/', include('geonode.contrib.favorite.urls')),
                            )

3. to show Favorites on a detail page, make these additions to the View and the corresponding template files.

3a. template - add link to the Favorite tab on the 'tab switcher' on geonode/templates/_actions.html:
(this single change gets included on each detail pages)

    after GeoGig, approx ln 15, add:

    <li><a href="#favorite" data-toggle="tab"><i class="fa fa-star"></i>{% trans "Favorite" %}</a></li>

3b. view - add an import and a code block to <model>_detail method.  Using Map as example, geonode/maps/views.py:
(repeat 3b and 3c for each detail page)

    in imports:
    from geonode.contrib.favorite.utils import get_favorite_info

    in map_detail method:
    if request.user.is_authenticated():
        context_dict["favorite_info"] = get_favorite_info(request.user, map_obj)

3c. template - include the Favorite html and js.  Using Map as example, geonode/maps/templates/maps/map_detail.html: 

    after the social_links block for map (or after ratings block for document/map), add:

    <article class="tab-pane" id="favorite">
      {% include "favorite/_favorite.html" %}
    </article>

    in the {% block extra_script %}, add:

    {% include "favorite/_favorite_js.html" %}


4. Add link to Favorites list from user profile page, geonode/people/templates/people/profile_detail.html:

    after My Activities, approx ln 95, add:

    <ul class="list-group">
        <li class="list-group-item"><a href="{% url "favorite_list" %}"><i class="fa fa-star"></i> {% trans "Favorites" %}</a></li>
    </ul>


5. Add link to Favorites list from user modal, geonode/templates/base.html:

    after notifications, approx ln 216, add:

    <li><a href="{% url "favorite_list" %}"><i class="fa fa-star"></i> {% trans "Favorites" %}</a></li> 


6. Run syncdb to create the new favorite_favorite table.