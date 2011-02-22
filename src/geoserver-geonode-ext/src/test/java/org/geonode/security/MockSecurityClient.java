package org.geonode.security;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.security.Authentication;
import org.springframework.security.AuthenticationException;
import org.springframework.security.GrantedAuthority;
import org.springframework.security.GrantedAuthorityImpl;
import org.springframework.security.providers.UsernamePasswordAuthenticationToken;
import org.springframework.security.providers.anonymous.AnonymousAuthenticationToken;
import org.geonode.security.LayersGrantedAuthority.LayerMode;

/**
 * A mock security client used to test
 * 
 * @author Andrea Aime - OpenGeo
 * 
 */
public class MockSecurityClient implements GeonodeSecurityClient {

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
        anonymousAuth = new AnonymousAuthenticationToken("geonode", "anonymous",
                new GrantedAuthority[] { new GrantedAuthorityImpl("ROLE_ANONYMOUS") });
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
            authorities.add(new GrantedAuthorityImpl(GeoNodeDataAccessManager.ADMIN_ROLE));
        }
        if (readOnlyLayers != null && readOnlyLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readOnlyLayers, LayerMode.READ_ONLY));
        }
        if (readWriteLayers != null && readWriteLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readWriteLayers, LayerMode.READ_WRITE));
        }

        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
                username, password,
                (GrantedAuthority[]) authorities.toArray(new GrantedAuthority[authorities.size()]));
        return token;
    }

    public void setAnonymousRights(boolean admin, List<String> readOnlyLayers,
            List<String> readWriteLayers) {
        List<GrantedAuthority> authorities = new ArrayList<GrantedAuthority>();
        authorities.add(new GrantedAuthorityImpl("ROLE_ANONYMOUS"));
        if (admin) {
            authorities.add(new GrantedAuthorityImpl(GeoNodeDataAccessManager.ADMIN_ROLE));
        }
        if (readOnlyLayers != null && readOnlyLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readOnlyLayers, LayerMode.READ_ONLY));
        }
        if (readWriteLayers != null && readWriteLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readWriteLayers, LayerMode.READ_WRITE));
        }

        anonymousAuth = new AnonymousAuthenticationToken("geonode", "anonymous",
                (GrantedAuthority[]) authorities.toArray(new GrantedAuthority[authorities.size()]));
    }

    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        return anonymousAuth;
    }
}
