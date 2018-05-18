package org.ringojs.tools;

import org.ringojs.engine.RingoConfiguration;
import org.ringojs.util.StringUtils;
import org.mozilla.javascript.tools.debugger.Dim;
import org.mozilla.javascript.tools.debugger.SwingGui;
import org.mozilla.javascript.debug.DebuggableScript;

import javax.swing.event.TreeSelectionListener;
import javax.swing.event.TreeSelectionEvent;
import javax.swing.*;
import javax.swing.tree.*;
import java.util.HashMap;
import java.util.Enumeration;
import java.util.Vector;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;

/*
* Helma License Notice
*
* The contents of this file are subject to the Helma License
* Version 2.0 (the "License"). You may not use this file except in
* compliance with the License. A copy of the License is available at
* http://adele.helma.org/download/ringo/license.txt
*
* Copyright 1998-2003 Helma Software. All Rights Reserved.
*
* $RCSfile$
* $Author: hannes $
* $Revision: 8820 $
* $Date: 2008-04-07 14:25:02 +0200 (Mon, 07 Apr 2008) $
*/


public class RingoDebugger extends Dim implements TreeSelectionListener {

    RingoConfiguration config;
    DebugGui gui;
    JTree tree;
    JList list;
    DebuggerTreeNode treeRoot;
    DefaultTreeModel treeModel;
    HashMap treeNodes = new HashMap();
    HashMap scriptNames = new HashMap();


    public RingoDebugger(RingoConfiguration config) {
        this.config = config;
        gui = new DebugGui(this, "RingoJS Debugger");
        gui.pack();
        gui.setVisible(true);
    }

    @SuppressWarnings("unchecked")
    void createTreeNode(String sourceName, Dim.SourceInfo sourceInfo) {
        // String[] path = StringUtils.split(sourceInfo.sourceName(), ":/\\");
        String[] path = StringUtils.split(sourceName, ":/\\");
        DebuggerTreeNode node = treeRoot;
        DebuggerTreeNode newNode = null;
        for (int i = 0; i < path.length; i++) {
            DebuggerTreeNode n = node.get(path[i]);
            if (n == null) {
                n = new DebuggerTreeNode(path[i]);
                node.add(n);
                if (newNode == null) newNode = n;
            }
            node = n;
        }
        treeNodes.put(sourceName, node);
        scriptNames.put(node, sourceName);
        if (newNode != null) {
            SwingUtilities.invokeLater(new NodeInserter(newNode));
        }
    }

    void openScript(TreePath path) {
        if (path == null)
            return;
        Object node = path.getLastPathComponent();
        if (node == null)
            return;
        String sourceName = (String) scriptNames.get(node);
        if (sourceName == null)
            return;
        gui.showFileWindow(sourceName, -1);
    }

    void openFunction(FunctionItem function) {
        if (function == null)
            return;
        FunctionSource src = function.src;
        if (src != null) {
            SourceInfo si = src.sourceInfo();
            String url = si.url();
            int lineNumber = src.firstLine();
            gui.showFileWindow(url, lineNumber);
        }
    }

    // @Override
    protected String getNormalizedUrl(DebuggableScript fnOrScript) {
        String source = fnOrScript.getSourceName();
        try {
            return config.getResource(source).getUrl().toString();
        } catch (Exception x) {
            return source;
        }
    }

    public void valueChanged(TreeSelectionEvent e) {
        DefaultMutableTreeNode node = (DefaultMutableTreeNode)
                tree.getLastSelectedPathComponent();

        if (node == null) return;

        Object script = scriptNames.get(node);
        if (script != null) {
            // openScript(script);
        }
    }

    public void setVisible(boolean visible) {
        gui.setVisible(visible);
    }

    public void dispose() {
        super.dispose();
        gui.setVisible(false);
        // Calling dispose() on the gui causes shutdown hook to hang on windows -
        // see http://helma.org/bugs/show_bug.cgi?id=586#c2
        // gui.dispose();
    }

    class DebuggerTreeNode extends DefaultMutableTreeNode {

        public DebuggerTreeNode(Object obj) {
            super(obj);
        }

        public DebuggerTreeNode get(String name) {
            Enumeration children = this.children();
            while (children.hasMoreElements()) {
                DebuggerTreeNode node = (DebuggerTreeNode) children.nextElement();
                if (node != null && name.equals(node.getUserObject()))
                    return node;
            }
            return null;
        }
    }

    class NodeInserter implements Runnable {
        MutableTreeNode node;

        NodeInserter(MutableTreeNode node) {
            this.node = node;
        }

        public void run() {
            MutableTreeNode parent = (MutableTreeNode) node.getParent();
            if (parent == treeRoot && treeRoot.getChildCount() == 1) {
                tree.makeVisible(new TreePath(new Object[]{parent, node}));
            }
            treeModel.insertNodeInto(node, parent, parent.getIndex(node));
        }
    }

    class DebugGui extends SwingGui {

        String currentSourceUrl;

