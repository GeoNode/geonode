/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import org.springframework.security.Authentication;
import org.springframework.security.GrantedAuthority;
import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.geoserver.catalog.LayerInfo;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.catalog.WorkspaceInfo;
import org.geoserver.security.AccessMode;
import org.geoserver.security.CatalogMode;
import org.geoserver.security.DataAccessManager;

/**
 * An access manager that uses the special authentication tokens setup by the
 * {@link GeonodeSecurityClient} to check if a layer can be accessed, or not
 * 
 * @author Andrea Aime - OpenGeo
 */
public class GeoNodeDataAccessManager implements DataAccessManager {

    public static final String ADMIN_ROLE = "ROLE_ADMINISTRATOR";

    boolean authenticationEnabled = true;

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

        if (user != null && user.getAuthorities() != null) {
            for (GrantedAuthority ga : user.getAuthorities()) {
                if (ga instanceof LayersGrantedAuthority) {
                    LayersGrantedAuthority lga = ((LayersGrantedAuthority) ga);
                    // see if the layer is contained in the granted authority list with
                    // sufficient privileges
                    if (mode == AccessMode.READ
                            || ((mode == AccessMode.WRITE) && lga.getAccessMode() == LayerMode.READ_WRITE)) {
                        if (lga.getLayerNames().contains(resource.getPrefixedName())) {
                            return true;
                        }
                    }
                } else if (ADMIN_ROLE.equals(ga.getAuthority())) {
                    // admin is all powerful
                    return true;
                }
            }
        }
        // if we got here sorry, no luck
        return false;
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
