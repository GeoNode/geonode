package org.geonode.web.security;

import org.apache.wicket.model.IModel;
import org.geonode.security.GeoNodeAnonymousAuthFilterConfig;
import org.geoserver.security.web.auth.AuthenticationFilterPanel;

public class GeoNodeAnonymousAuthFilterPanel extends AuthenticationFilterPanel<GeoNodeAnonymousAuthFilterConfig> {
    private static final long serialVersionUID = 6525505737315060871L;

    public GeoNodeAnonymousAuthFilterPanel(String id, IModel<GeoNodeAnonymousAuthFilterConfig> model) {
        super(id, model);
    }
}
