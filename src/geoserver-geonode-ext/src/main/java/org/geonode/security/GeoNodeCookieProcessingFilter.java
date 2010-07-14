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
import javax.servlet.http.HttpServletResponse;

import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;
import org.acegisecurity.context.SecurityContextHolder;
import org.acegisecurity.ui.rememberme.RememberMeServices;
import org.apache.ftpserver.usermanager.AnonymousAuthentication;
import org.geotools.util.logging.Logging;

/**
 * A processing filter that will inspect the cookies and look for the GeoNode single sign on one. If
 * that is found, GeoNode will be interrogated to gather the user privileges.
 * 
 * @author Andrea Aime - OpenGeo
 * 
 */
public class GeoNodeCookieProcessingFilter implements Filter {

    static final Logger LOGGER = Logging.getLogger(GeoNodeCookieProcessingFilter.class);

    static final String GEONODE_COOKIE_NAME = "sessionid";

    GeonodeSecurityClient client;

    private RememberMeServices rememberMeServices;

    public GeoNodeCookieProcessingFilter(GeonodeSecurityClient client) {
        this.client = client;
    }

    public void destroy() {
        // nothing to do here
    }

    public void init(FilterConfig filterConfig) throws ServletException {
        // nothing to do here
    }

    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        Authentication existingAuth = SecurityContextHolder.getContext().getAuthentication();
        Cookie gnCookie = getGeoNodeCookie(httpRequest);

        // if we still need to authenticate and we find the cookie, consult GeoNode for
        // an authentication
        boolean authenticationRequired = existingAuth == null || !existingAuth.isAuthenticated()
                || (existingAuth instanceof AnonymousAuthentication);
        if (authenticationRequired) {
            try {
                if (gnCookie != null) {

                    Authentication authResult = client.authenticate(gnCookie.getValue());

                    SecurityContextHolder.getContext().setAuthentication(authResult);

                    if (rememberMeServices != null) {
                        rememberMeServices.loginSuccess(httpRequest, httpResponse, authResult);
                    }
                } else {
                    Authentication authResult = client.authenticateAnonymous();

                    SecurityContextHolder.getContext().setAuthentication(authResult);

                    if (rememberMeServices != null) {
                        rememberMeServices.loginSuccess(httpRequest, httpResponse, authResult);
                    }
                }
            } catch (AuthenticationException e) {
                // we just go ahead and fall back on basic authentication
            } catch (IOException e) {
                LOGGER.log(Level.WARNING,
                        "Error connecting to the GeoNode server for authentication purposes", e);
            }
        }

        // move forward along the chain
        chain.doFilter(request, response);
    }

    Cookie getGeoNodeCookie(HttpServletRequest request) {
        if (request.getCookies() != null) {
            for (Cookie c : request.getCookies()) {
                if (GEONODE_COOKIE_NAME.equals(c.getName())) {
                    return c;
                }
            }
        }

        return null;
    }

    public void setRememberMeServices(RememberMeServices rememberMeServices) {
        this.rememberMeServices = rememberMeServices;
    }

    public void setClient(GeonodeSecurityClient client) {
        this.client = client;
    }

}
