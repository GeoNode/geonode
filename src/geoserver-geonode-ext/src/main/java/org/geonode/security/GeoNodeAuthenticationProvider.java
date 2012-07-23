/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;

import org.springframework.security.Authentication;
import org.springframework.security.AuthenticationException;
import org.springframework.security.AuthenticationServiceException;
import org.springframework.security.providers.AuthenticationProvider;
import org.springframework.security.providers.UsernamePasswordAuthenticationToken;
import org.springframework.util.Assert;

/**
 * An {@link AuthenticationProvider} provider passing the username/password to GeoNode for
 * authentication
 * 
 * @author Andrea Aime - OpenGeo
 * 
 */
public class GeoNodeAuthenticationProvider implements AuthenticationProvider {

    private GeonodeSecurityClient client;

    public GeoNodeAuthenticationProvider(GeonodeSecurityClient client) {
        this.client = client;
    }

    /**
     * @see org.springframework.security.providers.AuthenticationProvider#authenticate(org.acegisecurity.Authentication)
     */
    public Authentication authenticate(Authentication authentication)
            throws AuthenticationException {
        Assert.isInstanceOf(UsernamePasswordAuthenticationToken.class, authentication,
                "authentication shall be a UsernamePasswordAuthenticationToken");
        UsernamePasswordAuthenticationToken token = (UsernamePasswordAuthenticationToken) authentication;
        String username = token.getName();
        String password = (String) token.getCredentials();

        try {
            return client.authenticateUserPwd(username, password);
        } catch (IOException e) {
            throw new AuthenticationServiceException("Communication with GeoNode failed", e);
        }
    }

    /**
     * @see org.springframework.security.providers.AuthenticationProvider#supports(java.lang.Class)
     */
    public boolean supports(Class authentication) {
        return (UsernamePasswordAuthenticationToken.class.isAssignableFrom(authentication));
    }

    /**
     * 
     * @param client
     */
    public void setClient(GeonodeSecurityClient client) {
        this.client = client;
    }

}
