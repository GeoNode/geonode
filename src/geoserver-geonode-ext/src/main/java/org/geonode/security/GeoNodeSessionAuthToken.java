package org.geonode.security;

import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.providers.AbstractAuthenticationToken;

public class GeoNodeSessionAuthToken extends AbstractAuthenticationToken {

    /**
     * 
     */
    private static final long serialVersionUID = -3781584924355064548L;

    private Object principal;

    private Object credentials;

    public GeoNodeSessionAuthToken(Object principal, Object credentials,
            GrantedAuthority[] authorities) {
        super(authorities);
        super.setAuthenticated(true);
        this.principal = principal;
        this.credentials = credentials;
    }

    /**
     * 
     * @see org.acegisecurity.Authentication#getCredentials()
     */
    public Object getCredentials() {
        return credentials;
    }

    /**
     * @see org.acegisecurity.Authentication#getPrincipal()
     */
    public Object getPrincipal() {
        return principal;
    }

}
