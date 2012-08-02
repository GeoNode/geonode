package org.geonode.security;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

public class AnonymousGeoNodeAuthenticationToken extends UsernamePasswordAuthenticationToken {
    private static final long serialVersionUID = -8990929783736039847L;

    public AnonymousGeoNodeAuthenticationToken(Object principal, Object credentials) {
        super(principal, credentials);
    }
}
