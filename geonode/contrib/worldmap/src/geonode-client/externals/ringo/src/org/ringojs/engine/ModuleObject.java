package org.ringojs.engine;

import org.mozilla.javascript.Context;
import org.mozilla.javascript.Function;
import org.mozilla.javascript.ScriptRuntime;
import org.mozilla.javascript.Scriptable;
import org.mozilla.javascript.ScriptableObject;
import org.mozilla.javascript.Undefined;
import org.mozilla.javascript.annotations.JSFunction;
import org.mozilla.javascript.annotations.JSGetter;
import org.ringojs.repository.Repository;
import org.ringojs.repository.Resource;
import org.ringojs.repository.Trackable;

import java.io.IOException;

public class ModuleObject extends ScriptableObject {

    String id;
    Trackable source;
    Repository repository;

    public ModuleObject() {}

    ModuleObject(ModuleScope moduleScope) {
        setParentScope(moduleScope);
        setPrototype(ScriptableObject.getClassPrototype(moduleScope, "ModuleObject"));
        this.id = moduleScope.getModuleName();
        this.source = moduleScope.getSource();
        this.repository = moduleScope.getRepository();
    }

    @JSFunction
    public String resolve(Object path) throws IOException {
        String _path =  (path == null || path == Undefined.instance) ?
                "" : ScriptRuntime.toString(path);
        if (repository == null) {
            return _path;
        }
        Resource res = repository.getResource(_path);
        return  (res == null) ? _path : res.getRelativePath();
    }

    @JSFunction
    public Object singleton(Object id, Object factory) {
        if (!(id instanceof CharSequence)) {
            throw ScriptRuntime.constructError("Error",
                    "singleton() requires a string id as first argument");
        }
        Function factoryFunction = null;
        if (factory instanceof Function) {
            factoryFunction = (Function)factory;
        } else if (factory != Undefined.instance && factory != null) {
            throw ScriptRuntime.constructError("Error",
                    "Expected function as second argument");
        }
        Scriptable scope = ScriptableObject.getTopLevelScope(getParentScope());
        RhinoEngine engine = RhinoEngine.getEngine(scope);
        Singleton singleton = engine.getSingleton(new Singleton(source, id.toString()));
        return singleton.getValue(factoryFunction, scope, this);
    }

    @JSGetter
    public Object getId() {
        return id == null ? Undefined.instance : id;
    }

    @JSGetter
    public Object getPath() {
        return source == null ? Undefined.instance : source.getPath();
    }

    @JSGetter
    public Object getUri() {
        try {
            return source == null ? Undefined.instance : source.getUrl().toString();
        } catch (Exception x) {
            return Undefined.instance;
        }
    }

    @JSGetter
    public Object getDirectory() {
        return repository == null ? Undefined.instance : repository.getPath();
    }

    @Override
    protected Object equivalentValues(Object value) {
        if (value instanceof String) {
            return value.equals(id) ? Boolean.TRUE : Boolean.FALSE;
        }
        return NOT_FOUND;
    }

    @Override
    public String getClassName() {
        return "ModuleObject";
    }
}

/**
 * A wrapper around a singleton id and value.
 */
class Singleton {

    final String key;
    boolean evaluated;
    Object value;

    Singleton(Trackable source, String id) {
        this.key = source.getPath() + ":" + id;
    }

    synchronized Object getValue(Function function, Scriptable scope,
                                 ModuleObject obj) {
        if (!evaluated) {
            Context cx = Context.getCurrentContext();
            value = function.call(cx, scope, obj, ScriptRuntime.emptyArgs);
            evaluated = true; // only if evaluation was successful
        }
        return value;
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof Singleton
                && key.equals(((Singleton) obj).key);
    }

    @Override
    public int hashCode() {
        return key.hashCode();
    }
}
