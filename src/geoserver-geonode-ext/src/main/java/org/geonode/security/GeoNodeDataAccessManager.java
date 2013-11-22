/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.util.logging.Level;
import java.util.logging.Logger;

import org.geoserver.catalog.LayerInfo;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.catalog.WorkspaceInfo;
import org.geoserver.platform.GeoServerExtensions;
import org.geoserver.security.AccessMode;
import org.geoserver.security.CatalogMode;
import org.geoserver.security.DataAccessManager;
import org.geoserver.security.GeoServerRoleService;
import org.geoserver.security.GeoServerSecurityManager;
import org.geoserver.security.impl.GeoServerRole;
import org.geotools.util.logging.Logging;
import org.springframework.security.core.Authentication;

/**
 * An access manager that uses the special authentication tokens setup by the
 * {@link GeoNodeSecurityClient} to check if a layer can be accessed, or not
 * 
 * @author Andrea Aime - OpenGeo
 */
public class GeoNodeDataAccessManager implements DataAccessManager {
    private static final Logger LOG = Logging.getLogger(GeoNodeDataAccessManager.class);

    boolean authenticationEnabled = true;
    
    private final GeoNodeSecurityClient.Provider securityClientProvider;

    public GeoNodeDataAccessManager(GeoNodeSecurityClient.Provider securityClientProvider) {
        this.securityClientProvider = securityClientProvider;
    }
    
    public static GeoServerRole getAdminRole() {
        return roleService().getAdminRole();
    }
    
    private static GeoServerSecurityManager securityManager() {
        return GeoServerExtensions.bean(GeoServerSecurityManager.class);
    }
    
    private static GeoServerRoleService roleService() {
        return securityManager().getActiveRoleService();
    }
    
    /**
     * @see org.geoserver.security.DataAccessManager#canAccess(org.springframework.security.Authentication,
     *      org.geoserver.catalog.WorkspaceInfo, org.geoserver.security.AccessMode)
     */
    public boolean canAccess(Authentication user, WorkspaceInfo workspace, AccessMode mode) {
        // we only have access information at the layer level
        return true;
    }

    /**
     * @see org.geoserver.security.DataAccessManager#canAccess(org.springframework.security.Authentication,
     *      org.geoserver.catalog.LayerInfo, org.geoserver.security.AccessMode)
     */
    public boolean canAccess(Authentication user, LayerInfo layer, AccessMode mode) {
        return canAccess(user, layer.getResource(), mode);
    }

    /**
     * @see org.geoserver.security.DataAccessManager#canAccess(org.springframework.security.Authentication,
     *      org.geoserver.catalog.ResourceInfo, org.geoserver.security.AccessMode)
     */
    public boolean canAccess(Authentication user, ResourceInfo resource, AccessMode mode) {
        if (!authenticationEnabled) {
            return true;
        }

        /**
         * A null user should only come from an internal GeoServer process (such as a GWC seed
         * thread).
         * <p>
         * Care must be taken in setting up the security filter chain so that no request can get
         * here with a null user. At least an anonymous authentication token must be set.
         * </p>
         */
        if (user == null) {
            //throw new NullPointerException("user is null");
            return true;
        }
                
        if (LOG.isLoggable(Level.FINER)) {
            LOG.finer("Checking permissions for " + user +" with authorities " + user.getAuthorities() + " accessing " + resource);
        }
        
        if (user.getAuthorities().contains(GeoNodeDataAccessManager.getAdminRole())) {
            return true;
        }
        
        return securityClientProvider.getSecurityClient().authorize(user, resource, mode);
    }

    /**
     * @return {@link CatalogMode#HIDE}
     * @see org.geoserver.security.DataAccessManager#getMode()
     */
    public CatalogMode getMode() {
        return CatalogMode.HIDE;
    }

    /**
     * Used for testing purposes only
     * 
     * @param authenticationEnabled
     */
    public void setAuthenticationEnabled(boolean authenticationEnabled) {
        this.authenticationEnabled = authenticationEnabled;
    }

}
