package org.geonode.web.security;

import org.geonode.security.GeoNodeAnonymousAuthFilterConfig;
import org.geonode.security.GeoNodeAnonymousProcessingFilter;
import org.geoserver.security.web.auth.AuthenticationFilterPanelInfo;

public class GeoNodeAnonymousAuthFilterPanelInfo
extends AuthenticationFilterPanelInfo<GeoNodeAnonymousAuthFilterConfig, GeoNodeAnonymousAuthFilterPanel> 
{
    private static final long serialVersionUID = -3960688504391117471L;

    public GeoNodeAnonymousAuthFilterPanelInfo() {
        setComponentClass(GeoNodeAnonymousAuthFilterPanel.class);
        setServiceClass(GeoNodeAnonymousProcessingFilter.class);
        setServiceConfigClass(GeoNodeAnonymousAuthFilterConfig.class);
    }
}
