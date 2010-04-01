package org.geonode.process.batchdownload;

public class MapMetadata {

    private String title;

    private String author;

    private String abstractInfo;

    public MapMetadata() {
    }

    public MapMetadata(String title, String abstractInfo, String author) {
        this.title = title;
        this.author = author;
        this.abstractInfo = abstractInfo;
    }

    public String getTitle() {
        return this.title;
    }

    public String getAbstract() {
        return abstractInfo;
    }

    public String getAuthor() {
        return this.author;
    }
}
