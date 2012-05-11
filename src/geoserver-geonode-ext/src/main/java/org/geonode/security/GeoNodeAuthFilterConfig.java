package org.geonode.security;

import org.geoserver.security.config.SecurityAuthFilterConfig;
import org.geoserver.security.config.SecurityFilterConfig;

public class GeoNodeAuthFilterConfig extends SecurityFilterConfig implements SecurityAuthFilterConfig
{
    private static final long serialVersionUID = -5103697571467108155L;
    private String baseUrl;
    
    public String getBaseUrl() {
        return baseUrl;
    }
    
    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}
