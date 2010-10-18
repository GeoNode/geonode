package org.geonode.security;

import java.util.logging.Logger;

import org.acegisecurity.GrantedAuthority;
import org.acegisecurity.providers.AbstractAuthenticationToken;
import org.geotools.util.logging.Logging;

public class GeoNodeSessionAuthToken extends AbstractAuthenticationToken {

    static final Logger LOGGER = Logging.getLogger(GeoNodeSessionAuthToken.class);
	
    /**
     * 
     */
    private static final long serialVersionUID = -3781584924355064548L;

    private Object principal;

    private Object credentials;

    public GeoNodeSessionAuthToken(Object principal, Object credentials,
            GrantedAuthority[] authorities) {
        super(authorities);
    	LOGGER.fine("creating GeoNodeSessionAuthToken");
        super.setAuthenticated(true);
        LOGGER.fine("authenticated as " + principal.toString() + ", credentials: " + credentials.toString());
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
