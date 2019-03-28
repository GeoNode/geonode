import React from "react";
import PropTypes from "prop-types";
import getNewMapURL from "app/search/functions/getNewMapURL";
import ellipseString from "app/helpers/ellipseString";

const containsPath = (url, path) => url.indexOf(`/${path}/`) > -1;

const getStyle = (condition, style = {}) => {
  style.display = condition ? "block" : "none";
  return style;
};

const getDataButtonStyle = (listing, dataType) =>
  getStyle(listing.store_type === dataType, {
    verticalAlign: "middle",
    paddingRight: 10
  });

const Listing = props => {
  const listing = props.result;
  return (
    <article key={listing.key} resource_id={listing.id}>
      <div className="col-lg-12 item-container">
        <div className="col-lg-12 profile-avatar">
          <div className="col-lg-4 item-thumb">
            <a href={listing.detail_url}>
              <img src={listing.thumbnail_url} />
            </a>
          </div>
          <div className="col-lg-8 item-details">
            <div className="row">
              <div className="col-xs-10">
                <p className="item-meta">
                  <span className="item-category">
                    {listing.category__gn_description}
                  </span>
                  <br />
                  <span
                    className="item-category"
                    style={getStyle(listing.group)}
                  >
                    <a
                      href={`${listing.site_url}groups/group/${listing.group}/activity/`}
                    >
                      <i
                        className="fa fa-group"
                        aria-hidden="true"
                        style={{ marginRight: 8 }}
                      />
                      {listing.group_name}
                    </a>
                    <br />
                  </span>
                  <span
                    className="item-category"
                    style={getStyle(listing.has_time)}
                  >
                    <i
                      className="fa fa-clock-o"
                      aria-hidden="true"
                      style={{ marginRight: 8 }}
                    />
                    {window.gettext("Temporal Series")}
                    <br />
                  </span>
                </p>
                <h4>
                  <i
                    style={getDataButtonStyle(listing, "remoteStore")}
                    title="Remote Service"
                    className="fa fa-external-link fa-1"
                  />
                  <i
                    style={getDataButtonStyle(listing, "dataStore")}
                    title="Vector Data"
                    className="fa fa-pencil-square-o fa-1"
                  />
                  <i
                    style={getDataButtonStyle(listing, "coverageStore")}
                    title="Raster Data"
                    className="fa fa-picture-o fa-1"
                  />
                  <i
                    style={getDataButtonStyle(listing, "dataset")}
                    title="File/Dataset"
                    className="fa fa-newspaper-o fa-1"
                  />
                  <i
                    style={getDataButtonStyle(listing, "map")}
                    title="Map"
                    className="fa fa-map-o fa-1"
                  />
                  <a href={listing.detail_url}>{listing.title}</a>
                </h4>
              </div>
              <div className="col-xs-2">
                <h4>
                  <button
                    className="btn btn-default btn-xs pull-right"
                    ng-if="cart"
                    ng-click="cart.toggleItem(item)"
                    data-toggle="tooltip"
                    data-placement="bottom"
                    title="Select"
                  >
                    <i className="fa fa-lg" />
                  </button>
                </h4>
              </div>
            </div>
            <em
              style={getStyle(
                listing.online && listing.store_type === "remoteStore"
              )}
            >
              <span style={getStyle(listing.online)}>
                <i className="fa fa-power-off text-success" />{" "}
                {window.gettext("Service is online")}
              </span>
              <span style={getStyle(!listing.online)}>
                <i className="fa fa-power-off text-danger" />{" "}
                {window.gettext("Service is offline")}
              </span>
            </em>
            <div
              className="alert alert-danger"
              style={getStyle(listing.dirty_state)}
            >
              {window.gettext("SECURITY NOT YET SYNCHRONIZED")}
            </div>
            <div
              className="alert alert-warning"
              style={getStyle(!listing.dirty_state && !listing.is_approved)}
            >
              {window.gettext("PENDING APPROVAL")}
            </div>
            <div
              className="alert alert-danger"
              style={getStyle(
                !listing.dirty_state &&
                  listing.is_approved &&
                  !listing.is_published
              )}
            >
              {window.gettext("UNPUBLISHED")}
            </div>

            <p className="abstract">{ellipseString(300, listing.abstract)}</p>
            <div className="row">
              <div className="col-lg-12 item-items">
                <ul className="list-inline">
                  <li>
                    <a
                      href={`${listing.site_url}people/profile/${listing.owner__username}`}
                    >
                      <i className="fa fa-user" />
                      {listing.owner_name}
                    </a>
                  </li>
                  <li>
                    <a href={`${listing.detail_url}#info`}>
                      <i className="fa fa-calendar-o" />
                      {listing.date}
                    </a>
                  </li>
                  <li>
                    <a href={listing.detail_url}>
                      <i className="fa fa-eye" />
                      {listing.popular_count}
                    </a>
                  </li>
                  <li>
                    <a href={`${listing.detail_url}#share`}>
                      <i className="fa fa-share" />
                      {listing.share_count}
                    </a>
                  </li>
                  <li>
                    <a href={`${listing.detail_url}#rate`}>
                      <i className="fa fa-star" />
                      {listing.rating}
                    </a>
                  </li>

                  <li>
                    <a
                      style={getStyle(
                        containsPath(listing.detail_url, "layers")
                      )}
                      href={getNewMapURL(
                        window.siteUrl,
                        listing.detail_url.substring(8)
                      )}
                    >
                      <i className="fa fa-map-marker" />
                      {window.gettext("Create a Map")}
                    </a>
                  </li>
                  <li>
                    <a
                      style={getStyle(containsPath(listing.detail_url, "maps"))}
                      href={`${listing.site_url}maps/${listing.id}/view`}
                    >
                      <i className="fa fa-map-marker" />
                      {window.gettext("View Map")}
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};

Listing.propTypes = {
  result: PropTypes.object.isRequired
};

export default Listing;
