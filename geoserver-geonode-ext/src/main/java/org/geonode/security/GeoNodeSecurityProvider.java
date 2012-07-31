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
        return new GeoNodeCookieProcessingFilter();
    }
    
    private GeoNodeSecurityClient configuredClient(String baseUrl) {
        return new DefaultSecurityClient(baseUrl, httpClient);
    }
    
    @Override 
    public void init(GeoServerSecurityManager manager) {
    	try {
    		File cookie = geonodeCookie();
    		if (!cookie.exists()) {
    		    configureGeoNodeSecurity(manager);
    		    writeCookie(cookie);
    		}
		} catch (Exception e) {
			throw new RuntimeException("Failed to initialize GeoNode settings", e);
		}
    }
    
    private static File geonodeCookie() throws IOException {
    	GeoServerDataDirectory directory = GeoserverDataDirectory.accessor();
    	File geonodeDir = directory.findOrCreateDir("geonode");
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
        providerConfig.setBaseUrl("http://localhost/");
        manager.saveAuthenticationProvider(providerConfig);

        GeoNodeAuthFilterConfig filterConfig = new GeoNodeAuthFilterConfig();
        filterConfig.setName("geonodeCookieFilter");
        filterConfig.setClassName(GeoNodeCookieProcessingFilter.class.getCanonicalName());
        manager.saveFilter(filterConfig);
        
        GeoNodeAnonymousAuthFilterConfig anonymousFilterConfig = new GeoNodeAnonymousAuthFilterConfig();
        anonymousFilterConfig.setName("geonodeAnonymousFilter");
        anonymousFilterConfig.setClassName(GeoNodeAnonymousProcessingFilter.class.getCanonicalName());
        manager.saveFilter(anonymousFilterConfig);
    }

    private static void configureChains(GeoServerSecurityManager manager) throws Exception {
        SecurityManagerConfig config = manager.getSecurityConfig();
        config.getAuthProviderNames().add(0, "geonodeAuthProvider");

        GeoServerSecurityFilterChain filterChain = config.getFilterChain();
        String[] cookieChains = {
            GeoServerSecurityFilterChain.WEB_CHAIN,
            GeoServerSecurityFilterChain.REST_CHAIN,
            GeoServerSecurityFilterChain.GWC_REST_CHAIN,
            GeoServerSecurityFilterChain.DEFAULT_CHAIN
        };

        for (String chain : cookieChains) {
            filterChain.insertAfter(chain, "geonodeCookieFilter", "contextAsc");
            // if (!inserted) {
            // 	throw new RuntimeException("Failed to insert filter while configuring GeoNode extension: " + Arrays.toString(filter));
            // }
        }
        
        String[] anonymousChains = {
            GeoServerSecurityFilterChain.WEB_CHAIN,
            GeoServerSecurityFilterChain.REST_CHAIN,
            GeoServerSecurityFilterChain.GWC_REST_CHAIN,
            GeoServerSecurityFilterChain.DEFAULT_CHAIN
        };
        
        for (String chain : anonymousChains) {
            filterChain.insertBefore(chain, "geonodeAnonymousFilter", "anonymous");
        }
        
        manager.saveSecurityConfig(config);
    }
}
