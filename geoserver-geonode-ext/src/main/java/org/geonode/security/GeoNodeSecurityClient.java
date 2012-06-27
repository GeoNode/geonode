/* Copyright (c) 2010 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.authentication.AnonymousAuthenticationToken;

/**
 * A client that talks to GeoNode to authenticate the users based on cookies contents or
 * username/password
 * 
 * @author Andrea Aime - OpenGeo
 */
public interface GeoNodeSecurityClient {

    /**
     * Authenticates a user based on cookie contents
     * 
     * @param gnCookie
     * @return either a {@link GeoNodeSessionAuthToken} or an {@link AnonymousAuthenticationToken},
     *         depending on whether GeoNode knows about the {@code sessionid} with value
     *         {@code cookieValue} or not.
     * @throws AuthenticationException
     * @throws IOException
     */
    public Authentication authenticateCookie(String cookieValue) throws AuthenticationException,
            IOException;

    /**
     * Gets the authentication for an anonymous user
     * 
     * @param gnCookie
     * @return
     * @throws AuthenticationException
     * @throws IOException
     */
    public Authentication authenticateAnonymous() throws AuthenticationException, IOException;

    /**
     * Authenticates based on username/password
     * 
     * @param username
     * @param password
     * @return
     * @throws AuthenticationException
     * @throws IOException
     */
    public Authentication authenticateUserPwd(String username, String password)
            throws AuthenticationException, IOException;

}
