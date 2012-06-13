package org.geonode.web.security;

import org.apache.wicket.model.IModel;
import org.geonode.security.GeoNodeAuthFilterConfig;
import org.geoserver.security.web.auth.AuthenticationFilterPanel;

public class GeoNodeAuthFilterPanel extends AuthenticationFilterPanel<GeoNodeAuthFilterConfig> {
    private static final long serialVersionUID = 6525505737315060871L;

    public GeoNodeAuthFilterPanel(String id, IModel<GeoNodeAuthFilterConfig> model) {
        super(id, model);
    }
}
