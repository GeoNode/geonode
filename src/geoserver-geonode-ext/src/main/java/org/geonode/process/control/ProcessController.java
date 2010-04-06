package org.geonode.process.control;

import java.util.Map;

import org.geotools.process.Process;
import org.geotools.process.Progress;

public interface ProcessController {

    Progress submit(final Process process, final Map<String, Object> input);

    Long submitAsync(final AsyncProcess process, final Map<String, Object> input);

    /**
     * 
     * @param processId
     * @return
     * @throws IllegalArgumentException
     *             if process does not exist
     */
    ProcessStatus getStatus(final Long processId) throws IllegalArgumentException;

    float getProgress(final Long processId);

    /**
     * Returns the result of a {@link ProcessStatus#FINISHED FINISHED} process
     * 
     * @param processId
     * @return
     * @throws IllegalArgumentException
     *             if process {@code processId} does not exist
     * @throws IllegalStateException
     *             if process has not finished normally or is still running
     */
    Map<String, Object> getResult(final Long processId) throws IllegalArgumentException,
            IllegalStateException;

    /**
     * Cancels a process if running, and disposes it if it exists not matter its state.
     * 
     * @param processId
     * @return {@code true} if process was running and successfully killed, {@code false} if process
     *         was already terminated
     * @throws IllegalArgumentException
     *             if process does not exist
     */
    boolean kill(final Long processId) throws IllegalArgumentException;

    /**
     * 
     * @param processId
     * @return {@code true} if process is no longer running, no matter the reason (success, failure,
     *         cancellation), {@code false} if process is waiting for execution or running
     * @throws IllegalArgumentException
     *             if process does not exist
     */
    boolean isDone(Long processId) throws IllegalArgumentException;

    /**
     * 
     * @param processId
     * @return
     * @throws IllegalArgumentException
     */
    Throwable getReasonForFailure(Long processId) throws IllegalArgumentException;

}