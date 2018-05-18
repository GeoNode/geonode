package org.ringojs.wrappers;

import org.mozilla.javascript.*;
import org.mozilla.javascript.annotations.JSStaticFunction;
import org.mozilla.javascript.annotations.JSFunction;
import org.mozilla.javascript.annotations.JSGetter;
import org.ringojs.util.ScriptUtils;

public class Storable extends ScriptableObject {

    private Scriptable store;
    private String type;
    private boolean isPrototype;

    private Scriptable properties;
    private Object key;
    private Object entity;

    enum FactoryType {CONSTRUCTOR, FACTORY}

    public Storable() {
        this.isPrototype = true;
    }

    private Storable(Scriptable store, String type) {
        this.store = store;
        this.type = type;
        this.isPrototype = true;
    }

    private Storable(Storable prototype) {
        this.store = prototype.store;
        this.type = prototype.type;
        this.isPrototype = false;
    }

    static class FactoryFunction extends BaseFunction {

        Storable prototype;
        FactoryType factoryType;

        FactoryFunction(Storable prototype, Scriptable scope, FactoryType factoryType) {
            this.prototype = prototype;
            this.factoryType = factoryType;
            ScriptRuntime.setFunctionProtoAndParent(this, scope);
        }

        @Override
        public Object call(Context cx, Scriptable scope, Scriptable thisObj, Object[] args) {
            Storable storable = new Storable(prototype);
            switch (factoryType) {
                case CONSTRUCTOR:
                    ScriptUtils.checkArguments(args, 0, 1);
                    Scriptable properties = ScriptUtils.getScriptableArgument(args, 0, true);
                    if (properties == null) {
                        properties = cx.newObject(scope);
                    }
                    storable.properties = properties;
                    break;
                case FACTORY:
                    ScriptUtils.checkArguments(args, 1, 2);
                    storable.key = ScriptUtils.getObjectArgument(args, 0, false);
                    storable.entity = ScriptUtils.getObjectArgument(args, 1, true);
                    break;
            }
            storable.setParentScope(scope);
            storable.setPrototype(prototype);
            return storable;
        }

        @Override
        public int getArity() {
            return factoryType == FactoryType.CONSTRUCTOR ? 1 : 2;
        }

        @Override
        public String getFunctionName() {
            return prototype.getType();
        }

        @Override
        public int getLength() {
            return getArity();
        }
    }

    @JSStaticFunction
    public static Scriptable defineEntity(Scriptable store, String type, Object mapping)
            throws NoSuchMethodException {
        int attr = DONTENUM | PERMANENT | READONLY;
        Scriptable scope = ScriptRuntime.getTopCallScope(Context.getCurrentContext());
        Storable prototype = new Storable(store, type);
        prototype.setParentScope(scope);
        prototype.setPrototype(ScriptableObject.getClassPrototype(scope, "Storable"));
        // create the constructor, visible to the application
        BaseFunction ctor = new FactoryFunction(prototype, scope, FactoryType.CONSTRUCTOR);
        ctor.setImmunePrototypeProperty(prototype);
        defineProperty(prototype, "constructor", ctor, attr);
        // create the factory function, visible to the store implementation
        BaseFunction factory = new FactoryFunction(prototype, scope, FactoryType.FACTORY);
        ScriptableObject.defineProperty(ctor, "createInstance", factory, attr);
        if (mapping != Undefined.instance) {
            ctor.defineProperty("mapping", mapping, attr);
            factory.defineProperty("mapping", mapping, attr);
        }
        return ctor;
    }

    public String getClassName() {
        return "Storable";
    }

