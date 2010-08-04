package org.geonode.process.control;

import static org.geonode.process.control.ProcessStatus.CANCELLED;
import static org.geonode.process.control.ProcessStatus.FAILED;
import static org.geonode.process.control.ProcessStatus.FINISHED;

import java.io.IOException;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.geonode.process.storage.StorageManager;
import org.geonode.process.storage.StorageManagerFactory;
import org.geotools.process.Process;
import org.geotools.process.ProcessExecutor;
import org.geotools.process.Progress;
import org.geotools.util.logging.Logging;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.scheduling.concurrent.CustomizableThreadFactory;

public class DefaultProcessController implements ProcessController, DisposableBean {

    private static final Logger LOGGER = Logging.getLogger(DefaultProcessController.class);

    private static AtomicLong idSequence = new AtomicLong();

    private final Map<Long, ProcessInfo> asyncProcesses;

    private final ScheduledExecutorService evictorExecutor;

    private final ProcessExecutor processExecutor;

    private final StorageManagerFactory storageManagerFactory;

    /**
     * 
     * @param executor
     * @param storageManagerFactory
     * @param evictCheckSeconds
     *            period in <strong>seconds<strong> for the background thread to check for evictable
     *            processes
     * @param processEvictionMinutes
     *            how many <strong>minutes</strong> to keep the processes results after they've
     *            finalized execution
     */
    public DefaultProcessController(final ProcessExecutor executor,
            final StorageManagerFactory storageManagerFactory, final int evictCheckSeconds,
            final int processEvictionMinutes) {

        LOGGER.info("Initializing process controller...");
        this.processExecutor = executor;
        this.storageManagerFactory = storageManagerFactory;
        this.asyncProcesses = Collections.synchronizedMap(new HashMap<Long, ProcessInfo>());

        CustomizableThreadFactory daemonThreadFac = new CustomizableThreadFactory(
                "Process evictor thread");
        daemonThreadFac.setDaemon(true);
        daemonThreadFac.setThreadPriority(3);
        evictorExecutor = Executors.newScheduledThreadPool(1, daemonThreadFac);

        final long evictTimeoutMillis = TimeUnit.SECONDS.toMillis(processEvictionMinutes * 60);
        Runnable evictionTask = new ProcessEvictor(asyncProcesses, evictTimeoutMillis);
        evictorExecutor.scheduleWithFixedDelay(evictionTask, evictCheckSeconds, evictCheckSeconds,
                TimeUnit.SECONDS);
        LOGGER.info("Process controller initialized with eviction period = " + evictCheckSeconds
                + "s and process eviction timeout = " + processEvictionMinutes + "m");
    }

