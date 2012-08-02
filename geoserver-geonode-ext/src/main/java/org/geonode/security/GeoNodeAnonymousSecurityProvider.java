package org.geonode.security;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import org.geoserver.config.GeoServerDataDirectory;
import org.geoserver.security.GeoServerSecurityFilterChain;
import org.geoserver.security.GeoServerSecurityManager;
import org.geoserver.security.GeoServerSecurityProvider;
import org.geoserver.security.config.SecurityManagerConfig;
import org.geoserver.security.config.SecurityNamedServiceConfig;
import org.geoserver.security.validation.SecurityConfigException;
import org.vfny.geoserver.global.GeoserverDataDirectory;

public class GeoNodeAnonymousSecurityProvider extends GeoServerSecurityProvider {
    @Override
    public Class<GeoNodeAnonymousProcessingFilter> getFilterClass() {
        return GeoNodeAnonymousProcessingFilter.class;
    }
    
    @Override
    public GeoNodeAnonymousProcessingFilter createFilter(SecurityNamedServiceConfig config) {
        return new GeoNodeAnonymousProcessingFilter();
    }
}
