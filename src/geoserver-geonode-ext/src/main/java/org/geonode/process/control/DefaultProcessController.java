package org.geonode.process.control;

import static org.geonode.process.control.ProcessStatus.CANCELLED;
import static org.geonode.process.control.ProcessStatus.FAILED;
import static org.geonode.process.control.ProcessStatus.FINISHED;

import java.io.IOException;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Set;
import java.util.Map.Entry;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

import org.geonode.process.storage.StorageManager;
import org.geonode.process.storage.StorageManagerFactory;
import org.geotools.process.Process;
import org.geotools.process.ProcessExecutor;
import org.geotools.process.Progress;
import org.geotools.util.logging.Logging;

public class DefaultProcessController implements ProcessController {

    private static final Logger LOGGER = Logging.getLogger(DefaultProcessController.class);

    private static AtomicLong idSequence = new AtomicLong();

    private final Map<Long, ProcessInfo> asyncProcesses;

    private final ScheduledExecutorService evictorExecutor;

    private final ProcessExecutor processExecutor;

    private final StorageManagerFactory storageManagerFactory;

    private static class ProcessInfo {
        private final Long id;

        private final long submitionTime;

        private final AsyncProcess process;

        private final Progress progress;

        ProcessInfo(final Long id, final AsyncProcess process, final Progress progress,
                final long submitionTime) {
            this.id = id;
            this.process = process;
            this.progress = progress;
            this.submitionTime = submitionTime;
        }

        public Long getId() {
            return id;
        }

        public AsyncProcess getProcess() {
            return process;
        }

        public Progress getProgress() {
            return progress;
        }
    }

    public DefaultProcessController(final ProcessExecutor executor,
            final StorageManagerFactory storageManagerFactory, final int evictPeriodSeconds) {

        LOGGER.info("Initializing process controller...");
        this.processExecutor = executor;
        this.storageManagerFactory = storageManagerFactory;
        this.asyncProcesses = Collections.synchronizedMap(new HashMap<Long, ProcessInfo>());
        evictorExecutor = Executors.newScheduledThreadPool(1);

        Runnable command = new Runnable() {
            public void run() {
                LOGGER.info("Running process eviction...");
                synchronized (asyncProcesses) {
                    Set<Entry<Long, ProcessInfo>> entrySet = asyncProcesses.entrySet();
                    Iterator<Map.Entry<Long, ProcessInfo>> entries = entrySet.iterator();
                    while (entries.hasNext()) {
                        Entry<Long, ProcessInfo> entry = entries.next();
                        ProcessInfo processInfo = entry.getValue();
                        Progress progress = processInfo.getProgress();
                        if (progress.isDone()) {
                            LOGGER.info("Evicting process " + processInfo.getId() + ". Status: "
                                    + processInfo.getProcess().getStatus());
                            // //entries.remove();
                        }
                    }
                }
            }
        };
        evictorExecutor.scheduleWithFixedDelay(command, evictPeriodSeconds, evictPeriodSeconds,
                TimeUnit.SECONDS);
        LOGGER.info("Process controller initialized with eviction period = " + evictPeriodSeconds
                + "s");
    }

    @Override
    protected void finalize() {
        evictorExecutor.shutdownNow();
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.geonode.process.control.ProcessController#submit(org.geotools.process.Process,
     * java.util.Map)
     */
    public Progress submit(final Process process, final Map<String, Object> input) {
        Progress progress = processExecutor.submit(process, input);
        return progress;
    }

    /*
     * (non-Javadoc)
     * 
     * @seeorg.geonode.process.control.ProcessController#submitAsync(org.geonode.process.control.
     * AsyncProcess, java.util.Map)
     */
    public Long submitAsync(final AsyncProcess process, final Map<String, Object> input) {

        final Long processId = newProcessId();
        final StorageManager storageManager;
        try {
            storageManager = storageManagerFactory.newStorageManager(String.valueOf(processId));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        Map<String, Object> processInputs = new HashMap<String, Object>(input);
        processInputs.put(AsyncProcess.STORAGE_MANAGER.key, storageManager);

        Progress progress = processExecutor.submit(process, processInputs);
        long submitionTime = System.currentTimeMillis();

        ProcessInfo processInfo = new ProcessInfo(processId, process, progress, submitionTime);
        asyncProcesses.put(processId, processInfo);
        return processId;
    }

    private Long newProcessId() {
        long nextId = idSequence.incrementAndGet();
        return Long.valueOf(nextId);
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.geonode.process.control.ProcessController#getStatus(java.lang.Long)
     */
    public ProcessStatus getStatus(final Long processId) throws NoSuchElementException {
        ProcessInfo info = asyncProcesses.get(processId);
        if (info == null) {
            throw new NoSuchElementException("Process " + processId + " does not exist");
        }
        AsyncProcess process = info.getProcess();
        ProcessStatus status = process.getStatus();
        return status;
    }

    /**
     * @see org.geonode.process.control.ProcessController#getProgress(java.lang.Long)
     */
    public float getProgress(final Long processId) {
        ProcessInfo info = asyncProcesses.get(processId);
        Progress progress = info.getProgress();
        float prog = progress.getProgress();
        return prog;
    }

    /**
     * @see org.geonode.process.control.ProcessController#getResult(java.lang.Long)
     */
    public Map<String, Object> getResult(final Long processId) throws IllegalArgumentException,
            IllegalStateException {
        ProcessInfo info = asyncProcesses.get(processId);
        if (info == null) {
            throw new NoSuchElementException("Process " + processId + " does not exist");
        }
        ProcessStatus status = info.getProcess().getStatus();
        if (FINISHED != status) {
            throw new IllegalStateException("Process " + processId
                    + " is either not yet finished or has finished anormally. Current status: "
                    + status);
        }
        Map<String, Object> result;
        try {
            // status is FINISHED, so this future.get() shouln't block at all
            Progress future = info.getProgress();
            result = future.get();
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        } catch (ExecutionException e) {
            throw new RuntimeException(e);
        }
        return result;
    }

    /*
     * (non-Javadoc)
     * 
     * @see org.geonode.process.control.ProcessController#kill(java.lang.Long)
     */
    public boolean kill(final Long processId) {
        ProcessInfo info = asyncProcesses.get(processId);
        boolean cancel = false;
        if (info != null) {
            asyncProcesses.remove(processId);

            Progress progress = info.getProgress();
            final boolean mayInterruptIfRunning = true;

            cancel = progress.cancel(mayInterruptIfRunning);
        }
        return cancel;
    }

    public boolean isDone(Long processId) {
        ProcessStatus status = getStatus(processId);
        return status == CANCELLED || status == FAILED || status == FINISHED;
    }
}
