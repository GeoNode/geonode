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

import org.geoserver.security.GeoServerAuthenticationProvider;
import org.geoserver.security.filter.GeoServerAuthenticationFilter;
import org.geoserver.security.filter.GeoServerSecurityFilter;

import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.geotools.util.logging.Logging;

/**
 * A processing filter that will gather the unauthenticated user privileges from GeoNode's access
 * control list if no {@link Authentication#isAuthenticated() valid} authentication exist in the
 * {@link SecurityContext} already.
 * 
 * @author Gabriel Roldan - OpenGeo
 * 
 */
public class GeoNodeAnonymousProcessingFilter extends GeoServerSecurityFilter implements GeoServerAuthenticationFilter {
    static final Logger LOGGER = Logging.getLogger(GeoNodeAnonymousProcessingFilter.class);

    /**
     * @see javax.servlet.Filter#destroy()
     */
    public void destroy() {
        // nothing to do here
    }

    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        final SecurityContext securityContext = SecurityContextHolder.getContext();
        final Authentication existingAuth = securityContext.getAuthentication();

        final boolean authenticationRequired =
            existingAuth == null || !existingAuth.isAuthenticated();

        if (authenticationRequired) {
            try {
                Object principal = existingAuth == null ? null : existingAuth.getPrincipal();
                Collection<? extends GrantedAuthority> authorities = 
                    existingAuth == null ? null : existingAuth.getAuthorities();
                Authentication authRequest =
                    new AnonymousGeoNodeAuthenticationToken(principal, authorities);
                final Authentication authResult = getSecurityManager().authenticate(authRequest);
                securityContext.setAuthentication(authResult);
                LOGGER.finer("GeoNode Anonymous filter kicked in.");
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
}
