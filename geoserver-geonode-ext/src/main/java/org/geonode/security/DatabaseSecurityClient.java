package org.geonode.security;

import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.sql.DataSource;
import net.sf.json.JSONObject;
import net.sf.json.JSONSerializer;
import org.apache.commons.codec.binary.Base64;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.security.AccessMode;
import org.geotools.util.logging.Logging;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.web.authentication.preauth.PreAuthenticatedAuthenticationToken;

/**
 * While similar to the DefaultSecurityClient, the DatabaseSecurityClient does
 * authentication and authorization in two steps and with a finer grained, per
 * layer query.
 * @author Ian Schneider <ischneider@opengeo.org>
 */
public class DatabaseSecurityClient implements GeoNodeSecurityClient {

    private static final String GEONODE_COOKIE_NAME = "sessionid";
    
    // enums are passe, don't do it
    private final byte ACCESS_UNKNOWN = 0;
    private final byte ACCESS_DENIED = 1;
    private final byte ACCESS_READ = 2;
    private final byte ACCESS_WRITE = 3;
    
    private final Logger LOGGER = Logging.getLogger(DefaultSecurityClient.class);
    private final DataSource dataSource;
    private final HTTPClient client;
    private final String baseUrl;
    /**
     * Cache authentication for both cookie and user/password pairs
     */
    private final Cache<String, Authentication> authenticationCache;
    /**
     * Cache authorization by user/layer pair. The Byte value is one of the 
     * ACCESS_ fields.
     */
    private final Cache<AuthorizationKey, Byte> authorizationCache;
    private final AnonymousAuthenticationToken ANONYMOUS = new AnonymousAuthenticationToken(
            "geonode", "anonymous", Collections.singletonList(new SimpleGrantedAuthority("ROLE_ANONYMOUS")));
    private final Collection<? extends GrantedAuthority> ADMIN_AUTHORITY = 
            Collections.singleton(GeoNodeDataAccessManager.getAdminRole());

    public DatabaseSecurityClient(DataSource dataSource, String baseUrl, HTTPClient httpClient) {
        this.dataSource = dataSource;
        this.baseUrl = baseUrl;
        this.client = httpClient;
        // these can be stored longer maybe? just in case, expire this cache
        // after 1 day
        authenticationCache = CacheBuilder.newBuilder().
                maximumSize(100).expireAfterWrite(1, TimeUnit.DAYS).build();
        // the idea w/ expiration after access is that if someone has access to
        // a layer, it will probably not change quickly after that. cache
        // extension makes the standard pan/zoom or time playback perform much
        // better.
        // the issue of a new layer not appearing in the cache is not a problem
        // with this client as it caches layers individually and not in bulk
        authorizationCache = CacheBuilder.newBuilder().
                maximumSize(10000).expireAfterAccess(1, TimeUnit.MINUTES).build();
    }

    public Authentication authenticateCookie(String cookieValue) throws AuthenticationException, IOException {
        Authentication auth = authenticationCache.getIfPresent(cookieValue);
        if (auth == null) {
            final String headerName = "Cookie";
            final String headerValue = GEONODE_COOKIE_NAME + "=" + cookieValue;
            auth = authenticate(cookieValue, headerName, headerValue);
            authenticationCache.put(cookieValue, auth);
        }
        return auth;
    }

    public Authentication authenticateAnonymous() throws AuthenticationException, IOException {
        return ANONYMOUS;
    }

    public Authentication authenticateUserPwd(String username, String password) throws AuthenticationException, IOException {
        final String userPassword = username + ":" + password;
        Authentication auth = authenticationCache.getIfPresent(userPassword);
        if (auth == null) {
            final String headerName = "Authorization";
            final String headerValue = "Basic "
                    + new String(Base64.encodeBase64((username + ":" + password).getBytes()));

            auth = authenticate(password, headerName, headerValue);
            authenticationCache.put(userPassword, auth);
        }
        return auth;
    }

