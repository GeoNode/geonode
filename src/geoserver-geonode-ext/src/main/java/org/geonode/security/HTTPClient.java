package org.geonode.security;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import org.apache.commons.httpclient.HttpClient;
import org.apache.commons.httpclient.MultiThreadedHttpConnectionManager;
import org.apache.commons.httpclient.methods.GetMethod;
import org.springframework.util.Assert;

/**
 * A reentrant HTTP client used to send authentication requests to GeoNode
 * 
 * @author groldan
 * 
 */
public class HTTPClient {

    private final HttpClient client;

    /**
     * 
     * @param maxConnectionsPerHost
     * @param connectionTimeout
     * @param readTimeout
     */
    public HTTPClient(final int maxConnectionsPerHost, final int connectionTimeout,
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
}
