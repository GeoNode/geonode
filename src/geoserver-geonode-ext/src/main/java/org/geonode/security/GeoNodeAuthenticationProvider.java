/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;

import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;
import org.acegisecurity.AuthenticationServiceException;
import org.acegisecurity.providers.AuthenticationProvider;
import org.acegisecurity.providers.UsernamePasswordAuthenticationToken;

/**
 * An authentication provider passing the username/password to GeoNode for authentication
 * 
 * @author Andrea Aime - OpenGeo
 * 
 */
public class GeoNodeAuthenticationProvider implements AuthenticationProvider {

    GeonodeSecurityClient client;

    public GeoNodeAuthenticationProvider(GeonodeSecurityClient client) {
        this.client = client;
    }

    public Authentication authenticate(Authentication authentication)
            throws AuthenticationException {
        UsernamePasswordAuthenticationToken token = (UsernamePasswordAuthenticationToken) authentication;
        String username = token.getName();
        String password = (String) token.getCredentials();

        try {
            return client.authenticateUserPwd(username, password);
        } catch (IOException e) {
            throw new AuthenticationServiceException("Communication with GeoNode failed", e);
        }
    }

    public boolean supports(Class authentication) {
        return (UsernamePasswordAuthenticationToken.class.isAssignableFrom(authentication));
    }

    public void setClient(GeonodeSecurityClient client) {
        this.client = client;
    }

}
