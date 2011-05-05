package org.geonode.security;

<<<<<<< HEAD
import org.springframework.security.GrantedAuthority;
import org.springframework.security.providers.AbstractAuthenticationToken;
=======
import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.providers.AbstractAuthenticationToken;
>>>>>>> 62e10950604c85ea2fec4f0bb54c420c0ea66ed4

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
<<<<<<< HEAD
     * @see org.springframework.security.Authentication#getCredentials()
=======
     * @see org.acegisecurity.Authentication#getCredentials()
>>>>>>> 62e10950604c85ea2fec4f0bb54c420c0ea66ed4
     */
    public Object getCredentials() {
        return credentials;
    }

    /**
<<<<<<< HEAD
     * @see org.springframework.security.Authentication#getPrincipal()
=======
     * @see org.acegisecurity.Authentication#getPrincipal()
>>>>>>> 62e10950604c85ea2fec4f0bb54c420c0ea66ed4
     */
    public Object getPrincipal() {
        return principal;
    }

}
