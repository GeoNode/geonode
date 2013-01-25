package org.geonode.web.security;

import org.geonode.security.GeoNodeAuthFilterConfig;
import org.geonode.security.GeoNodeCookieProcessingFilter;
import org.geoserver.security.web.auth.AuthenticationFilterPanelInfo;

public class GeoNodeAuthFilterPanelInfo
extends AuthenticationFilterPanelInfo<GeoNodeAuthFilterConfig, GeoNodeAuthFilterPanel> 
{
    private static final long serialVersionUID = -3960688504391117471L;

    public GeoNodeAuthFilterPanelInfo() {
        setComponentClass(GeoNodeAuthFilterPanel.class);
        setServiceClass(GeoNodeCookieProcessingFilter.class);
        setServiceConfigClass(GeoNodeAuthFilterConfig.class);
    }
}
