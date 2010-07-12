package org.geonode.security;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.acegisecurity.Authentication;
import org.acegisecurity.AuthenticationException;
import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.GrantedAuthorityImpl;
import org.acegisecurity.providers.UsernamePasswordAuthenticationToken;
import org.geonode.security.LayersGrantedAuthority.LayerMode;

/**
 * A mock security client used to test  
 * @author Andrea Aime - OpenGeo
 *
 */
public class MockSecurityClient implements GeonodeSecurityClient {

    Map<String, Authentication> cookieAuths = new HashMap<String, Authentication>();

    Map<String, Authentication> userAuths = new HashMap<String, Authentication>();

    public Authentication authenticate(String cookieValue) throws AuthenticationException,
            IOException {
        return cookieAuths.get(cookieValue);
    }

    public Authentication authenticate(String username, String password)
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
        cookieAuths.clear();
        userAuths.clear();
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
        if (readOnlyLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readOnlyLayers, LayerMode.READ_ONLY));
        }
        if (readWriteLayers.size() > 0) {
            authorities.add(new LayersGrantedAuthority(readWriteLayers, LayerMode.READ_WRITE));
        }

        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
                username, password, (GrantedAuthority[]) authorities
                        .toArray(new GrantedAuthority[authorities.size()]));
        return token;
    }
}
