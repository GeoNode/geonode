package org.geonode.process.control;

import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.geonode.process.storage.Folder;
import org.geonode.process.storage.Resource;
import org.geonode.process.storage.StorageManager;
import org.geotools.data.Parameter;
import org.geotools.process.Process;
import org.geotools.process.ProcessException;
import org.geotools.text.Text;
import org.geotools.util.NullProgressListener;
import org.geotools.util.logging.Logging;
import org.opengis.util.ProgressListener;

public abstract class AsyncProcess implements Process {

    private static final Logger LOGGER = Logging.getLogger(AsyncProcess.class);

    /**
     * By lack of a better way to pass context/collaborator objects to a process, we use this
     * special input parameter.
     */
    public static final Parameter<StorageManager> STORAGE_MANAGER = new Parameter<StorageManager>(
            "StorageManager", StorageManager.class, Text.text("Storage Manager"),
            Text.text("Storage Manager"));

    private ProcessStatus status;

    private StorageManager storageManager;

    public AsyncProcess() {
        status = ProcessStatus.WAITING;
    }

    /**
     * Controls the status of the process and defers execution to
     * {@link #executeInternal(Map, ProgressListener)} so that subclasses do not need to worry about
     * setting the process {@link #getStatus() status}, but only about running the process logic and
     * updating the monitor's {@link ProgressListener#progress(float) progress}.
     * <p>
     * Before this method is called, the status of the process is {@link ProcessStatus#WAITING
     * WAITING}, right after this method is entered, the status changes to
     * {@link ProcessStatus#RUNNING RUNNING}. If an exception occurs, status is set to
     * {@link ProcessStatus#FAILED FAILED}. If the process returns normally but the
     * {@link ProgressListener#isCanceled() progress listener is cancelled}, the status is set to
     * {@link ProcessStatus#CANCELLED CANCELLED}. Otherwise the final status is
     * {@link ProcessStatus#FINISHED FINISHED}.
     * </p>
     */
    public final Map<String, Object> execute(final Map<String, Object> input,
            ProgressListener monitor) throws ProcessException {

        if (monitor == null) {
            monitor = new NullProgressListener();
        }
        status = ProcessStatus.RUNNING;
        storageManager = (StorageManager) input.get(STORAGE_MANAGER.key);
        try {
            Map<String, Object> result = executeInternal(input, monitor);
            if (monitor.isCanceled()) {
                status = ProcessStatus.CANCELLED;
                dispose();
            } else {
                status = ProcessStatus.FINISHED;
                monitor.complete();
            }
            return result;
        } catch (ProcessException e) {
            status = ProcessStatus.FAILED;
            monitor.exceptionOccurred(e);
            dispose();
            throw e;
        } catch (RuntimeException e) {
            status = ProcessStatus.FAILED;
            monitor.exceptionOccurred(e);
            dispose();
            throw e;
        } catch (Error e) {
            // This is really fatal. Though commonly it's bad practice to catch up Errors, not doing
            // so might lead to processes marked running indefinitely
            status = ProcessStatus.FAILED;
            monitor.exceptionOccurred(e);
            dispose();
            throw e;
        }
    }

    protected abstract Map<String, Object> executeInternal(Map<String, Object> input,
            ProgressListener monitor) throws ProcessException;

    public final ProcessStatus getStatus() {
        return status;
    }

    protected StorageManager getStorageManager() {
        return storageManager;
    }

    /**
     * To be called when the process nor its results are no longer needed, including any
     * {@link Resource} or {@link Folder} used either for temporary storage or to hold the process'
     * result.
     */
    public final void dispose() {
        try {
            disposeInternal();
        } catch (RuntimeException e) {
            LOGGER.log(Level.WARNING, "Process failed to dispose all its held resources", e);
        }
        StorageManager storageManager = getStorageManager();
        if (storageManager != null) {
            storageManager.dispose();
        }
    }

    /**
     * Subclasses should override if they need to dispose any other resource than the ones disposed
     * at {@link #dispose()}
     */
    protected void disposeInternal() {
        // nothing to do, override as needed
    }
}
