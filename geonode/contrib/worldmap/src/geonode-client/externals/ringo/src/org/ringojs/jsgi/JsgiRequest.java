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

package org.ringojs.jsgi;

import org.mozilla.javascript.*;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Enumeration;
import java.lang.reflect.Method;

public class JsgiRequest extends ScriptableObject {

    Scriptable jsgiObject;
    HttpServletRequest request;
    HttpServletResponse response;
    int readonly = PERMANENT | READONLY;
    Object httpVersion;

    /**
     * Prototype constructor
     */
    public JsgiRequest(Scriptable scope) {
        setParentScope(scope);
        setPrototype(ScriptableObject.getObjectPrototype(scope));
        try {
            defineProperty("host", null, getMethod("getServerName"), null, readonly);
            defineProperty("port", null, getMethod("getServerPort"), null, readonly);
            defineProperty("queryString", null, getMethod("getQueryString"), null, readonly);
            defineProperty("version", null, getMethod("getHttpVersion"), null, readonly);
            defineProperty("remoteAddress", null, getMethod("getRemoteHost"), null, readonly);
            defineProperty("scheme", null, getMethod("getUrlScheme"), null, readonly);
        } catch (NoSuchMethodException nsm) {
            throw new RuntimeException(nsm);
        }
        // JSGI spec and Jack's lint require env.constructor to be Object
        defineProperty("constructor", ScriptableObject.getProperty(scope, "Object"), DONTENUM);
        Scriptable jsgi = jsgiObject = newObject(scope);
        Scriptable version = newArray(scope, new Object[] {Integer.valueOf(0), Integer.valueOf(3)});
        ScriptableObject.defineProperty(jsgi, "version", version, readonly);
        ScriptableObject.defineProperty(jsgi, "multithread", Boolean.TRUE, readonly);
        ScriptableObject.defineProperty(jsgi, "multiprocess", Boolean.FALSE, readonly);
        ScriptableObject.defineProperty(jsgi, "async", Boolean.TRUE, readonly);
        ScriptableObject.defineProperty(jsgi, "runOnce", Boolean.FALSE, readonly);
        ScriptableObject.defineProperty(jsgi, "cgi", Boolean.FALSE, readonly);
    }

    /**
     * Instance constructor
     */
    public JsgiRequest(HttpServletRequest request, HttpServletResponse response,
                   JsgiRequest prototype, Scriptable scope, JsgiServlet servlet) {
        this.request = request;
        this.response = response;
        setPrototype(prototype);
        setParentScope(scope);
        Scriptable jsgi = newObject(scope);
        jsgi.setPrototype(prototype.jsgiObject);
        ScriptableObject.defineProperty(this, "jsgi", jsgi, PERMANENT);
        Scriptable headers = newObject(scope);
        ScriptableObject.defineProperty(this, "headers", headers, PERMANENT);
        for (Enumeration e = request.getHeaderNames(); e.hasMoreElements(); ) {
            String name = (String) e.nextElement();
            String value = request.getHeader(name);
            name = name.toLowerCase();
            headers.put(name, headers, value);
        }
        put("scriptName", this, checkString(request.getContextPath()
                + request.getServletPath()));
        String pathInfo = request.getPathInfo();
        String uri = request.getRequestURI();
        // Workaround for Tomcat returning "/" for pathInfo even if URI doesn't end with "/"
        put("pathInfo", this, "/".equals(pathInfo) && !uri.endsWith("/") ?
                "" : checkString(pathInfo));
        put("method", this, checkString(request.getMethod()));
        Scriptable env = newObject(scope);
        ScriptableObject.defineProperty(this, "env", env, PERMANENT);
        ScriptableObject.defineProperty(env, "servlet",
                new NativeJavaObject(scope, servlet, null), PERMANENT);
        ScriptableObject.defineProperty(env, "servletRequest",
                new NativeJavaObject(scope, request, null), PERMANENT);
        ScriptableObject.defineProperty(env, "servletResponse",
                new NativeJavaObject(scope, response, null), PERMANENT);
        // JSGI spec and Jack's lint require env.constructor to be Object
        defineProperty("constructor", scope.get("Object", scope), DONTENUM);
    }

    public String getServerName() {
        return checkString(request.getServerName());
    }

    public String getServerPort() {
        return checkString(Integer.toString(request.getServerPort()));
    }

    public String getQueryString() {
        return checkString(request.getQueryString());
    }

    public Object getHttpVersion() {
        if (httpVersion == null) {
            Scriptable scope = getParentScope();
            String protocol = request.getProtocol();
            if (protocol != null) {
                int major = protocol.indexOf('/');
                int minor = protocol.indexOf('.');
                if (major > -1 && minor > major) {
                    major = Integer.parseInt(protocol.substring(major + 1, minor));
                    minor = Integer.parseInt(protocol.substring(minor + 1));
                    httpVersion =  newArray(scope, new Object[] {
                            Integer.valueOf(major), Integer.valueOf(minor)});
                }
            }
            if (httpVersion == null) {
                newArray(scope, new Object[0]);
            }
        }
        return httpVersion;
    }

    public String getRemoteHost() {
        return checkString(request.getRemoteHost());
    }

    public String getUrlScheme() {
        return request.isSecure() ? "https" : "http";
    }

    private static Method getMethod(String name) throws NoSuchMethodException {
        return JsgiRequest.class.getDeclaredMethod(name);
    }

    private static String checkString(String str) {
        return str == null ? "" : str;
    }

    // local copies of Context methods so we can create new objects/arrays
    // without entering a context
    private Scriptable newObject(Scriptable scope) {
        NativeObject result = new NativeObject();
        ScriptRuntime.setBuiltinProtoAndParent(result, scope, TopLevel.Builtins.Object);
        return result;
    }

    private Scriptable newArray(Scriptable scope, Object[] elements) {
        NativeArray result = new NativeArray(elements);
        ScriptRuntime.setBuiltinProtoAndParent(result, scope, TopLevel.Builtins.Array);
        return result;
    }

    /**
     * Return the name of the class.
     */
    @Override
    public String getClassName() {
        return "JsgiRequest";
    }
}
