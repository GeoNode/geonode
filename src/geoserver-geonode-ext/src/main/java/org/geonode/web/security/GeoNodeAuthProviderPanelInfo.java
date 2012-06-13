package org.geonode.web.security;

import org.geonode.security.GeoNodeAuthenticationProvider;
import org.geonode.security.GeoNodeAuthProviderConfig;
import org.geoserver.security.web.auth.AuthenticationProviderPanelInfo;

public class GeoNodeAuthProviderPanelInfo
extends AuthenticationProviderPanelInfo<GeoNodeAuthProviderConfig, GeoNodeAuthProviderPanel> 
{
    private static final long serialVersionUID = -1760541331841403781L;

	public GeoNodeAuthProviderPanelInfo() {
        setComponentClass(GeoNodeAuthProviderPanel.class);
        setServiceClass(GeoNodeAuthenticationProvider.class);
        setServiceConfigClass(GeoNodeAuthProviderConfig.class);
    }
}
