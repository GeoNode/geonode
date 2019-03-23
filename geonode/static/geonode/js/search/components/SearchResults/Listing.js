import React from "react";
import Empty from "app/search/components/SearchResults/Empty";

export default class Results extends React.Component {
  render = () => (
    <article ng-repeat="item in results" resource_id="{{ item.id }}" ng-cloak class="ng-cloak">
      <div class="col-lg-12 item-container">
        <div class="col-lg-12 profile-avatar">
          <div class="col-lg-4 item-thumb">
            <a href="{{ item.detail_url }}">
              <img ng-src="{{ item.thumbnail_url }}" />
            </a>
          </div>
          <div class="col-lg-8 item-details">
            <div class="row">
              <div class="col-xs-10">
                <p class="item-meta">
                    <span class="item-category">{{ item.category__gn_description }}</span><br>
                    <span class="item-category" ng-if="item.group"><a href="{{ item.site_url }}groups/group/{{ item.group }}/activity/"><i class="fa fa-group" aria-hidden="true" style="margin-right: 8px;"></i>{{ item.group_name }}</a><br></span>
                    <span class="item-category" ng-if="item.has_time">
                      <i class="fa fa-clock-o" aria-hidden="true" style="margin-right: 8px;"></i>{window.gettext("Temporal Series")}<br>
                    </span>
                </p>
                <h4>
                    <i ng-if="item.store_type == 'remoteStore'" title="Remote Service" class="fa fa-external-link fa-1" style="vertical-align:  middle;padding-right: 10px;"></i>
                    <i ng-if="item.store_type == 'dataStore'" title="Vector Data" class="fa fa-pencil-square-o fa-1" style="vertical-align:  middle;padding-right: 10px;"></i>
                    <i ng-if="item.store_type == 'coverageStore'" title="Raster Data" class="fa fa-picture-o fa-1" style="vertical-align:  middle;padding-right: 10px;"></i>
                    <i ng-if="item.store_type == 'dataset'" title="File/Dataset" class="fa fa-newspaper-o fa-1" style="vertical-align:  middle;padding-right: 10px;"></i>
                    <i ng-if="item.store_type == 'map'" title="Map" class="fa fa-map-o fa-1" style="vertical-align:  middle;padding-right: 10px;"></i>
                    <a href="{{ item.detail_url }}">{{ item.title }}</a>
                </h4>
              </div>
              <div class="col-xs-2">
                <h4>
                  <button
                    class="btn btn-default btn-xs pull-right"
                    ng-if="cart"
                    ng-click="cart.toggleItem(item)"
                    data-toggle="tooltip"
                    data-placement="bottom"
                    title="Select"><i ng-class="cart.getFaClass(item.id)" class="fa fa-lg"></i></button>
                </h4>
              </div>
            </div>
            <em ng-if="item.online && item.store_type == 'remoteStore'">
              <span ng-if="item.online == true"><i class="fa fa-power-off text-success"></i> {window.gettext("Service is online")}</span>
              <span ng-if="item.online == false"><i class="fa fa-power-off text-danger"></i> {window.gettext("Service is offline")}</span>
            </em>
            <div class="alert alert-danger" ng-if="item.dirty_state == true">{window.gettext("SECURITY NOT YET SYNCHRONIZED")}</div>
            <div class="alert alert-warning" ng-if="item.dirty_state == false && item.is_approved == false">{window.gettext("PENDING APPROVAL")}</div>
            <div class="alert alert-danger" ng-if="item.dirty_state == false && item.is_approved == true && item.is_published == false">{window.gettext("UNPUBLISHED")}</div>

            <p class="abstract">{{ item.abstract | limitTo: 300 }}{{ item.abstract.length  > 300 ? '...' : ''}}</p>
            <div class="row">
              <div class="col-lg-12 item-items">
                <ul class="list-inline">
                  <li><a href="{{ item.site_url }}people/profile/{{ item.owner__username }}"><i class="fa fa-user"></i>{{ item.owner_name }}</a></li>
                  <li><a href="{{ item.detail_url }}#info"><i class="fa fa-calendar-o"></i>{{ item.date|date:'d MMM y' }}</a></li>
                  <li><a href="{{ item.detail_url }}"><i class="fa fa-eye"></i>{{ item.popular_count }}</a></li>
                  <li><a href="{{ item.detail_url }}#share"><i class="fa fa-share"></i>{{ item.share_count }}</a></li>
                  <li><a href="{{ item.detail_url }}#rate"><i class="fa fa-star"></i>{{ item.rating }}</a></li>
                  <li><a ng-if="item.detail_url.indexOf('/layers/') > -1" href="{% endverbatim %}{% url "new_map" %}?layer={% verbatim %}{{ item.detail_url.substring(8) }}">
                    <i class="fa fa-map-marker"></i>window.gettext("Create a Map")</a>
                  </li>
                  <li><a ng-if="item.detail_url.indexOf('/maps/') > -1" href="{{ item.site_url }}maps/{{item.id}}/view">
                    <i class="fa fa-map-marker"></i>window.gettext("View Map")</a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}
