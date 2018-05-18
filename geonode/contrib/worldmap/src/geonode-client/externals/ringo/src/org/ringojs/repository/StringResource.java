/*
 *  Copyright 2009 the RingoJS Project
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

package org.ringojs.repository;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.Reader;
import java.io.StringReader;
import java.net.MalformedURLException;
import java.net.URL;

public class StringResource implements Resource {
    
    private String name;
    private int lineNumber;
    private String content;
    private long lastModified;
    
    public StringResource(String name, String content) {
        this(name, content, 1);
    }

    public StringResource(String name, String content, int lineNumber) {
        this.name = name;
        this.content = content;
        this.lineNumber = lineNumber;
        lastModified = System.currentTimeMillis();
    }
       
    public String getBaseName() {
        return name;
    }

    public long getLength() {
        return content.length();
    }

    public InputStream getInputStream() throws IOException {
        return new ByteArrayInputStream(content.getBytes());
    }

    public Reader getReader(String encoding) throws IOException {
        return getReader();
    }

    public Reader getReader() throws IOException {
        return new StringReader(content);
    }

    public String getContent(String encoding) throws IOException {
        return getContent();
    }

    public String getContent() throws IOException {
        return content;
    }

    public String getRelativePath() {
        return name;
    }

    public boolean getStripShebang() {
        return false;
    }

    public void setStripShebang(boolean stripShebang) {
        // ignore
    }

    public int getLineNumber() {
        return lineNumber;
    }

    public long lastModified() {
        return lastModified;
    }

    public long getChecksum() throws IOException {
        return lastModified() + content.hashCode();
    }

    public boolean exists() throws IOException {
        return true;
    }

    public String getPath() {
        return null;
    }

    public String getName() {
        return name;
    }

    public URL getUrl() throws UnsupportedOperationException, MalformedURLException {
        throw new UnsupportedOperationException();
    }

    public Repository getParentRepository() {
        return null;
    }

    public Repository getRootRepository() {
        return null;
    }

    public String getModuleName() {
        return name;
    }

    public void setAbsolute(boolean absolute) {
        // ignore
    }

    public boolean isAbsolute() {
        return false;
    }
}
