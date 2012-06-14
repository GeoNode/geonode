package org.geonode.security;

import java.util.Collection;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.authentication.AbstractAuthenticationToken;

public class GeoNodeSessionAuthToken extends AbstractAuthenticationToken {

    /**
     * 
     */
    private static final long serialVersionUID = -3781584924355064548L;

    private Object principal;

    private Object credentials;

    public GeoNodeSessionAuthToken(Object principal, Object credentials,
            Collection<? extends GrantedAuthority> authorities) {
        super(authorities);
        super.setAuthenticated(true);
        this.principal = principal;
        this.credentials = credentials;
    }

    /**
     * 
     * @see org.springframework.security.Authentication#getCredentials()
     */
    public Object getCredentials() {
        return credentials;
    }

    /**
     * @see org.springframework.security.Authentication#getPrincipal()
     */
    public Object getPrincipal() {
        return principal;
    }

}
