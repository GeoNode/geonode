/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.springframework.security.GrantedAuthority;

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
     * @see org.springframework.security.GrantedAuthority#getAuthority()
     */
    public String getAuthority() {
        return null;
    }

    public int compareTo(Object o) {
        if (!(o instanceof LayersGrantedAuthority)) {
            return 0;
        }

        LayersGrantedAuthority that = (LayersGrantedAuthority) o;

        if (this.accessMode != that.accessMode) {
            List<LayerMode> modes = Arrays.asList(LayerMode.values());
            return modes.indexOf(this.accessMode) - modes.indexOf(that.accessMode);
        }

        if (this.layerNames.size() != that.layerNames.size()) {
            return this.layerNames.size() - that.layerNames.size();
        } else {
            for (int i = 0; i < this.layerNames.size(); i++) {
                int comparison = this.layerNames.get(i).compareTo(that.layerNames.get(i));
                if (comparison != 0)
                    return comparison;
            }
        }

        return 0;
    }

}
