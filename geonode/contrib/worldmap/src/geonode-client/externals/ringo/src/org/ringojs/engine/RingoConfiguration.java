/*
 *  Copyright 2008 Hannes Wallnoefer <hannes@helma.at>
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

package org.ringojs.engine;

import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.WrapFactory;
import org.ringojs.util.StringUtils;
import org.ringojs.repository.*;
import org.mozilla.javascript.ClassShutter;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.URLDecoder;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;
import java.util.Collections;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.logging.Logger;

/**
 * This class describes the configuration for a RingoJS application or shell session.
 * @author hannes
 */
public class RingoConfiguration {

    private Repository home;
    private Repository base;
    private List<Repository> repositories;
    private Resource mainResource;
    private String[] arguments;
    private int optimizationLevel = 0;
    private boolean strictVars = true;
    private boolean debug = false;
    private boolean verbose = false;
    private int languageVersion = 180;
    private boolean parentProtoProperties = false;
    private Class<Scriptable>[] hostClasses = null;
    private ClassShutter classShutter = null;
    private WrapFactory wrapFactory = null;
    private List<String> bootstrapScripts;
    private boolean sealed = false;
    private boolean policyEnabled = false;
    private boolean reloading = true;
    private String charset = "UTF-8";

    /**
     * Create a new Ringo configuration and sets up its module search path.
     *
     * @param ringoHome the ringo installation directory
     * @param userModules the module search path as list of paths
     * @param systemModules system module path to append to module path, or null
     * @throws FileNotFoundException if a moudule path item does not exist
     */
    public RingoConfiguration(Repository ringoHome, String[] userModules,
                              String[] systemModules) throws IOException {
        this(ringoHome, null, userModules, systemModules);
    }

    /**
     * Create a new Ringo configuration and sets up its module search path.
     *
     * @param ringoHome the ringo installation directory
     * @param basePath the path to resolve application against, pass null for
     *                 for current working directory
     * @param userModules the module search path as list of paths
     * @param systemModules system module path to append to module path, or null
     * @throws FileNotFoundException if a moudule path item does not exist
     */
    public RingoConfiguration(Repository ringoHome, Repository basePath,
                              String[] userModules, String[] systemModules)
            throws IOException {
        repositories = new ArrayList<Repository>();
        home = ringoHome;
        home.setAbsolute(true);
        if (basePath != null) {
            base = basePath;
            base.setAbsolute(true);
        }

        String optLevel = System.getProperty("rhino.optlevel");
        if (optLevel != null) {
            optimizationLevel = Integer.parseInt(optLevel);
        }
        String langVersion = System.getProperty("rhino.langversion");
        if (langVersion != null) {
            languageVersion = Integer.parseInt(langVersion);
        }
        String parentProto = System.getProperty("rhino.parentproto");
        if (parentProto != null) {
            parentProtoProperties = Integer.parseInt(parentProto) != 0;
        }

        if (userModules != null) {
            for (String pathElem : userModules) {
                String path = pathElem.trim();
                addModuleRepository(resolveRepository(path, false));
            }
        }

        // append system modules path relative to ringo home
        if (systemModules != null) {
            for (String pathElem : systemModules) {
                String path = pathElem.trim();
                addModuleRepository(resolveRepository(path, true));
            }
        }

        // now that repositories are set up try to set default log4j configuration file
        if (System.getProperty("log4j.configuration") == null) {
            Resource log4jConfig = getResource("config/log4j.properties");
            if (log4jConfig != null && log4jConfig.exists()) {
                try {
                    System.setProperty("log4j.configuration", log4jConfig.getUrl().toString());
                } catch (MalformedURLException x) {
                    System.setProperty("log4j.configuration", "file:" + log4jConfig.getPath());
                }
            }
        }
        getLogger().fine("Parsed repository list: " + repositories);
    }

    /**
     * Add a repository to the module search path.
     * @param repository the repository to add.
     */
    public void addModuleRepository(Repository repository) {
        if (repository != null) {
            repository.setRoot();
            repositories.add(repository);
        }
    }

    /**
     * Resolve a module repository path.
     * @param path the path
     * @param system whether repository should be resolved as system repository
     * @return a repository
     * @throws IOException if an I/O error happened while resolving
     */
    public Repository resolveRepository(String path, boolean system)
            throws IOException {
        File file = new File(path);
        if (!file.isAbsolute()) {
            // Try to resolve against root/base repository or classpath
            Repository parent = system ? home : base;
            Repository repo = resolveRepository(path, parent);
            if (repo != null) return repo;
            // then try to resolve against current directory
            file = file.getAbsoluteFile();
        }

        // make absolute
        file = file.getAbsoluteFile();

        if (file.isFile() && StringUtils.isZipOrJarFile(path)) {
            return new ZipRepository(file);
        } else {
            return new FileRepository(file);
        }
    }

