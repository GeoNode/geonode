package org.geonode.security;

import org.geoserver.security.config.BaseSecurityNamedServiceConfig;
import org.geoserver.security.config.SecurityAuthProviderConfig;

public class GeoNodeAuthProviderConfig extends BaseSecurityNamedServiceConfig
    implements SecurityAuthProviderConfig
{
    private static final long serialVersionUID = -4659786609079726648L;
    private String userGroupServiceName;
    private String baseUrl;

    public void setUserGroupServiceName(String userGroupServiceName) {
        this.userGroupServiceName = userGroupServiceName;
    }

    public String getUserGroupServiceName() {
        return this.userGroupServiceName;
    }

    public String getBaseUrl() {
        return baseUrl;
    }
    
    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}
