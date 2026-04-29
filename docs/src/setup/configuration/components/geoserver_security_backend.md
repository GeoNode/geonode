# GeoServer Security Backend

## GeoServer Security Subsystem

GeoServer has a robust security subsystem, modeled on Spring Security. Most of the security features are available through the Web administration interface.

For more details on how this works and how to configure and modify it, please refer to the official GeoServer guide [here](http://docs.geoserver.org/stable/en/user/security/webadmin/index.html).

By using the `GeoServer Data Dir` provided with GeoNode build, the following configuration are already available. You will need just to update them accordingly to your environment, like IP addresses and host names, OAuth2 keys, and similar things.

However it is recommended to read carefully all the following passages in order to understand exactly how the different component are configured and easily identify any possible issue during the deployment.

The main topics of this section are:

1. Connection to the GeoNode REST Role Service
2. Setup of the GeoServer OAuth2 Authentication Filter
3. Configuration of the GeoServer Filter Chains
4. Setup and test of the GeoFence Server and Default Rules
