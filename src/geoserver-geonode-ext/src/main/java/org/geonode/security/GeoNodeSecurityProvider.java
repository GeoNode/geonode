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
    
    private boolean inInit = false;
    
    @Override 
    public void init(GeoServerSecurityManager manager) {
    	if (inInit) return;
    	inInit = true;
    	try {
    		File cookie = geonodeCookie();
    		if (!cookie.exists()) {
    		    configureGeoNodeSecurity(manager);
    		    writeCookie(cookie);
    		}
		} catch (Exception e) {
			throw new RuntimeException("Failed to initialize GeoNode settings", e);
		} finally {
    		inInit = false;
    	}
    }
    
    private static File geonodeCookie() throws IOException {
    	GeoServerDataDirectory directory = GeoserverDataDirectory.accessor();
    	File geonodeDir = directory.findOrCreateDataDir("geonode");
    	return new File(geonodeDir, "geonode_initialized");
    }
    
    private static void writeCookie(File cookie) throws IOException {
    	FileWriter writer = new java.io.FileWriter(cookie);
    	writer.write("This file was created to flag that the GeoNode extensions have been configured in this server.");
    	writer.write("If you delete it, the GeoNode settings will be applied again the next time you restart GeoServer.");
    	writer.close();
    }
    
    private static void configureGeoNodeSecurity(GeoServerSecurityManager manager) throws Exception {
        addServices(manager);
        configureChains(manager);
    }

    private static void addServices(GeoServerSecurityManager manager)
        throws IOException, SecurityConfigException
        {
            GeoNodeAuthProviderConfig providerConfig = new GeoNodeAuthProviderConfig();
            providerConfig.setName("geonodeAuthProvider");
            providerConfig.setClassName(GeoNodeAuthenticationProvider.class.getCanonicalName());
            providerConfig.setBaseUrl("http://localhost:8000/");
            manager.saveAuthenticationProvider(providerConfig);

            GeoNodeAuthFilterConfig filterConfig = new GeoNodeAuthFilterConfig();
            filterConfig.setName("geonodeCookieFilter");
            filterConfig.setClassName(GeoNodeCookieProcessingFilter.class.getCanonicalName());
            filterConfig.setBaseUrl("http://localhost:8000/");
            manager.saveFilter(filterConfig);
        }

    private static void configureChains(GeoServerSecurityManager manager) throws Exception {
        SecurityManagerConfig config = manager.getSecurityConfig();
        config.getAuthProviderNames().add(0, "geonodeAuthProvider");

        GeoServerSecurityFilterChain filterChain = config.getFilterChain();
        String[][] filters = {
            { GeoServerSecurityFilterChain.WEB_CHAIN, "geonodeCookieFilter" },
            { GeoServerSecurityFilterChain.REST_CHAIN, "geonodeCookieFilter" },
            { GeoServerSecurityFilterChain.GWC_REST_CHAIN, "geonodeCookieFilter" },
            { GeoServerSecurityFilterChain.DEFAULT_CHAIN, "geonodeCookieFilter" },
        };

        for (String[] filter : filters) {
            filterChain.insertFirst(filter[0], filter[1]);
            // if (!inserted) {
            // 	throw new RuntimeException("Failed to insert filter while configuring GeoNode extension: " + Arrays.toString(filter));
            // }
        }

        manager.saveSecurityConfig(config);
    }
}
