/*
 *  Copyright 2009 Hannes Wallnoefer <hannes@helma.at>
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

import org.mozilla.javascript.ScriptableObject;
import org.mozilla.javascript.Scriptable;

/**
 * A scriptable wrapper around a scriptable object.
 */
public class ScriptableWrapper extends ScriptableObject {

    private Scriptable wrapped, properties;

    public ScriptableWrapper() {}

    public ScriptableWrapper(Scriptable wrapped, Scriptable properties) {
        this.wrapped = wrapped;
        this.properties = properties;
    }

    public String getClassName() {
        return "ScriptableWrapper";
    }

    @Override
    public Object get(String name, Scriptable start) {
        if (wrapped == null) {
            return super.get(name, start);
        }
        if (name.startsWith("super$")) {
            return wrapped.get(name.substring(6), wrapped);
        }
        if (properties != null) {
            Object value = properties.get(name, properties);
            if (value != NOT_FOUND) {
                return value;
            }
        }
        return wrapped.get(name, wrapped);
    }

    @Override
    public void put(String name, Scriptable start, Object value) {
        if (wrapped == null) {
            super.put(name, this, value);
        } else {
            if (properties.has(name, start)) {
                properties.put(name, properties, value);
            } else {
                wrapped.put(name, wrapped, value);
            }
        }
    }

    @Override
    public void delete(String name) {
        if (wrapped == null) {
            super.delete(name);
        } else {
            if (properties.has(name, properties)) {
                properties.delete(name);
            } else {
                wrapped.delete(name);
            }
        }
    }

    @Override
    public boolean has(String name, Scriptable start) {
        if (wrapped == null) {
            return super.has(name, this);
        }
        return wrapped.has(name, wrapped) || properties.has(name, properties);
    }
}
