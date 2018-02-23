package org.ringojs.test;

import junit.framework.TestCase;

import static org.ringojs.engine.RhinoEngine.normalizePath;

public class NormalizePathTest extends TestCase {

    public void test1() {
        String path = normalizePath("../bar/../foo/baz");
        assertEquals(path, "../foo/baz");
    }

    public void test2() {
        String path = normalizePath("./bar/.//../foo/baz");
        assertEquals(path, "foo/baz");
    }

    public void test3() {
        String path = normalizePath("bar/foo/baz");
        assertEquals(path, "bar/foo/baz");
    }

    public void test4() {
        String path = normalizePath("/bar/foo/baz/../BAZ");
        assertEquals(path, "/bar/foo/BAZ");
    }

    public void test5() {
        String path = normalizePath("bar//foo/./../baz/../../");
        assertEquals(path, "");
    }

    public void test6() {
        String path = normalizePath("bar/../foo/./../baz/../../../");
        assertEquals(path, "../..");
    }
}