    private Repository resolveRepository(String path, Repository parent)
            throws IOException {
        // Try to resolve against parent repository
        Repository repository;
        if (parent != null) {
            repository = parent.getChildRepository(path);
            if (repository != null && repository.exists()) {
                repository.setRoot();
                return repository;
            }
        }
        // Try to resolve path in main classloader classpath
        ClassLoader loader = RingoConfiguration.class.getClassLoader();
        repository = repositoryFromClasspath(path, loader);
        if (repository != null && repository.exists()) {
            repository.setRoot();
            return repository;
        }
        return null;
    }

    /**
     * Set the main script for this configuration. If the scriptName argument is not null,
     * we check whether the script is already contained in the ringo module path.
     *
     * If not, the script's parent repository is prepended to the module path. If scriptName is
     * null, we prepend the current working directory to the module path.
     * @param scriptName the name of the script, or null.
     * @throws FileNotFoundException if the script repository does not exist
     */
    public void setMainScript(String scriptName) throws IOException {
        if (scriptName != null) {
            File file = new File(scriptName);
            // check if the script is a zip file
            if (file.isFile() && StringUtils.isZipOrJarFile(scriptName)) {
                ZipRepository zipRepo = new ZipRepository(new File(scriptName));
                mainResource = zipRepo.getResource("main.js");
                if (mainResource.exists()) {
                    repositories.add(0, zipRepo);
                    return;
                }
            }
            // check if script is a path within a zip file
            int zip = scriptName.toLowerCase().indexOf(".zip/");
            if (zip > -1) {
                String zipFile = scriptName.substring(0, zip + 4);
                String scriptPath = scriptName.substring(zip + 5);
                ZipRepository zipRepo = new ZipRepository(new File(zipFile));
                mainResource = zipRepo.getResource(scriptPath);
                if (mainResource.exists()) {
                    repositories.add(0, zipRepo);
                    return;
                }
            }
            // check if the script exists as a standalone file
            Resource script = new FileResource(file);
            if (script.exists()) {
                // check if we are contained in one of the existing repositories
                String scriptPath = script.getPath();
                for (Repository repo : repositories) {
                    if (repo instanceof FileRepository && scriptPath.indexOf(repo.getPath()) == 0) {
                        // found a repository that contains main script - use it as base for module name
                        // reparent to make sure script resource is relative to parent
                        mainResource = repo.getResource(scriptPath.substring(repo.getPath().length()));
                        return;
                    }
                }
                // not found in the existing repositories - note that we do not add
                // parent directory as first element of module path anymore.
                // Instead, the script is set to absolute mode so module id will return the absolute path
                script.setAbsolute(true);
                mainResource = script;
            } else {
                // check if the script can be found in the module path
                script = getResource(scriptName);
                if (!script.exists()) {
                    // try converting module name to file path and lookup in module path
                    script = getResource(scriptName + ".js");
                }
                if (!script.exists()) {
                    // no luck resolving the script name, give up
                    throw new FileNotFoundException("Can't find file " + scriptName);
                }
                // found the script, so set mainModule
                mainResource = script;
            }
        }
    }

    /**
     * Get the main script resource resolved by calling {@link #setMainScript(String)}.
     * @return the main script resource, or null
     */
    public Resource getMainResource() {
        return mainResource;
    }

    /**
     * Return the ringo install directory
     * @return the ringo home directory
     */
    public Repository getRingoHome() {
        return home;
    }

    /**
     * Get a list of repositoris from the given ringoHome and ringoPath settings
     * using the ringo.home and ringo.path system properties as fallback.
     * @return a list of repositories matching the arguments and/or system properties
     */
    public List<Repository> getRepositories() {
        return repositories;
    }

    /**
     * Get the module name of the main resource of the configuration.
     * @return the name of the main module
     */
    public String getMainModule() {
        return (mainResource == null)? null : mainResource.getModuleName();
    }

    /**
     * Set the host classes to be added to the Rhino engine.
     * @param classes a list of Rhino host classes
     */
    public void setHostClasses(Class<Scriptable>[] classes) {
        this.hostClasses = classes;
    }

    /**
     * Get the host classes to be added to the Rhino engine.
     * @return a list of Rhino host classes
     */
    public Class<Scriptable>[] getHostClasses() {
        return hostClasses;
    }

