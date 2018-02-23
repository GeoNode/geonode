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
 * $RCSfile: ZipRepository.java,v $
 * $Author: hannes $
 * $Revision: 1.11 $
 * $Date: 2006/04/07 14:37:11 $
 */

package org.ringojs.repository;

import org.ringojs.util.StringUtils;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipException;
import java.net.URL;
import java.net.MalformedURLException;
import java.lang.ref.WeakReference;

public final class ZipRepository extends AbstractRepository {

    // zip file serving sub-repositories and zip file resources
    private File file;

    // weak reference to the zip file
    private WeakReference<ZipFile> zipFile;

    // the relative path of this repository within the zip file
    private final String entryPath;

    // the nested directory depth of this repository within the zip file
    private int depth;

    private long lastModified = -1;
    private boolean exists;

    /**
     * Constructs a ZipRespository using the given zip file.
     * @param path path to zip file
     * @throws ZipException a zip encoding related error occurred
     * @throws IOException an I/O error occurred
     */
    public ZipRepository(String path)
            throws ZipException, IOException {
        this(new File(path));
    }

    /**
     * Constructs a ZipRespository using the given zip file.
     * @param file zip file
     * @throws ZipException a zip encoding related error occurred
     * @throws IOException an I/O error occurred
     */
    public ZipRepository(File file)
            throws ZipException, IOException {
        // make sure our file has an absolute path,
        // see http://bugs.sun.com/bugdatabase/view_bug.do?bug_id=4117557
        if (!file.isAbsolute()) {
            file = file.getAbsoluteFile();
        }
        this.file = file;
        this.parent = null;
        name = file.getName();
        path = file.getPath() + '/';
        depth = 0;
        entryPath = "";
    }

    /**
     * Constructs a ZipRepository using the zip entryName belonging to the given
     * zip file and top-level repository
     * @param file the zip file
     * @param parent repository
     * @param entryPath the entry path name
     * @throws ZipException a zip encoding related error occurred
     * @throws IOException an I/O error occurred
     */
    private ZipRepository(File file, ZipRepository parent, String entryPath)
            throws ZipException, IOException {
        if (entryPath == null) {
            throw new NullPointerException("entryPath must not be null");
        } else if (entryPath.equals("")) {
            throw new IllegalArgumentException("entryPath must not be empty");
        }
        this.file = file;
        this.parent = parent;
        // Make sure entryPath ends with slash. This is the only way we
        // can be sure the zip entry isn't actually a file.
        this.entryPath = entryPath.endsWith("/") ? entryPath : entryPath + "/";
        String[] pathArray = StringUtils.split(entryPath, SEPARATOR);
        depth = pathArray.length;
        name = pathArray[depth - 1];
        path = parent.getPath() + name  + '/';
    }

    /**
     * Returns a java.util.zip.ZipFile for this repository.
     * @return a ZipFile for reading
     * @throws IOException an I/O related error occurred
     */
    protected synchronized ZipFile getZipFile() throws IOException {
        if (parent instanceof ZipRepository) {
            return ((ZipRepository) parent).getZipFile();
        }
        ZipFile zip = zipFile == null ? null : zipFile.get();
        if (zip == null || lastModified != file.lastModified()) {
            if (zip != null) {
                try {
                    zip.close();
                } catch (Exception ignore) {}
            }
            zip = new ZipFile(file);
            zipFile = new WeakReference<ZipFile>(zip);
            lastModified = file.lastModified();
        }
        return zip;
    }


    /**
     * Called to create a child resource for this repository.
     */
    @Override
    protected Resource lookupResource(String name) throws IOException {
        AbstractResource res = resources.get(name);
        if (res == null) {
            String childName = entryPath + name;
            ZipFile zip = getZipFile();
            // getEntry() will return a directory entry without trailing slash,
            // but it will not return a file entry with trailing slash.
            // Thus, the only way to make sure an entry is not a directory is
            // to explicitly try to fetch the entry as directory before fetching
            // it as file.
            ZipEntry entry = zip.getEntry(childName + "/");
            if (entry == null) {
                entry = zip.getEntry(childName);
            }
            res = new ZipResource(childName, this, entry);
            resources.put(name, res);
        }
        return res;
    }

    /**
     * Checks wether this resource actually (still) exists
     * @return true if the resource exists
     */
    public boolean exists() throws IOException {
        if (lastModified != file.lastModified()) {
            try {
                ZipFile zip = getZipFile();
                exists = entryPath.length() == 0 ?
                        zip != null : zip.getEntry(entryPath) != null;
            } catch (IOException ex) {
                exists = false;
            }
        }
        return exists;
    }

    protected AbstractRepository createChildRepository(String name)
            throws IOException {
        return new ZipRepository(file, this, entryPath + name);
    }

    protected void getResources(List<Resource> list, boolean recursive)
            throws IOException {
        Map<String,ZipEntry> entries = getChildEntries();

        for (Map.Entry<String, ZipEntry> entry : entries.entrySet()) {
            String entryName = entry.getKey();
            if (!entry.getValue().isDirectory()) {
                AbstractResource res = resources.get(entryName);
                if (res == null) {
                    ZipEntry zipEntry = entry.getValue();
                    res = new ZipResource(zipEntry.getName(), this, zipEntry);
                    resources.put(entryName, res);
                }
                list.add(res);
            } else if (recursive) {
                lookupRepository(entryName).getResources(list, true);
            }
        }
    }

    public Repository[] getRepositories() throws IOException {
        List<Repository> list = new ArrayList<Repository>();
        Map<String,ZipEntry> entries = getChildEntries();

        for (Map.Entry<String, ZipEntry> entry : entries.entrySet()) {
            if (entry.getValue().isDirectory()) {
                list.add(lookupRepository(entry.getKey()));
            }
        }
        return list.toArray(new Repository[list.size()]);
    }

    public URL getUrl() throws MalformedURLException {
        // return a Jar URL as described in
        // http://java.sun.com/j2se/1.5.0/docs/api/java/net/JarURLConnection.html
        if (parent instanceof ZipRepository) {
            return new URL(parent.getUrl() + name + "/");
        } else {
            String baseUrl = "jar:file:" + file + "!/";
            return entryPath.length() == 0 ?
                    new URL(baseUrl) : new URL(baseUrl + entryPath);
        }
    }

    public long lastModified() {
        return file.lastModified();
    }

    public long getChecksum() {
        return file.lastModified();
    }

    @Override
    public int hashCode() {
        return 17 + (37 * file.hashCode()) + (37 * path.hashCode());
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof ZipRepository)) {
            return false;
        }

        ZipRepository rep = (ZipRepository) obj;
        return (file.equals(rep.file) && path.equals(rep.path));
    }

    @Override
    public String toString() {
        return "ZipRepository[" + path + "]";
    }

    private Map<String, ZipEntry> getChildEntries() throws IOException {
        ZipFile zipfile = getZipFile();
        Map<String, ZipEntry> map = new TreeMap<String, ZipEntry>();
        Enumeration en = zipfile.entries();

        while (en.hasMoreElements()) {
            ZipEntry entry = (ZipEntry) en.nextElement();
            String entryName = entry.getName();

            if (!entryName.regionMatches(0, entryPath, 0, entryPath.length())) {
                // names don't match - not a child of ours
                continue;
            }
            String[] entrypath = StringUtils.split(entryName, SEPARATOR);
            if (depth > 0 && !name.equals(entrypath[depth-1])) {
                // catch case where our name is Foo and other's is FooBar
                continue;
            }
            if (entrypath.length == depth + 1) {
                map.put(entrypath[depth], entry);
            }
        }
        return map;
    }

}
