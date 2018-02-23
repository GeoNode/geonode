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
 * $RCSfile: AbstractRepository.java,v $
 * $Author: hannes $
 * $Revision: 1.7 $
 * $Date: 2006/04/07 14:37:11 $
 */

package org.ringojs.repository;

import java.io.IOException;
import java.lang.ref.SoftReference;
import java.util.*;

/**
 * Provides common methods and fields for the default implementations of the
 * repository interface
 */
public abstract class AbstractRepository implements Repository {


    /**
     * Parent repository this repository is contained in.
     */
    AbstractRepository parent;

    /**
     * Cache for direct child repositories
     */
    Map<String, SoftReference<AbstractRepository>> repositories =
            Collections.synchronizedMap(
                    new HashMap<String, SoftReference<AbstractRepository>>());

    /**
     * Cache for direct resources
     */
    Map<String, AbstractResource> resources =
            Collections.synchronizedMap(new HashMap<String, AbstractResource>());

    /**
     * Cached name for faster access
     */
    String path;

    /**
     * Cached short name for faster access
     */
    String name;

    /**
     * Whether this repository uses an absolute path
     */
    private boolean isAbsolute = false;

    /**
     * Called to create a child resource for this repository if it exists.
     * @param name the name of the child resource
     * @return the child resource, or null if no resource with the given name exists
     * @throws IOException an I/O error occurred
     */
    protected abstract Resource lookupResource(String name) throws IOException;

    /**
     * Create a new child reposiotory with the given name.
     * @param name the name
     * @return the new child repository
     * @throws IOException an I/O error occurred
     */
    protected abstract AbstractRepository createChildRepository(String name) throws IOException;

    /**
     * Add the repository's resources into the list, optionally descending into
     * nested repositories.
     * @param list the list to add the resources to
     * @param recursive whether to descend into nested repositories
     * @throws IOException an I/O related error occurred
     */
    protected abstract void getResources(List<Resource> list, boolean recursive)
            throws IOException;

    /**
     * Get the full name that identifies this repository globally
     */
    public String getPath() {
        return path;
    }

    /**
     * Get the local name that identifies this repository locally within its
     * parent repository
     */
    public String getName() {
        return name;
    }

    /**
     * Mark this repository as root repository.
     */
    public void setRoot() {
        parent = null;
    }

    /**
     * Set this Repository to absolute mode. This will cause all its
     * relative path operations to use absolute paths instead.
     * @param absolute true to operate in absolute mode
     */
    public void setAbsolute(boolean absolute) {
        isAbsolute = absolute;
    }

    /**
     * Return true if this Repository is in absolute mode.
     * @return true if absolute mode is on
     */
    public boolean isAbsolute() {
        return isAbsolute;
    }

    /**
     * Get the path of this repository relative to its root repository.
     *
     * @return the repository path
     */
    public String getRelativePath() {
        if (isAbsolute) {
            return path;
        } else if (parent == null) {
            return "";
        } else {
            StringBuffer b = new StringBuffer();
            getRelativePath(b);
            return b.toString();
        }
    }

    private void getRelativePath(StringBuffer buffer) {
        if (isAbsolute) {
            buffer.append(path);
        } else if (parent != null) {
            parent.getRelativePath(buffer);
            buffer.append(name).append('/');
        }
    }

    /**
     * Utility method to get the name for the module defined by this resource.
     *
     * @return the module name according to the securable module spec
     */
    public String getModuleName() {
        return getRelativePath();
    }

    /**
     * Resolve path relative to this repository.
     * @param path a path string
     * @param absolute whether to return an absolute path that can be used without this repository
     * @return a List containing the path elements resolved relative to this repository
     */
    protected String[] resolve(String path, boolean absolute) {
        String[] elements = path.split(SEPARATOR);
        LinkedList<String> list = new LinkedList<String>();
        if (absolute) {
            list.addAll(Arrays.asList(this.path.split(SEPARATOR)));
        }
        for (String e : elements) {
            if ("..".equals(e)) {
                String last = list.isEmpty() ? null : list.getLast();
                if (last == null || "..".equals(last)) {
                    list.add(e);
                } else if (!isAbsolute || list.size() > 1) {
                    list.removeLast();
                }
            } else if (!".".equals(e) && !"".equals(e)) {
                list.add(e);
            }
        }
        return list.toArray(new String[list.size()]);
    }

    /**
     * Get a resource contained in this repository identified by the given local name.
     * If the name can't be resolved to a resource, a resource object is returned
     * for which {@link Resource exists()} returns <code>false<code>.
     */
    public synchronized Resource getResource(String subpath) throws IOException {
        String[] list = resolve(subpath, false);
        AbstractRepository repo = this;
        if (list.length == 0) {
            repo = getParentRepository();
            return repo == null ? null : repo.getResource(name);
        } else {
            String last = list[list.length - 1];
            for (String e : list) {
                if (repo == null || e == last) {
                    break;
                }
                repo = repo.lookupRepository(e);
            }
            return repo == null ? null : repo.lookupResource(last);
        }
    }

    /**
     * Get a child repository with the given name
     * @param subpath the name of the repository
     * @return the child repository
     */
    public AbstractRepository getChildRepository(String subpath) throws IOException {
        String[] list = resolve(subpath, false);
        AbstractRepository repo = this;
        for (String e : list) {
            if (repo == null) {
                return null;
            }
            repo = repo.lookupRepository(e);
        }
        return repo;
    }

    protected AbstractRepository lookupRepository(String name) throws IOException {
        if (".".equals(name) || "".equals(name)) {
            return this;
        } else if ("..".equals(name)) {
            return getParentRepository();
        }
        SoftReference<AbstractRepository> ref = repositories.get(name);
        AbstractRepository repo = ref == null ? null : ref.get();
        if (repo == null) {
            repo = createChildRepository(name);
            repositories.put(name, new SoftReference<AbstractRepository>(repo));
        }
        return repo;
    }

    /**
     * Get this repository's parent repository.
     */
    public AbstractRepository getParentRepository() {
        return parent;
    }

    /**
     * Get the repository's root repository
     */
    public Repository getRootRepository() {
        if (parent == null) {
            return this;
        }
        return parent.getRootRepository();
    }

    public Resource[] getResources() throws IOException {
        return getResources(false);
    }

    public Resource[] getResources(boolean recursive) throws IOException {
        List<Resource> list = new ArrayList<Resource>();
        getResources(list, recursive);
        return list.toArray(new Resource[list.size()]);
    }

    public Resource[] getResources(String resourcePath, boolean recursive)
            throws IOException {
        Repository repository = getChildRepository(resourcePath);
        if (repository == null || !repository.exists()) {
            return new Resource[0];
        }
        return repository.getResources(recursive);
    }

    /**
     * Returns the repositories full path as string representation.
     * @see #getPath()
     */
    public String toString() {
        return getPath();
    }

    // Optimized separator lookup to avoid object creation overhead
    // of StringTokenizer and friends on critical code
    private int findSeparator(String path, int start) {
        int max = path.length();
        int numberOfSeparators = SEPARATOR.length();
        int found = -1;
        for (int i = 0; i < numberOfSeparators; i++) {
            char c = SEPARATOR.charAt(i);
            for (int j = start; j < max; j++) {
                if (path.charAt(j) == c) {
                    found = max = j;
                    break;
                }
            }
        }
        return found;
    }

}
