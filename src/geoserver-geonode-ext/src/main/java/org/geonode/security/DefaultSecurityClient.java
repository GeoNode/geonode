/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;

import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;

/**
 * Default implementation, which actually talks to a GeoNode server (there are also mock
 * implementations used for testing the whole machinery without a running GeoNode instance)
 * 
 * @author Andrea Aime - OpenGeo
 */
public class DefaultSecurityClient implements GeonodeSecurityClient {

    public Authentication authenticate(String cookieValue) throws AuthenticationException,
            IOException {
        return null;
    }

    public Authentication authenticate(String username, String password)
            throws AuthenticationException, IOException {
        return null;
    }

}
