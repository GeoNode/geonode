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


import org.springframework.security.Authentication;
import org.springframework.security.AuthenticationException;
import org.springframework.security.context.SecurityContext;
import org.springframework.security.context.SecurityContextHolder;
import org.geotools.util.logging.Logging;

/**
 * A processing filter that will gather the unauthenticated user privileges from GeoNode's access
 * control list if no {@link Authentication#isAuthenticated() valid} authentication exist in the
 * {@link SecurityContext} already.
 * 
 * @author Gabriel Roldan - OpenGeo
 * 
 */
public class GeoNodeAnonymousProcessingFilter implements Filter {

    static final Logger LOGGER = Logging.getLogger(GeoNodeAnonymousProcessingFilter.class);

    private GeonodeSecurityClient client;

    public GeoNodeAnonymousProcessingFilter(GeonodeSecurityClient client) {
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

        final SecurityContext securityContext = SecurityContextHolder.getContext();
        final Authentication existingAuth = securityContext.getAuthentication();

        final boolean authenticationRequired = existingAuth == null
                || !existingAuth.isAuthenticated();

        if (authenticationRequired) {

            try {
                final Authentication authResult;

                authResult = client.authenticateAnonymous();

                securityContext.setAuthentication(authResult);

            } catch (AuthenticationException e) {
                // Auth is mandatory in GeoNode security integration even for anonymous as GeoNode
                // controls the access to resources for unauthenticated users, so propagate and let
                // geonodeOwsExceptionTranslationFilter handle this
                throw e;
            } catch (IOException e) {
                LOGGER.log(Level.WARNING,
                        "Error connecting to the GeoNode server for authentication purposes", e);
                throw new ServletException("Error connecting to GeoNode authentication server: "
                        + e.getMessage(), e);
            }
        }

        // move forward along the chain
        chain.doFilter(request, response);
    }

    /**
     * @param client
     */
    public void setClient(GeonodeSecurityClient client) {
        this.client = client;
    }

}
