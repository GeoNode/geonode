package org.geonode.batchupload;

import java.io.File;
import java.io.FilenameFilter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

import org.apache.commons.vfs.AllFileSelector;
import org.apache.commons.vfs.FileObject;
import org.apache.commons.vfs.FileSelectInfo;
import org.apache.commons.vfs.FileSelector;
import org.apache.commons.vfs.FileSystemException;
import org.apache.commons.vfs.FileSystemManager;
import org.apache.commons.vfs.VFS;
import org.geotools.util.logging.Logging;

/**
 * Utility to work with compressed files
 * 
 * @author groldan
 */
class VFSWorker {

    private static final Logger LOGGER = Logging.getLogger(VFSWorker.class);

    private static final List<String> extensions = Arrays.asList(".zip", ".tar", ".tar.gz", ".tgz",
            ".tar.bz2", ".tbz2", ".gz", ".bz2", ".jar");

    public VFSWorker() {

    }

    public boolean canHandle(final File file) {
        final String name = file.getName().toLowerCase();
        for (String supportedExtension : extensions) {
            if (name.endsWith(supportedExtension)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 
     * @param archiveFile
     * @param filter
     * 
     * @return
     */
    public List<String> listFiles(final File archiveFile, final FilenameFilter filter) {
        FileSystemManager fsManager;
        try {
            fsManager = VFS.getManager();
            String absolutePath = resolveArchiveURI(archiveFile);
            FileObject resolvedFile = fsManager.resolveFile(absolutePath);

            FileSelector fileSelector = new FileSelector() {
                /**
                 * @see org.apache.commons.vfs.FileSelector#traverseDescendents(org.apache.commons.vfs.FileSelectInfo)
                 */
                public boolean traverseDescendents(FileSelectInfo folderInfo) throws Exception {
                    return true;
                }

                /**
                 * @see org.apache.commons.vfs.FileSelector#includeFile(org.apache.commons.vfs.FileSelectInfo)
                 */
                public boolean includeFile(FileSelectInfo fileInfo) throws Exception {
                    File folder = archiveFile.getParentFile();
                    String name = fileInfo.getFile().getName().getFriendlyURI();
                    return filter.accept(folder, name);
                }
            };

            FileObject fileSystem;
            if (fsManager.canCreateFileSystem(resolvedFile)) {
                fileSystem = fsManager.createFileSystem(resolvedFile);
            } else {
                fileSystem = resolvedFile;
            }
            LOGGER.fine("Listing spatial data files archived in " + archiveFile.getName());
            FileObject[] containedFiles = fileSystem.findFiles(fileSelector);
            List<String> names = new ArrayList<String>(containedFiles.length);
            for (FileObject fo : containedFiles) {
                // path relative to its filesystem (ie, to the archive file)
                String pathDecoded = fo.getName().getPathDecoded();
                names.add(pathDecoded);
            }
            LOGGER.fine("Found " + names.size() + " spatial data files in " + archiveFile.getName()
                    + ": " + names);
            return names;
        } catch (FileSystemException e) {
            e.printStackTrace();
        } finally {
            // fsManager.closeFileSystem(fileSystem.getFileSystem());
        }
        return Collections.emptyList();
    }

    private String resolveArchiveURI(final File archiveFile) {
        String archivePrefix = getaArchiveURLProtocol(archiveFile);
        String absolutePath = archivePrefix + archiveFile.getAbsolutePath();
        return absolutePath;
    }

    private String getaArchiveURLProtocol(final File file) {
        if (file.exists() && file.isDirectory()) {
            return "file://";
        }
        String name = file.getName().toLowerCase();
        if (name.endsWith(".zip")) {
            return "zip://";
        }
        if (name.endsWith(".tar")) {
            return "tar://";
        }
        if (name.endsWith(".tgz") || name.endsWith(".tar.gz")) {
            return "tgz://";
        }
        if (name.endsWith(".tbz2") || name.endsWith(".tar.bzip2") || name.endsWith(".tar.bz2")) {
            return "tbz2://";
        }
        if (name.endsWith(".gz")) {
            return "gz://";
        }
        if (name.endsWith(".bz2")) {
            return "bz2://";
        }
        if (name.endsWith(".jar")) {
            return "jar://";
        }
        return null;
    }

    /**
     * Extracts the archive file {@code archiveFile} to {@code targetFolder}; both shall previously
     * exist.
     */
    public void extractTo(File archiveFile, File targetFolder) {
        try {
            FileSystemManager manager = VFS.getManager();
            String sourceURI = resolveArchiveURI(archiveFile);
            String targetURI = resolveArchiveURI(targetFolder);
            FileObject source = manager.resolveFile(sourceURI);
            if (manager.canCreateFileSystem(source)) {
                source = manager.createFileSystem(source);
            }
            FileObject target = manager.createVirtualFileSystem(manager.resolveFile(targetFolder
                    .getAbsolutePath()));

            FileSelector selector = new AllFileSelector();
            target.copyFrom(source, selector);
        } catch (FileSystemException e) {
            throw new RuntimeException(e);
        }
    }
}
