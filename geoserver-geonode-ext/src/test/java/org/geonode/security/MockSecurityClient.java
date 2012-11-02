package org.geonode.security;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.geonode.security.LayersGrantedAuthority.LayerMode;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.security.AccessMode;
import org.geoserver.security.impl.GeoServerRole;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;

/**
 * A mock security client used to test
 * 
 * @author Andrea Aime - OpenGeo
 * 
 */
public class MockSecurityClient implements GeoNodeSecurityClient {

    Map<String, Authentication> cookieAuths;

    Map<String, Authentication> userAuths;

    AnonymousAuthenticationToken anonymousAuth;

    public MockSecurityClient() {
        reset();
    }

    public Authentication authenticateCookie(String cookieValue) throws AuthenticationException,
            IOException {
        return cookieAuths.get(cookieValue);
    }

    public Authentication authenticateUserPwd(String username, String password)
            throws AuthenticationException, IOException {
        Authentication auth = userAuths.get(username);
        if (auth != null) {
            if (password.equals(auth.getCredentials())) {
                return auth;
            }
        }
        return null;
    }

    public void reset() {
        cookieAuths = new HashMap<String, Authentication>();
        userAuths = new HashMap<String, Authentication>();
        
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>(1);
        authorities.add(GeoServerRole.ANONYMOUS_ROLE);
        anonymousAuth = new AnonymousAuthenticationToken("geonode", "anonymous", authorities);
    }

    public void addUserAuth(String username, String password, boolean admin,
            List<String> readOnlyLayers, List<String> readWriteLayers) {
        UsernamePasswordAuthenticationToken token = buildUser(username, password, admin,
                readOnlyLayers, readWriteLayers);
        userAuths.put(username, token);
    }

    public void addCookieAuth(String cookieValue, String username, boolean admin,
            List<String> readOnlyLayers, List<String> readWriteLayers) {
        UsernamePasswordAuthenticationToken token = buildUser(username, null, admin,
                readOnlyLayers, readWriteLayers);
        cookieAuths.put(cookieValue, token);
    }

    UsernamePasswordAuthenticationToken buildUser(String username, String password, boolean admin,
            List<String> readOnlyLayers, List<String> readWriteLayers) {
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        if (admin) {
            authorities.add(GeoNodeDataAccessManager.getAdminRole());
        }
        if (readOnlyLayers != null && readOnlyLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readOnlyLayers, LayerMode.READ_ONLY));
        }
        if (readWriteLayers != null && readWriteLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readWriteLayers, LayerMode.READ_WRITE));
        }

        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
                username, password, authorities);
        return token;
    }

    public void setAnonymousRights(boolean admin, List<String> readOnlyLayers,
            List<String> readWriteLayers) {
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        authorities.add(GeoServerRole.ANONYMOUS_ROLE);
        if (admin) {
            authorities.add(GeoNodeDataAccessManager.getAdminRole());
        }
        if (readOnlyLayers != null && readOnlyLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readOnlyLayers, LayerMode.READ_ONLY));
        }
        if (readWriteLayers != null && readWriteLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readWriteLayers, LayerMode.READ_WRITE));
        }

        anonymousAuth = new AnonymousAuthenticationToken("geonode", "anonymous", authorities);
    }

    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        return anonymousAuth;
    }
    
    public boolean authorize(Authentication user, ResourceInfo resource, AccessMode mode) {
        return DefaultSecurityClient.authorizeUsingAuthorities(user, resource, mode);
    }
}