    /**
     * Custom <tt>==</tt> operator.
     * Must return {@link org.mozilla.javascript.Scriptable#NOT_FOUND} if this object does not
     * have custom equality operator for the given value,
     * <tt>Boolean.TRUE</tt> if this object is equivalent to <tt>value</tt>,
     * <tt>Boolean.FALSE</tt> if this object is not equivalent to
     * <tt>value</tt>.
     * <p/>
     * The default implementation returns Boolean.TRUE
     * if <tt>this == value</tt> or {@link org.mozilla.javascript.Scriptable#NOT_FOUND} otherwise.
     * It indicates that by default custom equality is available only if
     * <tt>value</tt> is <tt>this</tt> in which case true is returned.
     */
    @Override
    protected Object equivalentValues(Object value) {
        if (this == value) {
            return Boolean.TRUE;
        }
        if (value instanceof Storable && isPersistent()) {
            Storable s = (Storable) value;
            return invokeStoreMethod("equalKeys", key, s.key);
        }
        return NOT_FOUND;
    }

    @JSFunction
    public void save(Object transaction) {
        if (!isPrototype) {
            if (entity == null) {
                entity = invokeStoreMethod("getEntity", type, properties != null ? properties : key);
            }
            if (transaction == Undefined.instance) {
                invokeStoreMethod("save", properties, entity);
            } else {
                invokeStoreMethod("save", properties, entity, transaction);
            }
        }
    }

    @JSFunction("remove")
    public void jsremove(Object transaction) {
        if (!isPrototype && isPersistent()) {
            if (key == null) {
                key = invokeStoreMethod("getKey", type, entity);
            }
            if (transaction == Undefined.instance) {
                invokeStoreMethod("remove", key);
            } else {
                invokeStoreMethod("remove", key, transaction);
            }
        }
    }

    @JSGetter("_key")
    public Object getKey() {
        if (!isPrototype && isPersistent()) {
            if (key == null) {
                key = invokeStoreMethod("getKey", type, entity);
            }
            return key;
        }
        return Undefined.instance;
    }

    @JSGetter("_id")
    public Object getId() {
        Object k = getKey();
        if (k != Undefined.instance) {
            return invokeStoreMethod("getId", k);
        }
        return Undefined.instance;
    }

    @Override
    public boolean has(String name, Scriptable start) {
        if (super.has(name, this)) {
            return true;
        }
        if (isPrototype) {
            return super.has(name, start);
        }
        if (properties == null && isPersistent()) {
            properties = loadProperties();
        }
        return properties != null && properties.has(name, properties);
    }

    @Override
    public Object get(String name, Scriptable start) {
        if (isPrototype || super.has(name, this)) {
            return super.get(name, start);
        }
        if (properties == null && isPersistent()) {
            properties = loadProperties();
        }
        return properties == null ? Scriptable.NOT_FOUND : properties.get(name, properties);
    }

    @Override
    public void put(String name, Scriptable start, Object value) {
        if (isPrototype || super.has(name, this)) {
            super.put(name, start, value);
        } else {
            if (properties == null) {
                properties = loadProperties();
            }
            properties.put(name, properties, value);
        }
    }

    @Override
    public void delete(String name) {
        if (isPrototype || super.has(name, this)) {
            super.delete(name);
        } else {
            if (properties == null) {
                properties = loadProperties();
            }
            properties.put(name, properties, null);
        }
    }

    public Object[] getIds() {
        if (isPrototype) {
            return super.getIds();
        }
        if (properties == null) {
            properties = loadProperties();
        }
        return properties.getIds();
    }

    public String getType() {
        return type;
    }

    private boolean isPersistent() {
        return key != null || entity != null;
    }

    private Scriptable loadProperties() {
        if (entity == null) {
            entity = invokeStoreMethod("getEntity", type, key);
        }
        return (Scriptable) invokeStoreMethod("getProperties", store, entity);
    }

    private Object invokeStoreMethod(String method, Object... args) {
        Object value = ScriptableObject.getProperty(store, method);
        if (value instanceof Callable) {
            return ((Callable) value).call(Context.getCurrentContext(), getParentScope(), store, args);
        }
        throw new RuntimeException("Store does not implement '" + method + "' method");
    }

}
