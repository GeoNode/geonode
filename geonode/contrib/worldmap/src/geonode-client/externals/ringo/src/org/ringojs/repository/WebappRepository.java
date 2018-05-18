package org.ringojs.repository;

import javax.servlet.ServletContext;
import java.io.File;
import java.net.URLDecoder;
import java.nio.charset.Charset;
import java.util.*;
import java.net.URL;
import java.net.MalformedURLException;
import java.io.IOException;

public class WebappRepository extends AbstractRepository {

    ServletContext context;

    private int exists = -1;

    public WebappRepository(ServletContext context, String path) {
        this.context = context;
        this.parent = null;
        if (path == null) {
            path = "/";
        } else if (!path.endsWith("/")) {
            path = path + "/";
        }
        this.path = path;
        this.name = path;
    }

    protected WebappRepository(ServletContext context, WebappRepository parent, String name) {
        this.context = context;
        this.parent = parent;
        this.name = name;
        this.path = parent.path + name + "/";
    }

    public long getChecksum() {
        return lastModified();
    }

    public long lastModified() {
        try {
            String realPath = context.getRealPath(path);
            return realPath == null ? 0 : new File(realPath).lastModified();
        } catch (Exception x) {
            return 0;
        }
    }

    public boolean exists() throws IOException {
        if (exists < 0) {
            if ("/".equals(path)) {
                exists = 1;
            } else {
                try {
                    URL url = context.getResource(path);
                    if (url != null && url.getProtocol().equals("file")) {
                        String enc = Charset.defaultCharset().name();
                        String path = URLDecoder.decode(url.getPath(), enc);
                        exists = new File(path).isDirectory() ? 1 : 0;
                    } else {
                        exists = url != null ? 1 : 0;
                    }
                } catch (MalformedURLException mux) {
                    exists = 0;
                }
            }
        }
        return exists == 1;
    }

    public URL getUrl() throws MalformedURLException {
        return context.getResource(path);
    }

    @Override
    protected Resource lookupResource(String name) {
        AbstractResource res = resources.get(name);
        if (res == null) {
            res = new WebappResource(context, this, name);
            resources.put(name, res);
        }
        return res;
    }

    protected AbstractRepository createChildRepository(String name) {
        return new WebappRepository(context, this, name);
    }

    protected void getResources(List<Resource> list, boolean recursive)
            throws IOException {
        Set paths = context.getResourcePaths(path);

        if (paths != null) {
            for (Object obj: paths) {
                String path = (String) obj;
                if (!path.endsWith("/")) {
                    int n = path.lastIndexOf('/', path.length() - 1);
                    String name = path.substring(n + 1);
                    list.add(lookupResource(name));
                } else if (recursive) {
                    int n = path.lastIndexOf('/', path.length() - 2);
                    String name = path.substring(n + 1, path.length() - 1);
                    AbstractRepository repo = lookupRepository(name);
                    repo.getResources(list, true);
                }
            }
        }
    }

    public Repository[] getRepositories() throws IOException {
        Set paths = context.getResourcePaths(path);
        List<Repository> list = new ArrayList<Repository>();

        if (paths != null) {
            for (Object obj: paths) {
                String path = (String) obj;
                if (path.endsWith("/")) {
                    int n = path.lastIndexOf('/', path.length() - 2);
                    String name = path.substring(n + 1, path.length() - 1);
                    list.add(lookupRepository(name));
                }
            }
        }
        return list.toArray(new Repository[list.size()]);
    }

    @Override
    public String toString() {
        return "WebappRepository[" + path + "]";
    }

    @Override
    public int hashCode() {
        return 5 + path.hashCode();
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof WebappRepository && path.equals(((WebappRepository)obj).path);
    }

}
