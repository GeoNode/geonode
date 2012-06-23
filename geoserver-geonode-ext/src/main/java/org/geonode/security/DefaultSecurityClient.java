/* Copyright (c) 2010 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import static org.geonode.security.GeoNodeCookieProcessingFilter.GEONODE_COOKIE_NAME;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.apache.commons.codec.binary.Base64;
import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.geotools.util.logging.Logging;
import org.springframework.context.ApplicationContext;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.util.Assert;

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
public class DefaultSecurityClient implements GeoNodeSecurityClient {
    static final Logger LOGGER = Logging.getLogger(DefaultSecurityClient.class);

    private final HTTPClient client;

    private String baseUrl;

    /**
     * Caches anonymous and cookie based authorizations for a given time
     */
    private final AuthCache authCache;

    /**
     * Used by {@link #authenticateAnonymous()} and {@link #authenticateCookie(String)} to update
     * {@link #authCache}
     */
    private Lock authLock = new ReentrantLock();

    public DefaultSecurityClient(String baseUrl, final HTTPClient httpClient) {
        this.client = httpClient;
        this.authCache = new AuthCache();
        this.baseUrl = baseUrl;
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
     * @see org.geonode.security.GeoNodeSecurityClient#authenticateCookie(java.lang.String)
     */
    public Authentication authenticateCookie(final String cookieValue)
            throws AuthenticationException, IOException {
        Assert.notNull(cookieValue);
        
        Authentication cachedAuth = authCache.get(cookieValue);
        if (null == cachedAuth) {
            authLock.lock();
            try {
                // got the lock, check again
                cachedAuth = authCache.get(cookieValue);
                if (null == cachedAuth) {

                    final String headerName = "Cookie";
                    final String headerValue = GEONODE_COOKIE_NAME + "=" + cookieValue;

                    cachedAuth = authenticate(cookieValue, headerName, headerValue);
                    if (cachedAuth instanceof UsernamePasswordAuthenticationToken) {
                        cachedAuth = new GeoNodeSessionAuthToken(cachedAuth.getPrincipal(),
                                cachedAuth.getCredentials(), cachedAuth.getAuthorities());
                    }
                    authCache.put(cookieValue, cachedAuth);
                }
            } finally {
                authLock.unlock();
            }
        }

        return cachedAuth;
    }

    /**
     * @see org.geonode.security.GeoNodeSecurityClient#authenticateUserPwd(java.lang.String,
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
     * @see org.geonode.security.GeoNodeSecurityClient#authenticateAnonymous()
     */
    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        Authentication cachedAuth = authCache.get("__anonymous__");
        if (null == cachedAuth) {
            authLock.lock();
            try {
                // got the lock, check again
                cachedAuth = authCache.get("__anonymous__");
                if (null == cachedAuth) {
                    cachedAuth = authenticate(null, (String[]) null);
                    authCache.put("__anonymous__", cachedAuth);
                }
            } finally {
                authLock.unlock();
            }
        }
        return cachedAuth;
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
            authorities.add(new SimpleGrantedAuthority(GeoNodeDataAccessManager.getActiveAdminRole()));
        }

        final Authentication authentication;

        if (json.getBoolean("is_anonymous")) {
            authorities.add(new SimpleGrantedAuthority("ROLE_ANONYMOUS"));
            String key = "geonode";
            Object principal = "anonymous";

            authentication = new AnonymousAuthenticationToken(key, principal, authorities);
        } else {
            String userName = "";
            if (json.containsKey("name")) {
                userName = json.getString("name");
            }

            authentication = new UsernamePasswordAuthenticationToken(userName, credentials,
                    authorities);
        }
        return authentication;
    }
}
