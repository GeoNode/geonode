package org.geonode.web.security;

import org.geonode.security.GeoNodeSecurityServiceConfig;
import org.geoserver.security.web.auth.AuthenticationProviderPanel;
import org.apache.wicket.model.IModel;

public class GeoNodeAuthProviderPanel
extends AuthenticationProviderPanel<GeoNodeSecurityServiceConfig>
{
    public GeoNodeAuthProviderPanel(String id, IModel<GeoNodeSecurityServiceConfig> model) {
        super(id, model);
    }
}
