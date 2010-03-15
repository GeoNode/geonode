package org.geonode.process;

public class LayerReference {
    private String name;
    private String service;
    private String metadataURL;
    private String serviceURL;

    public LayerReference() {}

    public LayerReference(String name, String service, String metadataURL, String serviceURL) {
        this.name = name;
        this.service = service;
        this.metadataURL = metadataURL;
        this.serviceURL = serviceURL;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public void setService(String service) {
        this.service = service;
    }

    public String getService() {
        return service;
    }

    public void setMetadataURL(String metadataURL) {
        this.metadataURL = metadataURL;
    }

    public String getMetadataURL() {
        return this.metadataURL;
    }

    public void setServiceURL(String serviceURL) {
        this.serviceURL = serviceURL;
    }

    public String getServiceURL() {
        return this.serviceURL;
    }
}