    private Authentication authenticate(final Object credentials, final String... requestHeaders)
            throws AuthenticationException, IOException {
        final String url = baseUrl + "layers/resolve_user";

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

    private Authentication toAuthentication(Object credentials, JSONObject json) {
        Collection<? extends GrantedAuthority> authorities = null;
        Authentication auth;
        Object userName = json.get("user");
        // if userName is null, this will return a JSONObject
        if (userName instanceof JSONObject) {
            // either anonymous or geoserver at this point
            if (json.getBoolean("geoserver")) {
                auth = new PreAuthenticatedAuthenticationToken("geoserver", "geoserver",
                        ADMIN_AUTHORITY
                );
            } else {
                auth = ANONYMOUS;
            }
        } else {
            if (json.getBoolean("superuser")) {
                authorities = ADMIN_AUTHORITY;
            } else {
                authorities = Collections.EMPTY_LIST;
            }
            auth = new UsernamePasswordAuthenticationToken(userName, credentials, authorities);
        }
        return auth;
    }
    
    String authorize(String user, String layerName) {
        Connection conn = null;
        PreparedStatement s = null;
        String auth = null;
        try {
            conn = dataSource.getConnection();
        } catch (SQLException ex) {
            LOGGER.log(Level.SEVERE, "Error opening auth db connection", ex);
        }
        if (conn != null) {
            try {
                s = conn.prepareStatement("select * from geonode_authorize_layer(?,?)");
                s.setString(1, user);
                s.setString(2, layerName);
            } catch (SQLException ex) {
                LOGGER.log(Level.SEVERE, "Error preparing auth statement", ex);
            }
        }
        if (s != null) {
            try {
                ResultSet rs = s.executeQuery();
                if (rs.next()) {
                    auth = rs.getString(1);
                } else {
                    LOGGER.log(Level.SEVERE, "Expected a result, got none");
                }
            } catch (SQLException ex) {
                LOGGER.log(Level.SEVERE, "Error getting results", ex);
            }
        }
        if (conn != null) {
            try {
                conn.close();
            } catch (SQLException ex) {
                LOGGER.log(Level.WARNING, "Error closing connection", ex);
            }
        }
        if (s != null) {
            try {
                s.close();
            } catch (SQLException ex) {
                LOGGER.log(Level.WARNING, "Error closing statement", ex);
            }
        }
        return auth;
    }

    public boolean authorize(Authentication user, ResourceInfo resource, AccessMode mode) {
        String resourceName = resource.prefixedName();
        AuthorizationKey key = new AuthorizationKey(user.getName(), resourceName);
        Byte bits = authorizationCache.getIfPresent(key);
        if (bits == null) {
            bits = computeBits(user, resource, mode);
            authorizationCache.put(key, bits);
        }
        boolean authorized = false;
        switch (bits) {
            case ACCESS_DENIED: case ACCESS_UNKNOWN:
                break;
            case ACCESS_READ: 
                authorized = mode == AccessMode.READ;
                break;
            case ACCESS_WRITE:
                authorized = true;
                break;
            default:
                throw new RuntimeException("Unknown authorization bits : " + bits);
        }
        return authorized;
    }
    
    private Byte computeBits(Authentication user, ResourceInfo resource, AccessMode mode) {
        String userName = user.getName();
        // mask anonymous - not known in the database
        if ("".equals(user.getCredentials())) {
            userName = null;
        }
        
        // auth string will be null or (reason)(-auth?)
        // where reason is for debugging purposes and auth is either 'ro' or 'rw'
        // reasons are:
        // nl - no layer (no auth)
        // nu - no user (no auth)
        // lo - layer owner
        // su - super user
        // gr - generic role
        // ur - user role
        // nf - no rule found (no auth)
        final String auth = authorize(userName, resource.prefixedName());
        final boolean debug = LOGGER.isLoggable(Level.FINE);
        byte bits = ACCESS_DENIED;
        // if auth is null, errors already logged, consider tossing an exception?
        if (auth != null) {
            String[] parts = auth.split("-");
            if (parts.length == 1) {
                String reason = parts[0];
                if ("nf".equals(reason)) {
                    if (debug) {
                        LOGGER.log(Level.FINE, "rejecting {0} : {1}", new Object[] {user.getName(), auth});
                    }
                } else {
                    LOGGER.log(Level.WARNING, "unknown access {0} : {1}", new Object[] {user.getName(), auth});
                    bits = ACCESS_UNKNOWN;
                }
            } else {
                boolean ro = "ro".equals(parts[1]);
                boolean rw = "rw".equals(parts[1]);
                if (! (ro || rw)) {
                    throw new RuntimeException("auth protocol failure, expected ro or rw, got " + parts[1]);
                }
                if (ro) {
                    bits = ACCESS_READ;
                } else {
                    bits = ACCESS_WRITE;
                }
                if (debug) {
                    LOGGER.log(Level.FINE, "authorized {0} to {1} for {2} : {3},{4}", new Object[]{
                                user.getName(), resource.prefixedName(), mode, auth, bits
                            });
                }
            }
        }
        // use valueOf to ensure object sharing
        return Byte.valueOf(bits);
    }

    /**
     * Key for tracking permissions on a layer for a given user.
     */
    private static final class AuthorizationKey {
        private final String user;
        private final String layer;
        
        AuthorizationKey(String user, String layer) {
            // internalized strings - there will be many of the same exact
            // user and layer strings - this results in potentially big savings
            this.user = user.intern();
            this.layer = layer.intern();
        }

        @Override
        public int hashCode() {
            return user.hashCode() ^ layer.hashCode();
        }

        @Override
        public boolean equals(Object obj) {
            AuthorizationKey o = (AuthorizationKey) obj;
            return o.user.equals(user) && o.layer.equals(layer);
        }
        
    }
}
