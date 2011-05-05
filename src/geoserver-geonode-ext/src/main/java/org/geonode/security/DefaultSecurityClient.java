/* Copyright (c) 2010 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

<<<<<<< HEAD
import org.springframework.security.Authentication;
import org.springframework.security.AuthenticationException;
import org.springframework.security.GrantedAuthority;
import org.springframework.security.GrantedAuthorityImpl;
import org.springframework.security.providers.UsernamePasswordAuthenticationToken;
import org.springframework.security.providers.anonymous.AnonymousAuthenticationToken;
=======
import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;
import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.GrantedAuthorityImpl;
import org.acegisecurity.providers.UsernamePasswordAuthenticationToken;
import org.acegisecurity.providers.anonymous.AnonymousAuthenticationToken;
>>>>>>> 62e10950604c85ea2fec4f0bb54c420c0ea66ed4
import org.apache.commons.codec.binary.Base64;
import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.geoserver.platform.GeoServerExtensions;
import org.geotools.util.logging.Logging;
import org.springframework.beans.BeansException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;

/**
 * Default implementation, which actually talks to a GeoNode server (there are also mock
 * implementations used for testing the whole machinery without a running GeoNode instance)
 * <p>
 * The GeoNode access control list endpoint is resolved at
 * {@link #setApplicationContext(ApplicationContext)}
 * </p>
 * 
 * @author Andrea Aime - OpenGeo
 */
public class DefaultSecurityClient implements GeonodeSecurityClient, ApplicationContextAware {
    static final Logger LOGGER = Logging.getLogger(DefaultSecurityClient.class);

    private final HTTPClient client;

    private String baseUrl;

    public DefaultSecurityClient(final HTTPClient httpClient) {
        this.client = httpClient;
    }

    /**
     * Package protected accessor to baseUrl for test purposes only
     * 
     * @return
     */
    String getBaseUrl() {
        return baseUrl;
    }

    /**
     * @see org.geonode.security.GeonodeSecurityClient#authenticateCookie(java.lang.String)
     */
    public Authentication authenticateCookie(final String cookieValue)
            throws AuthenticationException, IOException {

        final String headerName = "Cookie";
        final String headerValue = GeoNodeCookieProcessingFilter.GEONODE_COOKIE_NAME + "="
                + cookieValue;

        Authentication authentication = authenticate(cookieValue, headerName, headerValue);
        if (authentication instanceof UsernamePasswordAuthenticationToken) {
            authentication = new GeoNodeSessionAuthToken(authentication.getPrincipal(),
                    authentication.getCredentials(), authentication.getAuthorities());
        }
        return authentication;
    }

    /**
     * @see org.geonode.security.GeonodeSecurityClient#authenticateUserPwd(java.lang.String,
     *      java.lang.String)
     */
    public Authentication authenticateUserPwd(String username, String password)
            throws AuthenticationException, IOException {
        final String headerName = "Authorization";
        final String headerValue = "Basic "
                + new String(Base64.encodeBase64((username + ":" + password).getBytes()));

        return authenticate(password, headerName, headerValue);
    }

    /**
     * @see org.geonode.security.GeonodeSecurityClient#authenticateAnonymous()
     */
    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        return authenticate(null, (String[]) null);
    }

    private Authentication authenticate(final Object credentials, final String... requestHeaders)
            throws AuthenticationException, IOException {

        final String url = baseUrl + "data/acls";

        if (LOGGER.isLoggable(Level.FINEST)) {
            LOGGER.finest("Authenticating with " + Arrays.toString(requestHeaders));
        }
        final String responseBodyAsString = client.sendGET(url, requestHeaders);
        if (LOGGER.isLoggable(Level.FINEST)) {
            LOGGER.finest("Auth response: " + responseBodyAsString);
        }

        JSONObject json = (JSONObject) JSONSerializer.toJSON(responseBodyAsString);
        Authentication authentication = toAuthentication(credentials, json);
        return authentication;
    }

    @SuppressWarnings("unchecked")
    private Authentication toAuthentication(Object credentials, JSONObject json) {
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        if (json.containsKey("ro")) {
            JSONArray roLayers = json.getJSONArray("ro");
            authorities.add(new LayersGrantedAuthority(roLayers, LayerMode.READ_ONLY));
        }
        if (json.containsKey("rw")) {
            JSONArray rwLayers = json.getJSONArray("rw");
            authorities.add(new LayersGrantedAuthority(rwLayers, LayerMode.READ_WRITE));
        }
        if (json.getBoolean("is_superuser")) {
            authorities.add(new GrantedAuthorityImpl(GeoNodeDataAccessManager.ADMIN_ROLE));
        }

        final Authentication authentication;

        if (json.getBoolean("is_anonymous")) {
            authorities.add(new GrantedAuthorityImpl("ROLE_ANONYMOUS"));
            String key = "geonode";
            Object principal = "anonymous";
            GrantedAuthority[] grantedAuthorities = authorities
                    .toArray(new GrantedAuthority[authorities.size()]);

            authentication = new AnonymousAuthenticationToken(key, principal, grantedAuthorities);
        } else {
            String userName = "";
            if (json.containsKey("name")) {
                userName = json.getString("name");
            }
            GrantedAuthority[] grantedAuthorities = authorities
                    .toArray(new GrantedAuthority[authorities.size()]);

            authentication = new UsernamePasswordAuthenticationToken(userName, credentials,
                    grantedAuthorities);
        }
        return authentication;
    }

    /**
     * Looks up for the {@code GEONODE_BASE_URL} property (either a System property, a servlet
     * context parameter or an environment variable) to be used as the base URL for the GeoNode
     * authentication requests (for which {@code 'data/acls'} will be appended).
     * <p>
     * If not provided, defaults to {@code http://localhost:8000}
     * </p>
     * 
     * @see org.springframework.context.ApplicationContextAware#setApplicationContext(org.springframework.context.ApplicationContext)
     * @see GeoServerExtensions#getProperty(String, ApplicationContext)
     */
    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        // determine where geonode is
        this.baseUrl = GeoServerExtensions.getProperty("GEONODE_BASE_URL", applicationContext);
        if (baseUrl == null) {
            LOGGER.log(Level.WARNING, "GEONODE_BASE_URL is not set, "
                    + "assuming http://localhost:8000/");
            baseUrl = "http://localhost:8000/";
        }
        if (!baseUrl.endsWith("/")) {
            baseUrl += "/";
        }
    }

}
