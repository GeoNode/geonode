package org.geoserver.security;

import java.io.IOException;
import org.geonode.security.GeoNodeAuthenticationProvider;
import org.geonode.security.GeonodeSecurityClient;
import org.geoserver.config.GeoServerDataDirectory;
import org.geoserver.security.config.SecurityManagerConfig;

/**
 * Customize authentiation/authorization.
 * 
 * @author Ian Schneider <ischneider@opengeo.org>
 */
public class GeoNodeSecurityManager extends GeoServerSecurityManager {
    private final GeonodeSecurityClient client;

    public GeoNodeSecurityManager(GeoServerDataDirectory dataDir, GeonodeSecurityClient client) throws Exception {
        super(dataDir);
        this.client = client;
    }

    @Override
    void init(SecurityManagerConfig config) throws Exception {
        super.init(config);
        
        // inject our authentication provider
        authProviders.add(new GeoNodeAuthenticationProvider(client));
    }

    @Override
    public SecurityManagerConfig loadSecurityConfig() throws IOException {
        SecurityManagerConfig config = super.loadSecurityConfig();
        
        GeoServerSecurityFilterChain filterChain = config.getFilterChain();
        
        // we are going to insert the following. Previously, this was done
        // in the spring security context.
        String[][] filters = new String[][]{
            {GeoServerSecurityFilterChain.WEB_CHAIN, "geonodeCookieFilter", GeoServerSecurityFilterChain.SECURITY_CONTEXT_ASC_FILTER},
            {GeoServerSecurityFilterChain.REST_CHAIN, "geonodeCookieFilter", GeoServerSecurityFilterChain.SECURITY_CONTEXT_NO_ASC_FILTER},
            {GeoServerSecurityFilterChain.GWC_REST_CHAIN, "geonodeCookieFilter", GeoServerSecurityFilterChain.SECURITY_CONTEXT_NO_ASC_FILTER},
            {GeoServerSecurityFilterChain.DEFAULT_CHAIN, "geonodeCookieFilter", GeoServerSecurityFilterChain.SECURITY_CONTEXT_NO_ASC_FILTER},
            
            {GeoServerSecurityFilterChain.WEB_CHAIN, "gnBasicProcessingFilter", "geonodeCookieFilter"},
            {GeoServerSecurityFilterChain.REST_CHAIN, "gnBasicProcessingFilter", "geonodeCookieFilter"},
            {GeoServerSecurityFilterChain.GWC_REST_CHAIN, "gnBasicProcessingFilter", "geonodeCookieFilter"},
            {GeoServerSecurityFilterChain.DEFAULT_CHAIN, "gnBasicProcessingFilter", "geonodeCookieFilter"},
            
            {GeoServerSecurityFilterChain.WEB_CHAIN, "gnAuthenticationProcessingFilter", "gnBasicProcessingFilter"},
        };

        for (int i = 0; i < filters.length; i++) {
            boolean inserted = filterChain.insertAfter(filters[i][0],filters[i][1],filters[i][2]);
            // fail fast if not inserted properly, this means some configuration in the core has changed
            if (!inserted) throw new RuntimeException("Invalid filter config " + i);
        }
        
        return config;
    }
    
    
    
}
