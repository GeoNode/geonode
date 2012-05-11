package org.geonode.web.security;

import org.geonode.security.GeoNodeAuthenticationProvider;
import org.geonode.security.GeoNodeSecurityServiceConfig;
import org.geoserver.security.web.auth.AuthenticationProviderPanelInfo;

public class GeoNodeAuthProviderPanelInfo
extends AuthenticationProviderPanelInfo<GeoNodeSecurityServiceConfig, GeoNodeAuthProviderPanel> 
{
    public GeoNodeAuthProviderPanelInfo() {
        setComponentClass(GeoNodeAuthProviderPanel.class);
        setServiceClass(GeoNodeAuthenticationProvider.class);
        setServiceConfigClass(GeoNodeSecurityServiceConfig.class);
    }
}