    /**
     * @see org.springframework.beans.factory.DisposableBean#destroy()
     */
    public void destroy() throws Exception {
        LOGGER.info("Shutting down process controller....");

        evictorExecutor.shutdownNow();
        Set<Long> runningProcesses = new HashSet<Long>(asyncProcesses.keySet());
        if (runningProcesses.size() > 0) {

            for (Long processId : runningProcesses) {
                try {
                    LOGGER.info("Killing process " + processId
                            + " as the controller is shutting down");
                    kill(processId);
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Exception killing process " + processId
                            + " while shutting down process controller. Continuing...", e);
                }
            }
        }
        LOGGER.info("Process controller shut down.");
    }

    @Override
    protected void finalize() {
        try {
            destroy();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * @see org.geonode.process.control.ProcessController#submit(org.geotools.process.Process,
     *      java.util.Map)
     */
    public Progress submit(final Process process, final Map<String, Object> input) {
        Progress progress = processExecutor.submit(process, input);
        return progress;
    }

    /**
     * @see org.geonode.process.control.ProcessController#submitAsync(org.geonode.process.control.
     *      AsyncProcess, java.util.Map)
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

        ProcessInfo processInfo = new ProcessInfo(processId, process, progress);
        asyncProcesses.put(processId, processInfo);
        return processId;
    }

    private Long newProcessId() {
        long nextId = idSequence.incrementAndGet();
        return Long.valueOf(nextId);
    }

    /**
     * @see org.geonode.process.control.ProcessController#getStatus(java.lang.Long)
     */
    public ProcessStatus getStatus(final Long processId) throws IllegalArgumentException {
        ProcessInfo info = asyncProcesses.get(processId);
        if (info == null) {
            throw new IllegalArgumentException("Process " + processId + " does not exist");
        }
        AsyncProcess process = info.getProcess();
        ProcessStatus status = process.getStatus();
        return status;
    }

    /**
     * @see org.geonode.process.control.ProcessController#getReasonForFailure(java.lang.Long)
     */
    public Throwable getReasonForFailure(Long processId) throws IllegalArgumentException {
        ProcessInfo info = asyncProcesses.get(processId);
        if (info == null) {
            throw new IllegalArgumentException("Process " + processId + " does not exist");
        }
        Progress progress = info.getProgress();
        AsyncProcess process = info.getProcess();
        ProcessStatus status = process.getStatus();
        if (!isDone(status)) {
            return null;
        }

        Throwable cause = null;
        try {
            progress.get();
        } catch (InterruptedException e) {
            throw new RuntimeException("Unexpected interrupted exception! "
                    + "this souldn't happen, process already finished!");
        } catch (ExecutionException e) {
            cause = e.getCause();
        }
        return cause;
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
            throw new IllegalArgumentException("Process " + processId + " does not exist");
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

    /**
     * @see org.geonode.process.control.ProcessController#kill(java.lang.Long)
     */
    public boolean kill(final Long processId) throws IllegalArgumentException {
        ProcessInfo info = asyncProcesses.remove(processId);
        if (info == null) {
            throw new IllegalArgumentException("Process " + processId + " does not exist");
        }

        Progress progress = info.getProgress();
        final boolean mayInterruptIfRunning = true;
        final boolean cancel = progress.cancel(mayInterruptIfRunning);
        AsyncProcess process = info.getProcess();

        final ProcessStatus status = process.getStatus();
        if (status == ProcessStatus.WAITING || status == ProcessStatus.RUNNING) {
            LOGGER.warning("Process " + processId + " is " + status
                    + " after called for cancellation. Calling Process.dispose() anyways "
                    + "that may lead to unpredictable behavior");
        }
        process.dispose();

        return cancel;
    }

    /**
     * @see org.geonode.process.control.ProcessController#isDone(java.lang.Long)
     */
    public boolean isDone(Long processId) {
        ProcessStatus status = getStatus(processId);
        return isDone(status);
    }

    private boolean isDone(ProcessStatus status) {
        return status == CANCELLED || status == FAILED || status == FINISHED;
    }

    private static class ProcessInfo {
        private final Long id;

        private long finalizationTime;

        private final AsyncProcess process;

        private final Progress progress;

        ProcessInfo(final Long id, final AsyncProcess process, final Progress progress) {
            this.id = id;
            this.process = process;
            this.progress = progress;
            this.finalizationTime = -1;
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

        public long getFinalizationTime() {
            return finalizationTime;
        }

        public void setFinalizationTime(long finalizationTime) {
            this.finalizationTime = finalizationTime;
        }
    }

    /**
     * Background task that checks the processes and disposes them and any resource they might be
     * holding when at least a specified period of time has been elapsed since the process
     * terminated its execution.
     * 
     */
    private static final class ProcessEvictor implements Runnable {

        private final Map<Long, ProcessInfo> asyncProcesses;

        private final long evictTimeoutMillis;

        public ProcessEvictor(final Map<Long, ProcessInfo> asyncProcesses,
                final long evictTimeoutMillis) {
            this.asyncProcesses = asyncProcesses;
            this.evictTimeoutMillis = evictTimeoutMillis;
        }

        public void run() {
            LOGGER.finer("Running process eviction...");

            List<ProcessInfo> evictable = findEvictableProcesses();
            if (evictable.size() == 0) {
                return;
            }
            for (ProcessInfo processInfo : evictable) {
                dispose(processInfo);
            }
        }

        private void dispose(final ProcessInfo processInfo) {
            AsyncProcess process = processInfo.getProcess();
            if (process != null) {
                LOGGER.fine("Disposing results of process #" + processInfo.getId());
                process.dispose();
            }
        }

        private List<ProcessInfo> findEvictableProcesses() {

            List<ProcessInfo> evictable = new LinkedList<ProcessInfo>();

            synchronized (asyncProcesses) {
                final long currentTime = System.currentTimeMillis();

                Set<Entry<Long, ProcessInfo>> entrySet = asyncProcesses.entrySet();
                Iterator<Map.Entry<Long, ProcessInfo>> entries;
                Entry<Long, ProcessInfo> entry;

                for (entries = entrySet.iterator(); entries.hasNext();) {
                    entry = entries.next();
                    ProcessInfo processInfo = entry.getValue();
                    Progress progress = processInfo.getProgress();
                    if (progress.isDone()) {
                        final long finalizationTime = processInfo.getFinalizationTime();
                        if (-1L == finalizationTime) {
                            // mark is as just finalized and wait for another run the check
                            // whether to actually evict it
                            processInfo.setFinalizationTime(currentTime);
                        } else {
                            long deadPeriod = currentTime - finalizationTime;
                            if (evictTimeoutMillis <= deadPeriod) {
                                LOGGER.fine("Evicting process " + processInfo.getId()
                                        + ". Status: " + processInfo.getProcess().getStatus());
                                entries.remove();
                                evictable.add(processInfo);
                            }
                        }
                    }
                }
            }

            return evictable;
        }
    }

}
