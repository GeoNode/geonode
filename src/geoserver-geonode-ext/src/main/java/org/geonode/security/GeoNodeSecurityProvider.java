package org.geonode.security;

import org.geoserver.security.GeoServerSecurityProvider;
import org.geoserver.security.config.SecurityNamedServiceConfig;

public class GeoNodeSecurityProvider extends GeoServerSecurityProvider {
    @Override
    public Class<GeoNodeAuthenticationProvider> getAuthenticationProviderClass() {
        return GeoNodeAuthenticationProvider.class;
    }
    
    @Override
    public GeoNodeAuthenticationProvider createAuthenticationProvider(
            SecurityNamedServiceConfig config)
    {
        HTTPClient httpClient = new HTTPClient(10, 1000, 1000);
        GeoNodeSecurityClient client = new DefaultSecurityClient(httpClient );
        return new GeoNodeAuthenticationProvider(client);
    }
}
