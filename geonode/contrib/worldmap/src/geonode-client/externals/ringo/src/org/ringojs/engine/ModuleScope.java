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

import org.ringojs.repository.Repository;
import org.ringojs.repository.Trackable;
import org.mozilla.javascript.*;

/**
 * A scriptable object that keeps track of the resource it has been loaded from
 * so requests to load other stuff can look for local resources.
 */
public class ModuleScope extends ImporterTopLevel {

    private Trackable source;
    private Repository repository;
    private String id;
    private long checksum;
    private Scriptable exportsObject, moduleObject;
    private static final long serialVersionUID = -2409425841990094897L;

    public ModuleScope(String moduleId, Trackable source, Scriptable prototype) {
        setParentScope(null);
        setPrototype(prototype);
        // for activating the ImporterTopLevel import* functions
        activatePrototypeMap(3);
        // prototype properties include constructor property which we don't need
        delete("constructor");
        try {
            cacheBuiltins();
        } catch (NoSuchMethodError e) {
            // allows us to run with older versions of Rhino
        }
        this.source = source;
        this.repository = source instanceof Repository ?
                (Repository) source : source.getParentRepository();
        this.id = moduleId;
        // create and define module meta-object
        moduleObject = new ModuleObject(this);
        defineProperty("module", moduleObject, DONTENUM);
        // create and define exports object
        exportsObject = new ExportsObject();
        defineProperty("exports", exportsObject,  DONTENUM);
        // define non-standard module.exports object to allow
        // modules to redefine their exports.
        moduleObject.put("exports", moduleObject, exportsObject);
    }

    public Trackable getSource() {
        return source;
    }

    public Repository getRepository() {
        return repository;
    }

    public void reset() {
        Scriptable exports = new ExportsObject();
        defineProperty("exports", exports,  DONTENUM);
        moduleObject.put("exports", moduleObject, exports);
        moduleObject.delete("shared");
    }

    public long getChecksum() {
        return checksum;
    }

    public void setChecksum(long checksum) {
        this.checksum = checksum;
    }

    public String getModuleName() {
        return id;
    }

    protected void updateExports() {
        exportsObject = ScriptRuntime.toObject(
                this, ScriptableObject.getProperty(moduleObject, "exports"));
    }

    public Scriptable getExports() {
        return exportsObject;
    }

    public Scriptable getModuleObject() {
        return moduleObject;
    }

    @Override
    public String toString() {
        return "[ModuleScope " + source + "]";
    }

    @Override
    public Object getDefaultValue(Class hint) {
        if (hint == String.class || hint == null) {
            return toString();
        }
        return super.getDefaultValue(hint);
    }

    class ExportsObject extends NativeObject {
        ExportsObject() {
            setParentScope(ModuleScope.this);
            setPrototype(getObjectPrototype(ModuleScope.this));
        }

        public String getModuleName() {
            return id;
        }
    }
}
