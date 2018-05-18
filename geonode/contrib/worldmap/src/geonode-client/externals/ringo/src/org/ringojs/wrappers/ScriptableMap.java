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

package org.ringojs.wrappers;

import org.mozilla.javascript.*;
import org.ringojs.util.ScriptUtils;

import java.util.Map;
import java.util.HashMap;

/**
 * ScriptableMap is a wrapper for java.util.Map instances that allows developers
 * to interact with them as if it were a native JavaScript object.
 */
public class ScriptableMap extends NativeJavaObject {

    boolean reflect;
    Map map;
    final static String CLASSNAME = "ScriptableMap";

    // Set up a custom constructor, for this class is somewhere between a host class and
    // a native wrapper, for which no standard constructor class exists
    public static void init(Scriptable scope) throws NoSuchMethodException {
        BaseFunction ctor = new BaseFunction(scope, ScriptableObject.getFunctionPrototype(scope)) {
            @Override
            public Scriptable construct(Context cx, Scriptable scope, Object[] args) {
                boolean reflect = false;
                if (args.length > 2) {
                    throw new EvaluatorException("ScriptableMap() called with too many arguments");
                } if (args.length == 2) {
                    reflect = ScriptRuntime.toBoolean(args[1]);
                }
                return new ScriptableMap(scope, args.length == 0 ? null : args[0], reflect);
            }
            @Override
            public Object call(Context cx, Scriptable scope, Scriptable thisObj, Object[] args) {
                return construct(cx, scope, args);
            }
        };
        ScriptableObject.defineProperty(scope, CLASSNAME, ctor,
                ScriptableObject.DONTENUM | ScriptableObject.READONLY);
    }

    @SuppressWarnings("unchecked")
    private ScriptableMap(Scriptable scope, Object obj, boolean reflect) {
        this.parent = scope;
        this.reflect = reflect;
        if (obj instanceof Wrapper) {
            obj = ((Wrapper) obj).unwrap();
        }
        if (obj instanceof Map) {
            this.map = (Map) obj;
        } else if (obj == null || obj == Undefined.instance) {
            this.map = new HashMap();
        } else if (obj instanceof Scriptable) {
            this.map = new HashMap();
            Scriptable s = (Scriptable) obj;
            Object[] ids = s.getIds();
            for (Object id: ids) {
                if (id instanceof String) {
                    map.put(id, s.get((String)id, s));
                } else if (id instanceof Number) {
                    map.put(id, s.get(((Number)id).intValue(), s));
                }
            }
        } else {
            throw new EvaluatorException("Invalid argument to ScriptableMap(): " + obj);
        }
        this.javaObject = this.map;
        this.staticType = this.map.getClass();
        initMembers();
        initPrototype(scope);

    }

    public ScriptableMap(Scriptable scope, Map map) {
        super(scope, map, map.getClass());
        this.map = map;
        initPrototype(scope);
    }

    /**
     * Set the prototype to the Array prototype so we can use array methds such as
     * push, pop, shift, slice etc.
     * @param scope the global scope for looking up the Array constructor
     */
    protected void initPrototype(Scriptable scope) {
        Scriptable arrayProto = ScriptableObject.getClassPrototype(scope, "Object");
        if (arrayProto != null) {
            this.setPrototype(arrayProto);
        }
    }

    public Object get(String name, Scriptable start) {
        if (map == null || (reflect && super.has(name, start))) {
            return super.get(name, start);
        }
        return getInternal(name);
    }

    public Object get(int index, Scriptable start) {
        if (map == null) {
            return super.get(index, start);
        }
        return getInternal(new Integer(index));
    }

    private Object getInternal(Object key) {
        Object value = map.get(key);
        if (value == null) {
            return Scriptable.NOT_FOUND;
        }
        return ScriptUtils.javaToJS(value, getParentScope());
    }

    public boolean has(String name, Scriptable start) {
        if (map == null || (reflect && super.has(name, start))) {
            return super.has(name, start);
        } else {
            return map.containsKey(name);
        }
    }

    public boolean has(int index, Scriptable start) {
        if (map == null) {
            return super.has(index, start);
        } else {
            return map.containsKey(new Integer(index));
        }
    }

    public void put(String name, Scriptable start, Object value) {
        if (map == null || (reflect && super.has(name, start))) {
            super.put(name, start, value);
        } else {
            putInternal(name, value);
        }
    }

    public void put(int index, Scriptable start, Object value) {
        if (map == null) {
             super.put(index, start, value);
         } else {
             putInternal(new Integer(index), value);
        }
    }

    @SuppressWarnings("unchecked")
    private void putInternal(Object key, Object value) {
        try {
            map.put(key, ScriptUtils.jsToJava(value));
        } catch (RuntimeException e) {
            Context.throwAsScriptRuntimeEx(e);
        }
    }

    public void delete(String name) {
        if (map != null) {
            try {
                map.remove(name);
            } catch (RuntimeException e) {
                Context.throwAsScriptRuntimeEx(e);
            }
        } else {
            super.delete(name);
        }
    }

    public void delete(int index) {
        if (map != null) {
            try {
                map.remove(new Integer(index));
            } catch (RuntimeException e) {
                Context.throwAsScriptRuntimeEx(e);
            }
        } else {
            super.delete(index);
        }
    }

    public Object[] getIds() {
        if (map == null) {
            return super.getIds();
        } else {
            return map.keySet().toArray();
        }
    }

    public String toString() {
        if (map == null)
            return super.toString();
        return map.toString();
    }

    public Object getDefaultValue(Class typeHint) {
        return toString();
    }

    public Object unwrap() {
        return map;
    }

    public Map getMap() {
        return map;
    }

    public String getClassName() {
        return CLASSNAME;
    }
}