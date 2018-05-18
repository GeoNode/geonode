/*
 *  Copyright 2010-2012 Hannes Wallnoefer <hannes@helma.at>
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

import org.mozilla.javascript.BaseFunction;
import org.mozilla.javascript.Context;
import org.mozilla.javascript.NativeObject;
import org.mozilla.javascript.ScriptRuntime;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.ScriptableObject;
import org.mozilla.javascript.Undefined;
import org.mozilla.javascript.WrappedException;
import org.mozilla.javascript.Wrapper;
import org.ringojs.repository.FileRepository;
import org.ringojs.repository.Repository;
import org.ringojs.repository.ZipRepository;
import org.ringojs.util.ScriptUtils;
import org.ringojs.util.StringUtils;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.lang.ref.SoftReference;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Require extends BaseFunction {

    RhinoEngine engine;
    RingoGlobal scope;

    static Method getMain;
    static {
        try {
            getMain = Require.class.getDeclaredMethod("getMain", ScriptableObject.class);
        } catch (NoSuchMethodException nsm) {
            throw new NoSuchMethodError("getMain");
        }
    }
    
    public Require(RhinoEngine engine, RingoGlobal scope) {
        super(scope, ScriptableObject.getClassPrototype(scope, "Function"));
        this.engine = engine;
        this.scope = scope;
        // Set up require.main property as setter - note that accessing this will cause
        // the main module to be loaded, which may result in problems if engine setup
        // isn't finished yet. Alas, the CommonJS Modules spec requires us to do this.
        int attr = DONTENUM | PERMANENT | READONLY;
        defineProperty("main", this, getMain, null, attr);
        defineProperty("paths", new ModulePath(), attr);
        defineProperty("extensions", new Extensions(), attr);
    }
    
    @Override
    public Object call(Context cx, Scriptable scope, Scriptable thisObj, Object[] args) {
        if (args.length != 1 || !(args[0] instanceof CharSequence)) {
            throw Context.reportRuntimeError(
                    "require() expects a single string argument");
        }
        ModuleScope moduleScope = thisObj instanceof ModuleScope ?
                (ModuleScope) thisObj : null;
        try {
            RingoWorker worker = engine.getCurrentWorker();
            if (worker == null) {
                worker = engine.getWorker();
            }
            String arg = args[0].toString();
            Scriptable module = worker.loadModuleInternal(cx, arg, moduleScope);
            return module instanceof ModuleScope ?
                    ((ModuleScope)module).getExports() : module;
        } catch (FileNotFoundException notFound) {
            throw Context.reportRuntimeError("Cannot find module '" + args[0] + "'");
        } catch (IOException iox) {
            throw Context.reportRuntimeError("Error loading module '" + args[0] + "': "  + iox);
        }
    }

    @Override
    public int getArity() {
        return 1;
    }

    public Object getMain(ScriptableObject thisObj) {
        try {
            ModuleScope main = engine.getMainModuleScope();
            return main != null ? main.getModuleObject() : Undefined.instance;
        } catch (Exception x) {
            return Undefined.instance;
        }
    }

    class Extensions extends NativeObject {
        
        public Extensions() {
            setParentScope(scope);
            setPrototype(ScriptableObject.getClassPrototype(scope, "Object"));
        }
        
        @Override
        public void put(String name, Scriptable start, Object value) {
            engine.addModuleLoader(name, value);
            super.put(name, start, value);
        }

        @Override
        public void delete(String name) {
            engine.removeModuleLoader(name);
            super.delete(name);
        }
    }

    class ModulePath extends ScriptableObject {
    
        List<Repository> paths;
        Map<String, SoftReference<Repository>> cache =
                new HashMap<String, SoftReference<Repository>>();
    
        public ModulePath() {
            this.paths = engine.getRepositories();
            for (Repository repo : paths) {
                cache.put(repo.getPath(), new SoftReference<Repository>(repo));
            }
            setParentScope(scope);
            setPrototype(ScriptableObject.getClassPrototype(scope, "Array"));
            defineProperty("length", Integer.valueOf(this.paths.size()), DONTENUM);
        }
    
        @Override
        public String getClassName() {
            return "ModulePath";
        }
    
        @Override
        public void put(int index, Scriptable start, Object value) {
            if (paths != null) {
                Repository repo;
                try {
                    repo = toRepository(value);
                } catch (IOException iox) {
                    throw new WrappedException(iox);
                }
                while (index >= paths.size()) {
                    paths.add(null);
                }
                paths.set(index, repo);
                defineProperty("length", Integer.valueOf(paths.size()), DONTENUM);
            } else {
                super.put(index, start, value);
            }
        }
    
        @Override
        public void put(String id, Scriptable start, Object value) {
            if (paths != null && "length".equals(id)) {
                int length = ScriptUtils.toInt(value, -1);
                if (length < 0) {
                    throw Context.reportRuntimeError("Invalid length value: " + value);
                }
                while (length > paths.size()) {
                    paths.add(null);
                }
                while (length < paths.size()) {
                    paths.remove(length);
                }
            }
            super.put(id, start, value);
        }
    
        @Override
        public Object get(int index, Scriptable start) {
            if (paths != null) {
                Repository value = index < paths.size() ? paths.get(index) : null;
                return value == null ? NOT_FOUND : value.getPath();
            }
            return super.get(index, start);
        }
    
        @Override
        public boolean has(int index, Scriptable start) {
            if (paths != null) {
                return index >= 0 && index < paths.size();
            }
            return super.has(index, start);
        }
    
        @Override
        public Object[] getIds() {
            if (paths != null) {
                Object[] ids = new Object[paths.size()];
                for (int i = 0; i < ids.length; i++) {
                    ids[i] = Integer.valueOf(i);
                }
                return ids;
            }
            return super.getIds();
        }
    
        private Repository toRepository(Object value) throws IOException {
            if (value instanceof Wrapper) {
                value = ((Wrapper) value).unwrap();
            }
            Repository repo = null;
            if (value instanceof Repository) {
                repo = (Repository) value;
                // repositories in module search path must be configured as root repository
                repo.setRoot();
                cache.put(repo.getPath(), new SoftReference<Repository>(repo));
            } else if (value != null && value != Undefined.instance) {
                String str = ScriptRuntime.toString(value);
                SoftReference<Repository> ref = cache.get(str);
                repo = ref == null ? null : ref.get();
                if (repo == null) {
                    File file = new File(str);
                    if (file.isFile() && StringUtils.isZipOrJarFile(str)) {
                        repo = new ZipRepository(str);
                    } else {
                        repo = new FileRepository(str);
                    }
                    cache.put(repo.getPath(), new SoftReference<Repository>(repo));
                }
            } else {
                throw Context.reportRuntimeError("Invalid module path item: " + value);
            }
            return repo;
        }
    }
    
}


