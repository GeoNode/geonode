package org.geonode.http;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.MultiThreadedHttpConnectionManager;
import org.apache.commons.httpclient.NameValuePair;
import org.apache.commons.httpclient.methods.GetMethod;
import org.apache.commons.httpclient.methods.PostMethod;
import org.geoserver.platform.GeoServerExtensions;
import org.geotools.util.logging.Logging;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanInitializationException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.util.Assert;

/**
 * A reentrant HTTP client used to send authentication requests to GeoNode
 * 
 * @author groldan
 * 
 */
public class GeoNodeHTTPClient implements ApplicationContextAware {

    private static final Logger LOGGER = Logging.getLogger(GeoNodeHTTPClient.class);

    private final HttpClient client;

    /**
     * The GeoNode base URL (on top of which to construct URL to call back GeoNode)
     */
    private URL baseUrl;

    /**
     * Returns the GeoNode base URL on top of which to construct URLs to hit GeoNode REST end
     * points.
     * <p>
     * The URL is obtained from the GEONODE_BASE_URL property (either a System property, a servlet
     * context parameter or an environment variable).
     * </p>
     */
    public URL getBaseURL() {
        return baseUrl;
    }

    /**
     * 
     * @param maxConnectionsPerHost
     * @param connectionTimeout
     * @param readTimeout
     */
    public GeoNodeHTTPClient(final int maxConnectionsPerHost, final int connectionTimeout,
            final int readTimeout) {

        Assert.isTrue(maxConnectionsPerHost > 0,
                "maxConnectionsPerHost shall be a positive integer");
        Assert.isTrue(connectionTimeout >= 0,
                "connectionTimeout shall be a positive integer or zero");
        Assert.isTrue(readTimeout >= 0, "readTimeout shall be a positive integer or zero");

        MultiThreadedHttpConnectionManager connectionManager = new MultiThreadedHttpConnectionManager();
        connectionManager.getParams().setDefaultMaxConnectionsPerHost(maxConnectionsPerHost);
        connectionManager.getParams().setConnectionTimeout(connectionTimeout);
        connectionManager.getParams().setSoTimeout(readTimeout);
        client = new HttpClient(connectionManager);
    }

    /**
     * Sends an HTTP GET request to the given {@code url} with the provided (possibly empty or null)
     * request headers, and returns the response content as a string.
     * 
     * @param url
     * @param requestHeaders
     * @return
     * @throws IOException
     */
    public String sendGET(final String url, final String[] requestHeaders) throws IOException {

        GetMethod get = new GetMethod(url);
        get.setFollowRedirects(true);

        final int numHeaders = requestHeaders == null ? 0 : requestHeaders.length / 2;
        for (int i = 0; i < numHeaders; i++) {
            String headerName = requestHeaders[2 * i];
            String headerValue = requestHeaders[1 + 2 * i];
            get.addRequestHeader(headerName, headerValue);
        }

        final int status;
        final String responseBodyAsString;

        try {
            status = client.executeMethod(get);
            if (status != 200) {
                throw new IOException("GeoNode communication failed, status report is: " + status
                        + ", " + get.getStatusText());
            }
            StringBuilder responseBody = new StringBuilder();
            InputStream bodyAsStream = get.getResponseBodyAsStream();
            try {
                BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(
                        bodyAsStream));
                String line;
                while ((line = bufferedReader.readLine()) != null) {
                    responseBody.append(line).append('\n');
                }
            } finally {
                bodyAsStream.close();
            }
            responseBodyAsString = responseBody.toString();
        } finally {
            get.releaseConnection();
        }

        return responseBodyAsString;
    }

    /**
     * 
     * @param url
     *            the target URL
     * @param formParams
     *            parameters to send as form url encoded
     * @return HTTP status response code
     * @throws IOException
     *             if the POST request fails
     */
    public void sendPOST(final String url, Map<String, String> formParams) throws IOException {
        PostMethod post = new PostMethod(url);
        List<NameValuePair> data = new ArrayList<NameValuePair>(formParams.size());
        for (Map.Entry<String, String> kvp : formParams.entrySet()) {
            data.add(new NameValuePair(kvp.getKey(), kvp.getValue()));
        }
        post.setRequestBody(data.toArray(new NameValuePair[data.size()]));

        try {
            int responseCode = client.executeMethod(post);
            if (responseCode != 200) {
                throw new IOException("POST request to " + url + " failed: " + post.getStatusText());
            }
        } catch (IOException e) {
            throw e;
        } finally {
            post.releaseConnection();
        }
    }

    /**
     * Looks up for the {@code GEONODE_BASE_URL} property (either a System property, a servlet
     * context parameter or an environment variable) to be used as the base URL for the GeoNode
     * authentication requests (for which {@code 'data/acls'} will be appended).
     * <p>
     * If not provided, defaults to {@code http://localhost:8000}
     * </p>
     * 
     * @see org.springframework.context.ApplicationContextAware#setApplicationContext(org.springframework.context.ApplicationContext)
     * @see GeoServerExtensions#getProperty(String, ApplicationContext)
     */
    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        // determine where geonode is
        String url = GeoServerExtensions.getProperty("GEONODE_BASE_URL", applicationContext);
        if (url == null) {
            LOGGER.log(Level.WARNING, "GEONODE_BASE_URL is not set, "
                    + "assuming http://localhost:8000/");
            url = "http://localhost:8000/";
        }
        if (!url.endsWith("/")) {
            url += "/";
        }
        try {
            this.baseUrl = new URL(url);
        } catch (MalformedURLException e) {
            String msg = "Error fetching property GEONODE_BASE_URL: '" + url + "': ";
            throw new BeanInitializationException(msg + e.getMessage());
        }
    }

}