        public DebugGui(Dim dim, String title) {
            super(dim, title);
            Container contentPane = getContentPane();
            Component main = contentPane.getComponent(1);
            contentPane.remove(main);

            treeRoot = new DebuggerTreeNode(title);
            tree = new JTree(treeRoot);
            treeModel = new DefaultTreeModel(treeRoot);
            tree.setModel(treeModel);
            tree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION);
            tree.addTreeSelectionListener(RingoDebugger.this);
            // tree.setRootVisible(false);
            // track double clicks
            tree.addMouseListener(new MouseAdapter() {
                public void mouseClicked(MouseEvent evt) {
                    openScript(tree.getSelectionPath());
                }
            });
            // track enter key
            tree.addKeyListener(new KeyAdapter() {
                public void keyPressed(KeyEvent evt) {
                    if (evt.getKeyCode() == KeyEvent.VK_ENTER)
                        openScript(tree.getSelectionPath());
                }
            });
            JScrollPane treeScroller = new JScrollPane(tree);
            treeScroller.setPreferredSize(new Dimension(180, 300));

            list = new JList();
            // no bold font lists for me, thanks
            list.setFont(list.getFont().deriveFont(Font.PLAIN));
            list.addMouseListener(new MouseAdapter() {
                public void mouseClicked(MouseEvent evt) {
                    openFunction((FunctionItem) list.getSelectedValue());
                }
            });
            list.addKeyListener(new KeyAdapter() {
                public void keyPressed(KeyEvent evt) {
                    if (evt.getKeyCode() == KeyEvent.VK_ENTER)
                        openFunction((FunctionItem) list.getSelectedValue());
                }
            });
            JScrollPane listScroller = new JScrollPane(list);
            listScroller.setPreferredSize(new Dimension(180, 200));

            JSplitPane split1 = new JSplitPane(JSplitPane.VERTICAL_SPLIT);
            split1.setTopComponent(treeScroller);
            split1.setBottomComponent(listScroller);
            split1.setOneTouchExpandable(true);
            split1.setResizeWeight(0.66);

            JSplitPane split2 = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
            split2.setLeftComponent(split1);
            split2.setRightComponent(main);
            split2.setOneTouchExpandable(true);
            contentPane.add(split2, BorderLayout.CENTER);
        }

        public void updateSourceText(final Dim.SourceInfo sourceInfo) {
            // super.updateSourceText(sourceInfo);
            String filename = sourceInfo.url();
            if (!treeNodes.containsKey(filename)) {
                createTreeNode(filename, sourceInfo);
            }
            SwingUtilities.invokeLater(new Runnable() {
                public void run() {
                    updateFileWindow(sourceInfo);
                }
            });
        }

        protected void showFileWindow(String sourceName, int lineNumber) {
            if (!isVisible())
                setVisible(true);
            if (!sourceName.equals(currentSourceUrl)) {
                updateFunctionList(sourceName);
                DebuggerTreeNode node = (DebuggerTreeNode) treeNodes.get(sourceName);
                if (node != null) {
                    TreePath path = new TreePath(node.getPath());
                    tree.setSelectionPath(path);
                    tree.scrollPathToVisible(path);
                }
            }
            super.showFileWindow(sourceName, lineNumber);
        }

        @SuppressWarnings("unchecked")
        private void updateFunctionList(String sourceName) {
            // display functions for opened script file
            currentSourceUrl = sourceName;
            Vector functions = new Vector();
            SourceInfo si = sourceInfo(sourceName);
            String[] lines = si.source().split("\\r\\n|\\r|\\n");
            int length = si.functionSourcesTop();
            for (int i = 0; i < length; i++) {
                FunctionSource src = si.functionSource(i);
                if (sourceName.equals(src.sourceInfo().url())) {
                    functions.add(new FunctionItem(src, lines));
                }
            }
            // Collections.sort(functions);
            list.setListData(functions);
        }
    }

    class FunctionItem implements Comparable {

        FunctionSource src;
        String name;
        String line = "";

        FunctionItem(FunctionSource src, String[] lines) {
            this.src = src;
            name = src.name();
            if ("".equals(name)) {
                try {
                    line = lines[src.firstLine() - 1];
                    int f = line.indexOf("function") - 1;
                    StringBuffer b = new StringBuffer();
                    boolean assignment = false;
                    while (f-- > 0) {
                        char c = line.charAt(f);
                        if (c == ':' || c == '=')
                            assignment = true;
                        else if (assignment && Character.isJavaIdentifierPart(c)
                                || c == '$' || c == '.')
                            b.append(c);
                        else if (!Character.isWhitespace(c) || b.length() > 0)
                            break;
                    }
                    name = b.length() > 0 ? b.reverse().toString() : "<anonymous>";
                } catch (Exception x) {
                    // fall back to default name
                    name = "<anonymous>";
                }
            }
        }

        public int compareTo(Object o) {
            FunctionItem other = (FunctionItem) o;
            return name.compareTo(other.name);
        }

        public String toString() {
            return name;
        }

    }
}