    /**
     * Get the Rhino optimization level
     * @return int value between -1 and 9
     */
    public int getOptLevel() {
        // always use optimization level -1  if running debugger
        return debug ? -1 : optimizationLevel;
    }

    /**
     * Set the Rhino optimization level
     * @param optlevel int value between -1 and 9
     */
    public void setOptLevel(int optlevel) {
        this.optimizationLevel = optlevel;
    }

    public boolean getDebug() {
        return debug;
    }

    public void setDebug(boolean debug) {
        this.debug = debug;
    }

    public boolean isVerbose() {
        return verbose;
    }

    public void setVerbose(boolean verbose) {
        this.verbose = verbose;
        System.setProperty("ringo.verbose", String.valueOf(verbose));
    }

    public boolean getStrictVars() {
        return strictVars;
    }

    public void setStrictVars(boolean strictVars) {
        this.strictVars = strictVars;
    }

    /**
     * Get the desired JavaScript langauge version
     * @return int value between 0 and 180
     */
    public int getLanguageVersion() {
        return languageVersion;
    }

    /**
     * Get the flag to enable __parent__ and __proto__ properties on JS objects
     * @return true if __parent__ and __proto__ properties should be enabled
     */
    public boolean hasParentProtoProperties() {
        return parentProtoProperties;
    }

    /**
     * Set the flag to enable __parent__ and __proto__ properties on JS objects
     * @param flag true to enable __parent__ and __proto__ properties
     */
    public void setParentProtoProperties(boolean flag) {
        this.parentProtoProperties = flag;
    }

    /**
     * Get a resource from our script repository
     * @param path the resource path
     * @return the resource
     * @throws IOException an I/O error occurred
     */
    public Resource getResource(String path) throws IOException {
        return getResource(path, null);
    }
    /**
     * Get a resource from our script repository
     * @param path the resource path
     * @param loaders optional list of module loaders
     * @return the resource
     * @throws IOException an I/O error occurred
     */
    public Resource getResource(String path, ModuleLoader[] loaders)
            throws IOException {
        Resource res;
        for (Repository repo: repositories) {
            if (loaders != null) {
                assert loaders.length > 0 && loaders[0] != null;
                for (ModuleLoader loader : loaders) {
                    res = repo.getResource(path + loader.getExtension());
                    if (res != null && res.exists()) {
                        return res;
                    }
                }
            } else {
                res = repo.getResource(path);
                if (res != null && res.exists()) {
                    return res;
                }
            }
        }
        if (loaders == null) {
            res = resourceFromClasspath(path, null);
            if (res != null && res.exists()) {
                return res;
            }
        } else {
            for (ModuleLoader loader : loaders) {
                String p = path + loader.getExtension();
                res = resourceFromClasspath(p, null);
                if (res != null && res.exists()) {
                    return res;
                }
            }
        }
        return new NotFound(path);
    }

    /**
     * Get a resource from our script repository
     * @param path the resource path
     * @return the resource
     * @throws IOException an I/O error occurred
     */
    public Repository getRepository(String path) throws IOException {
        Repository repo;
        for (Repository parent: repositories) {
            repo = parent.getChildRepository(path);
            if (repo != null && repo.exists()) {
                return repo;
            }
        }
        repo = repositoryFromClasspath(path, null);
        if (repo != null && repo.exists()) {
            return repo;
        }
        return new NotFound(path);
    }

    /**
     * Get a list of all child resources for the given path relative to
     * our script repository.
     * @param path the repository path
     * @param recursive whether to include nested resources
     * @return a list of all contained child resources
     * @throws IOException an I/O error occurred
     */
    public List<Resource> getResources(String path, boolean recursive) throws IOException {
        List<Resource> list = new ArrayList<Resource>();
        for (Repository repo: repositories) {
            Collections.addAll(list, repo.getResources(path, recursive));
        }
        return list;
    }

    public String getCharset() {
        return charset;
    }

    public void setCharset(String charset) {
        this.charset = charset;
    }

    public ClassShutter getClassShutter() {
        return classShutter;
    }

    public void setClassShutter(ClassShutter classShutter) {
        this.classShutter = classShutter;
    }

    public WrapFactory getWrapFactory() {
        if (wrapFactory == null) {
            wrapFactory = new RingoWrapFactory();
        }
        return wrapFactory;
    }

    public void setWrapFactory(WrapFactory wrapFactory) {
        this.wrapFactory = wrapFactory;
    }

    public boolean isSealed() {
        return sealed;
    }

    public void setSealed(boolean sealed) {
        this.sealed = sealed;
    }

