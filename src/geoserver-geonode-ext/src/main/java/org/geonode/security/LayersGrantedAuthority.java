/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.util.List;

import org.acegisecurity.GrantedAuthority;

/**
 * An authority marking the user
 * 
 * @author Andrea Aime - OpenGeo
 */
public class LayersGrantedAuthority implements GrantedAuthority {

    public enum LayerMode {
        READ_ONLY, READ_WRITE
    };

    List<String> layerNames;

    LayerMode accessMode;

    public LayersGrantedAuthority(List<String> layerNames, LayerMode accessMode) {
        super();
        this.layerNames = layerNames;
        this.accessMode = accessMode;
    }

    public LayerMode getAccessMode() {
        return accessMode;
    }

    public List<String> getLayerNames() {
        return layerNames;
    }

    public String getAuthority() {
        return null; // this is not a role, so we return null, by API spec
    }

}
