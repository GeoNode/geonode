package org.geonode.security;

import org.geoserver.config.util.XStreamPersister;
import org.geoserver.security.config.SecurityNamedServiceConfig;
import org.geoserver.security.filter.AbstractFilterProvider;
import org.geoserver.security.filter.GeoServerAnonymousAuthenticationFilter;
import org.geoserver.security.filter.GeoServerSecurityFilter;

/**
 * The only state that the GeoNodeAnonymousProcessingFilter contains is the
 * GeonodeSecurityClient instance. To support testing, we need to swap out
 * the client, so we always return the same instance.
 * 
 * @author Ian Schneider <ischneider@opengeo.org>
 */
public class GeoNodeAnonymousProcessingFilterProvider extends AbstractFilterProvider {
    
    private final GeoNodeAnonymousProcessingFilter filter;
    
    public GeoNodeAnonymousProcessingFilterProvider(GeonodeSecurityClient client) {
        filter = new GeoNodeAnonymousProcessingFilter(client);
    }
    
    public void setClient(GeonodeSecurityClient client) {
        // only called from testing, swap out the client instance in the filter
        filter.setClient(client);
    }

    @Override
    public void configure(XStreamPersister xp) {
        super.configure(xp);
        xp.getXStream().alias("anonymousAuthentication", GeoNodeAnonymousProcessingFilterProvider.class);
    }

    @Override
    public Class<? extends GeoServerSecurityFilter> getFilterClass() {
        return GeoServerAnonymousAuthenticationFilter.class;
    }

    @Override
    public GeoServerSecurityFilter createFilter(SecurityNamedServiceConfig config) {
        return filter;
    }
    
}
