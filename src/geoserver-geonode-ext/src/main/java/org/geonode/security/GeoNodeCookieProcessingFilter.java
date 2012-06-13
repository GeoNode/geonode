/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;
import java.util.Collection;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;

import org.geoserver.security.filter.GeoServerAuthenticationFilter;
import org.geoserver.security.filter.GeoServerSecurityFilter;
import org.geotools.util.logging.Logging;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * A processing filter that will inspect the cookies and look for the GeoNode single sign on one. If
 * that is found, GeoNode will be interrogated to gather the user privileges.
 * 
 * @author Andrea Aime - OpenGeo
 * @author Gabriel Roldan - OpenGeo
 */
public class GeoNodeCookieProcessingFilter extends GeoServerSecurityFilter
    implements GeoServerAuthenticationFilter
{
    static final Logger LOGGER = Logging.getLogger(GeoNodeCookieProcessingFilter.class);
    static final String GEONODE_COOKIE_NAME = "sessionid";

    private GeoNodeSecurityClient client;

    public GeoNodeCookieProcessingFilter(GeoNodeSecurityClient client) {
        this.client = client;
    }

    /**
     * @see javax.servlet.Filter#destroy()
     */
    public void destroy() {
        // nothing to do here
    }

    /**
     * 
     * @see javax.servlet.Filter#doFilter(javax.servlet.ServletRequest,
     *      javax.servlet.ServletResponse, javax.servlet.FilterChain)
     */
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        final HttpServletRequest httpRequest = (HttpServletRequest) request;

        final SecurityContext securityContext = SecurityContextHolder.getContext();
        final Authentication existingAuth = securityContext.getAuthentication();

        final String gnCookie = getGeoNodeCookieValue(httpRequest);
        
        final boolean alreadyAuthenticated = existingAuth != null && existingAuth.isAuthenticated();
        final boolean anonymous = existingAuth instanceof AnonymousAuthenticationToken;
        final boolean hasPreviouslyValidatedGeoNodeCookie =
        		(existingAuth instanceof GeoNodeSessionAuthToken) &&
        		existingAuth.getCredentials().equals(gnCookie);

        // if we still need to authenticate and we find the cookie, consult GeoNode for
        // an authentication
        final boolean authenticationRequired =
            !(alreadyAuthenticated || anonymous || hasPreviouslyValidatedGeoNodeCookie);
        
        if (authenticationRequired && gnCookie != null) {
            try {
                Object principal = existingAuth == null ? null : existingAuth.getPrincipal();
                Collection<? extends GrantedAuthority> authorities = 
                    existingAuth == null ? null : existingAuth.getAuthorities();
                Authentication authRequest = 
                    new GeoNodeSessionAuthToken(principal, gnCookie, authorities);
                final Authentication authResult = getSecurityManager().authenticate(authRequest);
                securityContext.setAuthentication(authResult);
            } catch (AuthenticationException e) {
                // we just go ahead and fall back on basic authentication
                LOGGER.log(
                    Level.WARNING,
                    "Error connecting to the GeoNode server for authentication purposes",
                    e);
            }
        }

        // move forward along the chain
        chain.doFilter(request, response);
    }

    private String getGeoNodeCookieValue(HttpServletRequest request) {
        if (request.getCookies() != null) {
            for (Cookie c : request.getCookies()) {
                if (GEONODE_COOKIE_NAME.equals(c.getName())) {
                    return c.getValue();
                }
            }
        }

        return null;
    }

    /**
     * @param client
     */
    public void setClient(GeoNodeSecurityClient client) {
        this.client = client;
    }

}
