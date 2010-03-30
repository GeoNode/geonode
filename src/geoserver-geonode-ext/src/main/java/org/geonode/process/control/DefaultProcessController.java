package org.geonode.process.control;

import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Set;
import java.util.Map.Entry;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;

import org.geotools.process.Process;
import org.geotools.process.ProcessExecutor;
import org.geotools.process.Progress;
import org.geotools.util.logging.Logging;

public class DefaultProcessController {

    private static final Logger LOGGER = Logging.getLogger(DefaultProcessController.class);

    private static AtomicLong idSequence = new AtomicLong();

    private ProcessExecutor processExecutor;

    private final Map<Long, ProcessInfo> asyncProcesses;

    private ScheduledExecutorService evictorExecutor;

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

    public DefaultProcessController(final ProcessExecutor executor, final int evictPeriodSeconds) {
        LOGGER.info("Initializing process controller...");
        this.processExecutor = executor;
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
                            entries.remove();
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

    public Progress submit(final Process process, final Map<String, Object> input) {
        Progress progress = processExecutor.submit(process, input);
        return progress;
    }

    public Long submitAsync(final AsyncProcess process, final Map<String, Object> input) {
        Progress progress = processExecutor.submit(process, input);
        long submitionTime = System.currentTimeMillis();
        Long processId = newProcessId();
        ProcessInfo processInfo = new ProcessInfo(processId, process, progress, submitionTime);
        asyncProcesses.put(processId, processInfo);
        return processId;
    }

    private Long newProcessId() {
        long nextId = idSequence.incrementAndGet();
        return Long.valueOf(nextId);
    }

    public ProcessStatus getStatus(final Long processId) throws NoSuchElementException {
        ProcessInfo info = asyncProcesses.get(processId);
        AsyncProcess process = info.getProcess();
        ProcessStatus status = process.getStatus();
        return status;
    }

    public float getProgress(final Long processId) {
        ProcessInfo info = asyncProcesses.get(processId);
        Progress progress = info.getProgress();
        float prog = progress.getProgress();
        return prog;
    }

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
}
