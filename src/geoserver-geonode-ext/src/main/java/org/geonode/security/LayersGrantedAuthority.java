/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.acegisecurity.GrantedAuthority;

/**
 * An authority marking the user credentials read/only and read/write access to layers
 * 
 * @author Andrea Aime - OpenGeo
 */
public class LayersGrantedAuthority implements GrantedAuthority {

    private static final long serialVersionUID = 3234834124752682694L;

    public enum LayerMode {
        READ_ONLY, READ_WRITE
    };

    private final List<String> layerNames;

    private final LayerMode accessMode;

    public LayersGrantedAuthority(final List<String> layerNames, final LayerMode accessMode) {
        super();
        this.layerNames = Collections.unmodifiableList(new ArrayList<String>(layerNames));
        this.accessMode = accessMode;
    }

    public LayerMode getAccessMode() {
        return accessMode;
    }

    public List<String> getLayerNames() {
        return layerNames;
    }

    /**
     * This is not a role, so we return {@code null}, by API spec.
     * 
     * @return {@code null}
     * @see org.acegisecurity.GrantedAuthority#getAuthority()
     */
    public String getAuthority() {
        return null;
    }

}
