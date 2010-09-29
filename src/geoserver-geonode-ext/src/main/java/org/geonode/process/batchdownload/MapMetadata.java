package org.geonode.process.batchdownload;

public class MapMetadata {

    private String title;

    private String author;

    private String abstractInfo;

    private String readme;

    /**
     * This constructor and {@link #MapMetadata(String)} are mutually exclusive, as well as the
     * properties they set
     * 
     * @param title
     *            the readme file's title field content
     * @param abstractInfo
     *            the readme file's abstract field content
     * @param author
     *            the readme file's author field content
     */
    public MapMetadata(String title, String abstractInfo, String author) {
        this.title = title;
        this.author = author;
        this.abstractInfo = abstractInfo;
    }

    /**
     * This constructor and {@link #MapMetadata(String, String, String)} are mutually exclusive, as
     * well as the properties they set
     * 
     * @param readme
     *            the full contents for the README file
     */
    public MapMetadata(String readme) {
        this.readme = readme;
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

    /**
     * @return the full contents for the readme.txt file, or {@code null} indicating the
     *         {@link #getTitle()}, {@link #getAbstract()} and {@link #getAuthor()} properties
     *         should be used instead.
     */
    public String getReadme() {
        return readme;
    }
}
