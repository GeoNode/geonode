/*
 *  Copyright 2012 Hannes Wallnoefer <hannes@helma.at>
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

import org.mozilla.javascript.Context;
import org.mozilla.javascript.Function;
import org.mozilla.javascript.GeneratedClassLoader;
import org.mozilla.javascript.Script;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.SecurityController;
import org.mozilla.javascript.json.JsonParser;
import org.ringojs.repository.Resource;

import java.io.IOException;
import java.io.InputStream;
import java.security.AccessController;
import java.security.PrivilegedAction;

public abstract class ModuleLoader {

    private String extension;

    public ModuleLoader(String extension) {
        this.extension = extension;
    }

    public String getExtension() {
        return extension;
    }

    public abstract Object load(Context cx,  RhinoEngine engine,
                                Object securityDomain, String moduleName, 
                                String charset, Resource resource) throws Exception;
    
}

class JsModuleLoader extends ModuleLoader {

    public JsModuleLoader() {
        super(".js");
    }

    @Override
    public Object load(final Context cx,  RhinoEngine engine, final Object securityDomain,
                       String moduleName, String charset, final Resource resource)
            throws Exception {
        return AccessController.doPrivileged(new PrivilegedAction<Object>() {
            public Object run() {
                try {
                    return cx.compileReader(resource.getReader(),
                            resource.getRelativePath(),
                            resource.getLineNumber(), securityDomain);
                } catch (IOException iox) {
                    throw new RuntimeException(iox);
                }
            }
        });
    }
}

class JsonModuleLoader extends ModuleLoader {

    public JsonModuleLoader() {
        super(".json");
    }

    @Override
    public Object load(Context cx, RhinoEngine engine, Object securityDomain,
                       String moduleName, String charset, Resource resource)
                       throws Exception {
        JsonParser json = new JsonParser(cx, engine.getScope());
        return json.parseValue(resource.getContent());
    }
}

class ClassModuleLoader extends ModuleLoader {

    public ClassModuleLoader() {
        super(".class");
    }

    @Override
    public Object load(Context cx,  RhinoEngine engine, Object securityDomain,
                       String moduleName, String charset, Resource resource)
                       throws Exception {
        long l = resource.getLength();
        if (l > Integer.MAX_VALUE) {
            throw new IOException("File too large: " + l);
        }

        int length = (int) l;
        byte[] bytes = new byte[length];
        InputStream input = resource.getInputStream();
        int offset = 0, read;

        while (offset < length) {
            read = input.read(bytes, offset, length - offset);
            if (read < 0) break;
            offset += read;
        }

        if (offset < length) {
            throw new IOException("Could not read file completely");
        }
        input.close();

        String className = moduleName.replaceAll("/", ".");
        ClassLoader rhinoLoader = getClass().getClassLoader();
        GeneratedClassLoader loader;
        loader = SecurityController.createLoader(rhinoLoader, securityDomain);
        
        Class<?> clazz = loader.defineClass(className, bytes);
        loader.linkClass(clazz);
        if (!Script.class.isAssignableFrom(clazz)) {
            throw new ClassCastException("Module must be a Rhino script class");
        }
        
        return clazz.newInstance();
    }
}

class ScriptedModuleLoader extends ModuleLoader {
    
    Function function;

    public ScriptedModuleLoader(String extension, Function function) {
        super(extension);
        this.function = function;
    }
    
    @Override
    public Object load(Context cx, RhinoEngine engine, Object securityDomain,
                       String moduleName, String charset, Resource resource)
                       throws Exception {
        Scriptable scope = engine.getScope();
        Object[] args = {cx.getWrapFactory().wrap(cx, scope, resource, null)};
        Object source = function.call(cx, scope, scope, args);

        if (source instanceof CharSequence) {
            return cx.compileString(source.toString(), resource.getRelativePath(),
                    resource.getLineNumber(), securityDomain);
        } else if (source instanceof Scriptable) {
            return source;
        } else {
            throw new RuntimeException("Loader must return script or object");
        }
    }
}