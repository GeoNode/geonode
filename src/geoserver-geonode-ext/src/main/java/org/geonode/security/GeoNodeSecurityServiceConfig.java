package org.geonode.security;

import org.geoserver.security.config.BaseSecurityNamedServiceConfig;
import org.geoserver.security.config.SecurityAuthProviderConfig;

public class GeoNodeSecurityServiceConfig extends BaseSecurityNamedServiceConfig
    implements SecurityAuthProviderConfig
{
    private static final long serialVersionUID = -4659786609079726648L;
    private String userGroupServiceName;

    public void setUserGroupServiceName(String userGroupServiceName) {
        this.userGroupServiceName = userGroupServiceName;
    }

    public String getUserGroupServiceName() {
        return this.userGroupServiceName;
    }

    public String getBaseUrl() {
        return "http://localhost:8000/";
    }
}
