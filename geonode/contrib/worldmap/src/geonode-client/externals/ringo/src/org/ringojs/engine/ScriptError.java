package org.ringojs.engine;

import org.ringojs.util.StringUtils;

public class ScriptError {

    public final String message, sourceName, lineSource;
    public final int lineNumber, offset;

    ScriptError(String message, String sourceName, int lineNumber,
                String lineSource, int offset) {
        this.message = message;
        this.sourceName = sourceName == null ? "[unknown source]" : sourceName;
        this.lineSource = lineSource;
        this.lineNumber = lineNumber;
        this.offset = offset;
    }

    public String toString() {
        String lineSeparator = System.getProperty("line.separator", "\n");
        StringBuilder b = new StringBuilder(sourceName).append(", line ")
                .append(lineNumber).append(": ").append(message)
                .append(lineSeparator).append(lineSource).append(lineSeparator);
        for(int i = 0; i < offset - 1; i++) {
            b.append(' ');
        }
        b.append('^');
        return b.toString();
    }

    public String toHtml() {
        String lineSeparator = System.getProperty("line.separator", "\n");
        StringBuilder b = new StringBuilder("<p>").append(sourceName)
                .append(", line ").append(lineNumber).append(": <b>")
                .append(StringUtils.escapeHtml(message)).append("</b></p>")
                .append(lineSeparator).append("<pre>");
        int srcLength = lineSource.length();
        int errorStart = Math.max(0, offset - 2);
        int errorEnd = Math.min(srcLength, offset);
        b.append(StringUtils.escapeHtml(lineSource.substring(0, errorStart)))
                .append("<span style='border-bottom: 3px solid red;'>")
                .append(StringUtils.escapeHtml(lineSource.substring(errorStart, errorEnd)))
                .append("</span>")
                .append(StringUtils.escapeHtml(lineSource.substring(errorEnd)))
                .append(lineSeparator).append("</pre>");
        return b.toString();
    }

}
