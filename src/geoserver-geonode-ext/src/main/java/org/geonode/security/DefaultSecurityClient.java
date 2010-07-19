/* Copyright (c) 2001 - 2007 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, availible at the root
 * application directory.
 */
package org.geonode.security;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;

import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;
import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.GrantedAuthorityImpl;
import org.acegisecurity.providers.UsernamePasswordAuthenticationToken;
import org.acegisecurity.providers.anonymous.AnonymousAuthenticationToken;
import org.apache.commons.codec.binary.Base64;
import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.MultiThreadedHttpConnectionManager;
import org.apache.commons.httpclient.methods.GetMethod;
import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.geoserver.platform.GeoServerExtensions;
import org.geotools.util.logging.Logging;
import org.springframework.beans.BeansException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;

/**
 * Default implementation, which actually talks to a GeoNode server (there are also mock
 * implementations used for testing the whole machinery without a running GeoNode instance)
 * 
 * @author Andrea Aime - OpenGeo
 */
public class DefaultSecurityClient implements GeonodeSecurityClient, ApplicationContextAware {
    static final Logger LOGGER = Logging.getLogger(DefaultSecurityClient.class);

    HttpClient client;

    String baseUrl;

    public DefaultSecurityClient() {
        MultiThreadedHttpConnectionManager httpConnectionManager = new MultiThreadedHttpConnectionManager();
        httpConnectionManager.getParams().setConnectionTimeout(1000);
        httpConnectionManager.getParams().setSoTimeout(1000);
        client = new HttpClient(httpConnectionManager);
    }

    public Authentication authenticate(String cookieValue) throws AuthenticationException,
            IOException {
        GetMethod get = new GetMethod(baseUrl + "data/acls");
        try {
            get.addRequestHeader("Cookie", GeoNodeCookieProcessingFilter.GEONODE_COOKIE_NAME + "="
                    + cookieValue);
            get.setFollowRedirects(true);
            int status = client.executeMethod(get);

            if (status != 200) {
                throw new IOException("GeoNode communication failed, status report is: " + status
                        + ", " + get.getStatusText());
            }

            String response = get.getResponseBodyAsString();
            JSONObject json = (JSONObject) JSONSerializer.toJSON(response);
            return toAuthentication(json);
        } finally {
            get.releaseConnection();
        }
    }

    public Authentication authenticate(String username, String password)
            throws AuthenticationException, IOException {
        GetMethod get = new GetMethod(baseUrl + "data/acls");
        try {
            get.addRequestHeader("Authorization", "Basic "
                    + new String(Base64.encodeBase64((username + ":" + password).getBytes())));
            get.setFollowRedirects(true);
            int status = client.executeMethod(get);

            if (status != 200) {
                throw new IOException("GeoNode communication failed, status report is: " + status
                        + ", " + get.getStatusText());
            }

            JSONObject json = (JSONObject) JSONSerializer.toJSON(get.getResponseBodyAsString());
            return toAuthentication(json);

        } finally {
            get.releaseConnection();
        }
    }
    
    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        GetMethod get = new GetMethod(baseUrl + "data/acls");
        try {
            get.setFollowRedirects(true);
            int status = client.executeMethod(get);

            if (status != 200) {
                throw new IOException("GeoNode communication failed, status report is: " + status
                        + ", " + get.getStatusText());
            }

            JSONObject json = (JSONObject) JSONSerializer.toJSON(get.getResponseBodyAsString());
            return toAuthentication(json);

        } finally {
            get.releaseConnection();
        }
    }

    private Authentication toAuthentication(JSONObject json) {
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        JSONArray roLayers = json.getJSONArray("ro");
        if (roLayers != null) {
            authorities.add(new LayersGrantedAuthority(new ArrayList<String>(roLayers),
                    LayerMode.READ_ONLY));
        }
        JSONArray rwLayers = json.getJSONArray("rw");
        if (rwLayers != null) {
            authorities.add(new LayersGrantedAuthority(new ArrayList<String>(rwLayers),
                    LayerMode.READ_ONLY));
        }
        if (json.getBoolean("is_superuser")) {
            authorities.add(new GrantedAuthorityImpl(GeoNodeDataAccessManager.ADMIN_ROLE));
        }

        if(json.getBoolean("is_anonymous")) {
            authorities.add(new GrantedAuthorityImpl("ROLE_ANONYMOUS"));
            return new AnonymousAuthenticationToken("geonode", "anonymous", (GrantedAuthority[]) authorities
                    .toArray(new GrantedAuthority[authorities.size()]));
        } else {
            return new UsernamePasswordAuthenticationToken("", null, (GrantedAuthority[]) authorities
                    .toArray(new GrantedAuthority[authorities.size()]));
        }
    }

    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        // determine where geonode is
        this.baseUrl = GeoServerExtensions.getProperty("GEONODE_BASE_URL", applicationContext);
        if (baseUrl == null) {
            LOGGER.log(Level.WARNING, "GEONODE_BASE_URL is not set, "
                    + "assuming http://locahost:8000/");
            baseUrl = "http://localhost:8000/";
        }
        if (!baseUrl.endsWith("/")) {
            baseUrl += "/";
        }
    }

    

}
