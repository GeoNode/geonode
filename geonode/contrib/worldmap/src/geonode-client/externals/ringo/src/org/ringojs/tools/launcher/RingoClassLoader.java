/*
 *  Copyright 2006 Hannes Wallnoefer <hannes@helma.at>
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

package org.ringojs.tools.launcher;

import java.net.URLClassLoader;
import java.net.URL;
import java.net.MalformedURLException;
import java.io.File;

/**
 * A <code>ClassLoader</code> used for application class loading. This class
 * provides constructors and methods to add jar directories to the classpath.
 *
 * <p>Note that class lookups are cached, so adding a jar file after a class has
 * already been looked up won't make the classes available.
 */
public class RingoClassLoader extends URLClassLoader {

    public RingoClassLoader() {
        this(new URL[0]);
    }

    public RingoClassLoader(URL[] urls) {
        this(urls, RingoClassLoader.class.getClassLoader());
    }

    public RingoClassLoader(File home, String[] classpath)
            throws MalformedURLException {
        this(new URL[0]);
        for (String item: classpath) {
            if (item.endsWith(File.separator + "**") || item.endsWith("/**")) {
                File dir = getAbsoluteFile(home, item.substring(0, item.length() - 2));
                addClasspathWildcard(dir, true);
            } else if (item.endsWith(File.separator + "*") || item.endsWith("/*")) {
                File dir = getAbsoluteFile(home, item.substring(0, item.length() - 1));
                addClasspathWildcard(dir, false);
            } else {
                File file = getAbsoluteFile(home, item);
                addURL(new URL("file:" + file));
            }
        }
    }

    public RingoClassLoader(URL[] urls, ClassLoader parent) {
        super(urls, parent);
    }

    protected void addClasspathWildcard(File dir, boolean recursive)
            throws MalformedURLException {
        if (!dir.exists()) {
            throw new IllegalArgumentException("Directory '" + dir + "' does not exist");
        } else if (!dir.isDirectory()) {
            throw new IllegalArgumentException("'" + dir + "' is not a directory");
        }
        File[] files = dir.listFiles();
        for (File file: files) {
            if (recursive && file.isDirectory()) {
                addClasspathWildcard(file, true);
            } else {
                String name = file.getName().toLowerCase();
                if (file.isFile() && (name.endsWith(".jar") || (name.endsWith(".zip")))) {
                    addURL(new URL("file:" + file));
                }
            }
        }
    }

    static File getAbsoluteFile(File home, String path) {
        File file = new File(path);
        if (file.isAbsolute()) {
            return file;
        }
        return new File(home, path);
    }

}
