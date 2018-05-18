/*
 * Helma License Notice
 *
 * The contents of this file are subject to the Helma License
 * Version 2.0 (the "License"). You may not use this file except in
 * compliance with the License. A copy of the License is available at
 * http://adele.helma.org/download/helma/license.txt
 *
 * Copyright 2005 Hannes Wallnoefer. All Rights Reserved.
 */
package org.ringojs.engine;

import org.mozilla.javascript.*;
import org.mozilla.javascript.tools.ToolErrorReporter;
import org.ringojs.repository.Resource;

import java.security.AccessController;
import java.security.PrivilegedAction;
import java.util.HashMap;
import java.util.ArrayList;

public class RingoContextFactory extends ContextFactory {

    RhinoEngine engine;

    int languageVersion = Context.VERSION_1_8;
    boolean strictMode = false;
    boolean strictVars = true;
    boolean warningAsError = false;
    boolean parentProtoProperties = true;
    int optimizationLevel = 0;
    boolean generatingDebug = true;
    ClassShutter classShutter;

    static int instructionLimit = 0xfffffff;

    public RingoContextFactory(RhinoEngine engine, RingoConfiguration config) {
        this.engine = engine;
        optimizationLevel = config.getOptLevel();
        languageVersion = config.getLanguageVersion();
        parentProtoProperties = config.hasParentProtoProperties();
        classShutter = config.getClassShutter();
        strictVars = config.getStrictVars();
    }

    @Override
    protected boolean hasFeature(Context cx, int featureIndex) {
        switch (featureIndex) {
            case Context.FEATURE_STRICT_VARS:
                return strictVars;

            case Context.FEATURE_STRICT_EVAL:
            case Context.FEATURE_STRICT_MODE:
                return strictMode;

            case Context.FEATURE_RESERVED_KEYWORD_AS_IDENTIFIER:
                return true;

            case Context.FEATURE_WARNING_AS_ERROR:
                return warningAsError;

            case Context.FEATURE_PARENT_PROTO_PROPERTIES:
                return parentProtoProperties;

            case Context.FEATURE_LOCATION_INFORMATION_IN_ERROR:
                return true;
        }

        return super.hasFeature(cx, featureIndex);
    }

    @Override
    protected void onContextCreated(Context cx) {
        super.onContextCreated(cx);
        AccessController.doPrivileged(new PrivilegedAction<Void>() {
            public Void run() {
                Thread.currentThread().setContextClassLoader(engine.getClassLoader());
                return null;
            }
        });
        cx.setApplicationClassLoader(engine.getClassLoader());
        cx.setWrapFactory(engine.getWrapFactory());
        cx.setLanguageVersion(languageVersion);
        cx.setOptimizationLevel(optimizationLevel);
        if (classShutter != null) {
            cx.setClassShutter(classShutter);
        }
        if (engine.isPolicyEnabled()) {
            cx.setInstructionObserverThreshold(instructionLimit);
            cx.setSecurityController(new PolicySecurityController());
        }
        cx.setErrorReporter(new ToolErrorReporter(true));
        cx.setGeneratingDebug(generatingDebug);
    }

    @Override
    protected void onContextReleased(Context cx) {
        super.onContextReleased(cx);
    }

    /**
     * Implementation of
     * {@link org.mozilla.javascript.Context#observeInstructionCount(int instructionCount)}.
     * This can be used to customize {@link org.mozilla.javascript.Context} without introducing
     * additional subclasses.
     */
    @Override
    protected void observeInstructionCount(Context cx, int instructionCount) {
        if (instructionCount > instructionLimit) {
            throw new Error("Maximum instruction count exceeded");
        }
    }

    public void setStrictMode(boolean flag) {
        checkNotSealed();
        this.strictMode = flag;
    }

    public void setParentProtoProperties(boolean flag) {
        checkNotSealed();
        this.parentProtoProperties = flag;
    }

    public void setWarningAsError(boolean flag) {
        checkNotSealed();
        this.warningAsError = flag;
    }

    public void setLanguageVersion(int version) {
        Context.checkLanguageVersion(version);
        checkNotSealed();
        this.languageVersion = version;
    }

    public void setOptimizationLevel(int optimizationLevel) {
        Context.checkOptimizationLevel(optimizationLevel);
        checkNotSealed();
        this.optimizationLevel = optimizationLevel;
    }

    public void setGeneratingDebug(boolean generatingDebug) {
        this.generatingDebug = generatingDebug;
    }

}
