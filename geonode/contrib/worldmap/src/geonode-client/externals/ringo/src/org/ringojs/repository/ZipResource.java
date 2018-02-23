/*
 * Helma License Notice
 *
 * The contents of this file are subject to the Helma License
 * Version 2.0 (the "License"). You may not use this file except in
 * compliance with the License. A copy of the License is available at
 * http://adele.helma.org/download/helma/license.txt
 *
 * Copyright 1998-2003 Helma Software. All Rights Reserved.
 *
 * $RCSfile: ZipResource.java,v $
 * $Author: hannes $
 * $Revision: 1.7 $
 * $Date: 2005/12/19 22:15:11 $
 */

package org.ringojs.repository;

import java.io.*;
import java.net.URL;
import java.net.MalformedURLException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public final class ZipResource extends AbstractResource {

    private String entryName;
    private boolean exists;
    long length;
    long lastModified;

    protected ZipResource(String childName, ZipRepository repository, ZipEntry entry) {
        this.repository = repository;
        this.entryName = childName;
        exists = entry != null && !entry.isDirectory();
        length = exists ? entry.getSize() : 0;
        lastModified = repository.lastModified();

        int slash = entryName.lastIndexOf('/');
        this.name = slash < 0 ? entryName : entryName.substring(slash + 1);
        this.path = repository.getPath() + name;
        setBaseNameFromName(name);
    }

    public long lastModified() {
        return repository.lastModified();
    }

    public long getChecksum() {
        return repository.lastModified();
    }

    public InputStream getInputStream() throws IOException {
        ZipFile zipfile = getZipFile();
        ZipEntry entry = zipfile.getEntry(entryName);
        if (entry == null) {
            throw new IOException("Zip resource " + this + " does not exist");
        }
        return stripShebang(zipfile.getInputStream(entry));
    }

    private void update() {
        try {
            ZipEntry entry = getZipFile().getEntry(entryName);
            exists = entry != null && !entry.isDirectory();
            length = exists ? entry.getSize() : 0;
            lastModified = repository.lastModified();
        } catch (IOException ex) {
            exists = false;
        }

    }

    public boolean exists() throws IOException {
        if (lastModified != repository.lastModified()) {
            update();
        }
        return exists;
    }


    public URL getUrl() throws MalformedURLException {
        // return a Jar URL as defined in
        // http://java.sun.com/j2se/1.5.0/docs/api/java/net/JarURLConnection.html
        return new URL(repository.getUrl() + name);
    }

    public long getLength() {
        if (lastModified != repository.lastModified()) {
            update();
        }
        return length;
    }

    @Override
    public int hashCode() {
        return 17 + path.hashCode();
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof ZipResource && path.equals(((ZipResource) obj).path);
    }

    @Override
    public String toString() {
        return getPath();
    }

    private ZipFile getZipFile() throws IOException {
        if (!(repository instanceof ZipRepository)) {
            throw new IOException("Parent is not a ZipRepository: " + repository);
        }
        return ((ZipRepository) repository).getZipFile();
    }
}
