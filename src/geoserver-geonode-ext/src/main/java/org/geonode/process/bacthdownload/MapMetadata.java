package org.geonode.process.bacthdownload;

public class MapMetadata {
    private String title;

    private String author;

    public MapMetadata() {
    }

    public MapMetadata(String title, String author) {
        this.title = title;
        this.author = author;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getTitle() {
        return this.title;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getAuthor() {
        return this.author;
    }
}
