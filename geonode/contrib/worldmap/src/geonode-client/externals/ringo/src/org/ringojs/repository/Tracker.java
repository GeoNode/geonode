/*
 * Helma License Notice
 *
 * The contents of this file are subject to the Helma License
 * Version 2.0 (the "License"). You may not use this file except in
 * compliance with the License. A copy of the License is available at
 * http://adele.helma.org/download/helma/license.txt
 *
 * Copyright 1998-2003 Helma Software. All Rights Reserved.
 *
 * $RCSfile: ResourceTracker.java,v $
 * $Author: hannes $
 * $Revision: 1.2 $
 * $Date: 2005/03/10 16:54:03 $
 */

package org.ringojs.repository;

import java.io.IOException;

/**
 * A utility class that allows Resource consumers to track changes
 * on resources.
 */
public class Tracker {

    Trackable source;
    long lastModified;

    public Tracker(Trackable source) throws IOException {
        this.source = source;
        markClean();
    }

    public boolean hasChanged() throws IOException {
        return lastModified != source.lastModified();
    }

    public void markClean() throws IOException {
        lastModified = source.lastModified();
    }

    public Trackable getSource() {
        return source;
    }
}
