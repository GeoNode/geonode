/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.geotools.util.logging.Logging;

/**
 * A processing filter that will inspect the cookies and look for the GeoNode single sign on one. If
 * that is found, GeoNode will be interrogated to gather the user privileges.
 * 
 * @author Andrea Aime - OpenGeo
 * @author Gabriel Roldan - OpenGeo
 */
public class GeoNodeCookieProcessingFilter implements Filter {

    static final Logger LOGGER = Logging.getLogger(GeoNodeCookieProcessingFilter.class);

    static final String GEONODE_COOKIE_NAME = "sessionid";

    private GeonodeSecurityClient client;

    public GeoNodeCookieProcessingFilter(GeonodeSecurityClient client) {
        this.client = client;
    }

    /**
     * @see javax.servlet.Filter#destroy()
     */
    public void destroy() {
        // nothing to do here
    }

    /**
     * @see javax.servlet.Filter#init(javax.servlet.FilterConfig)
     */
    public void init(FilterConfig filterConfig) throws ServletException {
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

        // if we still need to authenticate and we find the cookie, consult GeoNode for
        // an authentication
        final boolean authenticationRequired;
        if (existingAuth == null || !existingAuth.isAuthenticated()
                || (existingAuth instanceof AnonymousAuthenticationToken)) {
            authenticationRequired = true;
        } else if (existingAuth instanceof GeoNodeSessionAuthToken) {
            Object credentials = existingAuth.getCredentials();
            boolean stillValid = gnCookie != null && gnCookie.equals(credentials);
            existingAuth.setAuthenticated(stillValid);
            authenticationRequired = !stillValid;
        } else {
            authenticationRequired = false;
        }

        if (authenticationRequired && gnCookie != null) {
            try {
                final Authentication authResult;
                authResult = client.authenticateCookie(gnCookie);
                securityContext.setAuthentication(authResult);

            } catch (AuthenticationException e) {
                // we just go ahead and fall back on basic authentication
            } catch (IOException e) {
                LOGGER.log(Level.WARNING,
                        "Error connecting to the GeoNode server for authentication purposes", e);
                // throw new ServletException("Error connecting to GeoNode authentication server: "
                // + e.getMessage(), e);
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
    public void setClient(GeonodeSecurityClient client) {
        this.client = client;
    }

}
