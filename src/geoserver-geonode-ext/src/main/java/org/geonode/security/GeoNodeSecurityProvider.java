package org.geonode.security;

import org.geoserver.security.GeoServerSecurityProvider;
import org.geoserver.security.config.SecurityNamedServiceConfig;

public class GeoNodeSecurityProvider extends GeoServerSecurityProvider {
    private final HTTPClient httpClient = new HTTPClient(10, 1000, 1000);
    
    @Override
    public Class<GeoNodeAuthenticationProvider> getAuthenticationProviderClass() {
        return GeoNodeAuthenticationProvider.class;
    }
    
    @Override
    public GeoNodeAuthenticationProvider createAuthenticationProvider(
            SecurityNamedServiceConfig config)
    {
        return new GeoNodeAuthenticationProvider(
                configuredClient(((GeoNodeAuthProviderConfig)config).getBaseUrl()));
    }
    
    @Override
    public Class<GeoNodeCookieProcessingFilter> getFilterClass() {
        return GeoNodeCookieProcessingFilter.class;
    }
    
    @Override
    public GeoNodeCookieProcessingFilter createFilter(SecurityNamedServiceConfig config) {
        return new GeoNodeCookieProcessingFilter(
                configuredClient(((GeoNodeAuthFilterConfig)config).getBaseUrl()));
    }
    
    private GeoNodeSecurityClient configuredClient(String baseUrl) {
        return new DefaultSecurityClient(baseUrl, httpClient);
    }
}
