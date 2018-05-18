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

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.net.URLDecoder;
import java.nio.charset.Charset;

/**
 * Main launcher class. This figures out the Ringo home directory,
 * sets up the classpath, and launches one of the Ringo tools.
 */
public class Main {

    private Class runnerClass;
    private Object runnerInstance;

    /**
     * Ringo main method. This retrieves the Ringo home directory, creates the
     * classpath and invokes main() in one of the ringo tool classes.
     *
     * @param args command line arguments
     *
     */
    public static void main(String[] args) {
        Main main = new Main();
        main.run(args);
    }

    public Main() {
        try {
            File home = getRingoHome();
            ClassLoader loader = createClassLoader(home);

            runnerClass = loader.loadClass("org.ringojs.tools.RingoRunner");
            runnerInstance = runnerClass.newInstance();
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }

    }

    @SuppressWarnings("unchecked")
    private void run(String[] args) {
        try {
            runnerClass.getMethod("run", args.getClass()).invoke(runnerInstance, (Object) args);
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }
    }

    @SuppressWarnings("unchecked")
    public void init(String[] args) {
        try {
            runnerClass.getMethod("init", args.getClass()).invoke(runnerInstance, (Object) args);
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }
    }

    @SuppressWarnings("unchecked")
    public void start() {
        try {
            runnerClass.getMethod("start").invoke(runnerInstance);
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }
    }

    @SuppressWarnings("unchecked")
    public void stop() {
        try {
            runnerClass.getMethod("stop").invoke(runnerInstance);
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }
    }

    @SuppressWarnings("unchecked")
    public void destroy() {
        try {
            runnerClass.getMethod("destroy").invoke(runnerInstance);
        } catch (Exception x) {
            System.err.println("Uncaught exception: ");
            x.printStackTrace();
            System.exit(2);
        }
    }

    /**
     * Create a server-wide ClassLoader from our install directory.
     * This will be used as parent ClassLoader for all application
     * ClassLoaders.
     *
     * @param home the ringo install directory
     * @return the main classloader we'll be using
     * @throws MalformedURLException
     */
    public static ClassLoader createClassLoader(File home)
            throws MalformedURLException {
        String classpath = System.getProperty("ringo.classpath", "lib/**");
        String[] classes = classpath.split(",");
        RingoClassLoader loader = new RingoClassLoader(home, classes);

        // set the new class loader as context class loader
        Thread.currentThread().setContextClassLoader(loader);
        return loader;
    }


    /**
     * Get the Ringo install directory.
     *
     * @return the base install directory we're running in
     * @throws IOException an I/O related exception occurred
     * @throws MalformedURLException the jar URL couldn't be parsed
     */
    public static File getRingoHome()
            throws IOException {
        // check if home directory is set via system property
        String ringoHome = System.getProperty("ringo.home");
        if (ringoHome == null) {
            ringoHome = System.getenv("RINGO_HOME");
        }

        if (ringoHome == null) {

            URL launcherUrl = findUrl(Main.class.getClassLoader());
            if (launcherUrl == null) {
                launcherUrl = findUrl(Thread.currentThread().getContextClassLoader());
            }
            if (launcherUrl == null) {
                launcherUrl = findUrl(ClassLoader.getSystemClassLoader());
            }

            // this is a  JAR URL of the form
            //    jar:<url>!/{entry}
            // we strip away the jar: prefix and the !/{entry} suffix
            // to get the original jar file URL

            String jarUrl = launcherUrl.toString();
            // decode installDir in case it is URL-encoded
            jarUrl = URLDecoder.decode(jarUrl, Charset.defaultCharset().name());

            if (!jarUrl.startsWith("jar:") || !jarUrl.contains("!")) {
                ringoHome = System.getProperty("user.dir");
                System.err.println("Warning: ringo.home system property is not set ");
                System.err.println("         and not started from launcher.jar. Using ");
                System.err.println("         current working directory as install dir.");
            } else {
                int excl = jarUrl.indexOf("!");
                jarUrl = jarUrl.substring(4, excl);
                launcherUrl = new URL(jarUrl);
                ringoHome = new File(launcherUrl.getPath()).getParent();
                if (ringoHome == null) {
                    ringoHome = ".";
                }
            }
        }

        File home = new File(ringoHome).getCanonicalFile();
        // set System property
        System.setProperty("ringo.home", home.getPath());
        return home;
    }

    private static URL findUrl(ClassLoader loader) {
        if (loader instanceof URLClassLoader) {
            return((URLClassLoader) loader).findResource("org/ringojs/tools/launcher/Main.class");
        }
        return null;
    }

}
