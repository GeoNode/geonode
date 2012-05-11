package org.geonode.security;

import org.geoserver.security.config.BaseSecurityNamedServiceConfig;
import org.geoserver.security.config.SecurityAuthProviderConfig;

public class GeoNodeSecurityServiceConfig extends BaseSecurityNamedServiceConfig
    implements SecurityAuthProviderConfig {

    private String userGroupServiceName;

    public void setUserGroupServiceName(String userGroupServiceName) {
        this.userGroupServiceName = userGroupServiceName;
    }

    public String getUserGroupServiceName() {
        return this.userGroupServiceName;
    }
}