    public boolean isReloading() {
        return reloading;
    }

    public void setReloading(boolean reloading) {
        this.reloading = reloading;
    }

    public boolean isPolicyEnabled() {
        return policyEnabled;
    }

    public void setPolicyEnabled(boolean hasPolicy) {
        this.policyEnabled = hasPolicy;
    }

    public List<String> getBootstrapScripts() {
        return bootstrapScripts;
    }

    public String[] getArguments() {
        return arguments;
    }

    public void setArguments(String[] arguments) {
        this.arguments = arguments;
    }

    public void setBootstrapScripts(List<String> bootstrapScripts) {
        this.bootstrapScripts = bootstrapScripts;
    }

    private static Logger getLogger() {
        return Logger.getLogger("org.ringojs.tools");
    }

    private static Repository toZipRepository(URL url) throws IOException {
        String nested = url.getPath();
        int excl = nested.indexOf("!");

        if (excl > -1) {
            nested = nested.substring(0, excl);
            try {
                url = new URL(nested);
            } catch (MalformedURLException e) {
                // try with the file prefix
                url = new URL("file://" + nested);
            }

            if ("file".equals(url.getProtocol())) {
                String enc = Charset.defaultCharset().name();
                return new ZipRepository(URLDecoder.decode(url.getPath(), enc));
            }
        }
        return null;
    }

    private static Resource resourceFromClasspath(String path, ClassLoader loader)
            throws IOException {
        String canonicalPath = path.endsWith("/") ?
                path.substring(0, path.length() - 1) : path;
        URL url = urlFromClasspath(canonicalPath, loader);
        if (url != null) {
            String proto = url.getProtocol();
            if ("jar".equals(proto) || "zip".equals(proto) || "wsjar".equals(proto)) {
                Repository repo = toZipRepository(url);
                return repo.getResource(path);
            } else if ("file".equals(proto)) {
                String enc = Charset.defaultCharset().name();
                return new FileResource(URLDecoder.decode(url.getPath(), enc));
            }
        }
        return null;
    }

    private static Repository repositoryFromClasspath(String path, ClassLoader loader)
            throws IOException {
        String canonicalPath = path.endsWith("/") ? path : path + "/";
        URL url = urlFromClasspath(canonicalPath, loader);
        if (url != null) {
            String proto = url.getProtocol();
            if ("jar".equals(proto) || "zip".equals(proto) || "wsjar".equals(proto)) {
                Repository repo = toZipRepository(url);
                return repo.getChildRepository(path);
            } else if ("file".equals(proto)) {
                String enc = Charset.defaultCharset().name();
                return new FileRepository(URLDecoder.decode(url.getPath(), enc));
            }
        }
        return null;
    }

    private static URL urlFromClasspath(String path, ClassLoader loader) {
        if (loader == null) {
            loader = Thread.currentThread().getContextClassLoader();
        }
        if (loader == null) {
            loader = RingoConfiguration.class.getClassLoader();
        }
        if (loader == null) {
            return null;
        }
        return loader.getResource(path);
    }
}

/**
 * This is used as return value in {@link RingoConfiguration#getResource(String)}
 * and {@link RingoConfiguration#getRepository(String)} when the given path
 * could not be resolved.
 */
class NotFound extends AbstractResource implements Repository {

    NotFound(String path) {
        this.path = path;
        int slash = path.lastIndexOf('/');
        this.name = slash < 0 ? path : path.substring(slash + 1);
        setBaseNameFromName(name);
    }

    public long getLength() {
        return 0;
    }

    public InputStream getInputStream() throws IOException {
        throw new FileNotFoundException("\"" + path + "\" not found");
    }

    public long lastModified() {
        return 0;
    }

    public boolean exists() {
        return false;
    }

    public Repository getChildRepository(String path) throws IOException {
        return this;
    }

    public Resource getResource(String resourceName) throws IOException {
        return this;
    }

    public Resource[] getResources() throws IOException {
        return new Resource[0];
    }

    public Resource[] getResources(boolean recursive) throws IOException {
        return new Resource[0];
    }

    public Resource[] getResources(String resourcePath, boolean recursive) throws IOException {
        return new Resource[0];
    }

    public Repository[] getRepositories() throws IOException {
        return new Repository[0];
    }

    public void setRoot() {}

    public URL getUrl() throws UnsupportedOperationException, MalformedURLException {
        throw new UnsupportedOperationException("Unable to resolve \"" + path + "\"");
    }

    public String toString() {
        return "Resource \"" + path + "\"";
    }
}
