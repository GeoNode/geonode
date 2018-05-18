package org.ringojs.repository;

import javax.servlet.ServletContext;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.Charset;

public class WebappResource extends AbstractResource {

    ServletContext context;
    private int exists = -1;

    protected WebappResource(ServletContext context, WebappRepository repository, String name) {
        this.context = context;
        this.repository = repository;
        this.name = name;
        this.path = repository.path + name;
        setBaseNameFromName(name);
    }

    public long lastModified() {
        try {
            String realPath = context.getRealPath(path);
            return realPath == null ? 0 : new File(realPath).lastModified();
        } catch (Exception x) {
            return 0;
        }
    }

    public boolean exists() throws IOException{
        if (exists < 0) {
            try {
                URL url = context.getResource(path);
                if (url != null && url.getProtocol().equals("file")) {
                    String enc = Charset.defaultCharset().name();
                    String path = URLDecoder.decode(url.getPath(), enc);
                    exists = new File(path).isFile() ? 1 : 0;
                } else {
                    exists = url != null ? 1 : 0;
                }
            } catch (MalformedURLException mux) {
                exists = 0;
            }
        }
        return exists == 1;
    }

    public long getLength() {
        return 0;
    }

    public InputStream getInputStream() throws IOException {
        return stripShebang(context.getResourceAsStream(path));
    }

    public URL getUrl() throws MalformedURLException {
        return context.getResource(path);
    }

    @Override
    public String toString() {
        return "WebappResource[" + path + "]";
    }

    @Override
    public int hashCode() {
        return 37 + path.hashCode();
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof WebappResource && path.equals(((WebappResource)obj).path);
    }
}
