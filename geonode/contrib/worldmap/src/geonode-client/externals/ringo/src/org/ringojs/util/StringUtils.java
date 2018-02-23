/*
 * Helma License Notice
 *
 * The contents of this file are subject to the Helma License
 * Version 2.0 (the "License"). You may not use this file except in
 * compliance with the License. A copy of the License is available at
 * http://adele.invoker.org/download/invoker/license.txt
 *
 * Copyright 2005 Hannes Wallnoefer. All Rights Reserved.
 */

package org.ringojs.util;


import java.nio.CharBuffer;
import java.util.StringTokenizer;

/**
 * Utility class for String manipulation.
 */
public class StringUtils {


    /**
     *  Split a string into an array of strings. Use comma and space
     *  as delimiters.
     * @param str the string to split
     * @return the string split into a string array
     */
    public static String[] split(String str) {
        return split(str, ", \t\n\r\f");
    }

    /**
     *  Split a string into an array of strings.
     * @param str the string to split
     * @param delim the delimiter to split the string at
     * @return the string split into a string array
     */
    public static String[] split(String str, String delim) {
        if (str == null) {
            return new String[0];
        }
        StringTokenizer st = new StringTokenizer(str, delim);
        String[] s = new String[st.countTokens()];
        for (int i=0; i<s.length; i++) {
            s[i] = st.nextToken();
        }
        return s;
    }

    /**
     * Break a string into a string array, using line breaks as delimiters.
     * This supports Unix, Mac and Windows style line breaks.
     * @param str the string to split
     * @return the string split at line breaks
     */
    public static String[] splitLines(String str) {
        if (str == null) {
            return new String[0];
        }
        return str.split("\\r\\n|\\r|\\n");
    }

    public static String join(String[] strings, String separator) {
        StringBuffer buffer = new StringBuffer();
        int length = strings.length;
        for (int i = 0; i < length; i++) {
            buffer.append(strings[i]);
            if (i < length - 1)
                buffer.append(separator);
        }
        return buffer.toString();
    }

    /**
     * Escape the string to make it safe for use within an HTML document.
     * @param str the string to escape
     * @return  the escaped string
     */
    public static String escapeHtml(String str) {
        return str.replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll("\"", "&quot;");
    }

    /**
     * Split a string and try to convert to an array of classes.
     * @param str a string containint class names
     * @param delim the delimiter
     * @return an array of classes
     * @throws ClassNotFoundException if any class name contained in the string
     *         couldn't be resolved
     */
    public static Class[] toClassArray(String str, String delim)
            throws ClassNotFoundException {
        String[] s = split(str, delim);
        Class[] classes = new Class[s.length];
        for (int i=0; i<s.length; i++) {
            classes[i] = Class.forName(s[i]);
        }
        return classes;
    }

    /**
     * Check whether the argument has a .zip or .jar file extension
     * @param str a file name
     * @return true if str ends with .zip or .jar
     */
    public static boolean isZipOrJarFile(String str) {
        if (str == null) {
            throw new NullPointerException("str must not be null");
        }
        String lower = str.toLowerCase();
        return lower.endsWith(".zip") || lower.endsWith(".jar");
    }

    /**
     * Scan for a newline sequence in the given CharBuffer, starting at
     * position from until buffer.position(). A newline sequence is one of
     * "r\n", "\r", or "\n". Returns the index of the
     * first newline sequence, or -1 if none was found.
     *
     * @param buffer the character buffer
     * @param from the position to start searching
     * @return the index of first newline sequence found, or -1
     */
    public static int searchNewline(CharBuffer buffer, int from) {
        int to = buffer.position();
        if (from >= to) {
            return -1;
        }
        char[] chars = buffer.array();
        for (int i = from; i < to; i++) {
            if (chars[i] == '\n' || (chars[i] == '\r' && i < to - 1)) {
                return i;
            }
        }
        return -1;
    }

}
