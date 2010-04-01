package org.geonode.process.control;

import java.util.Map;
import java.util.NoSuchElementException;

import org.geotools.process.Process;
import org.geotools.process.Progress;

public interface ProcessController {

    Progress submit(final Process process, final Map<String, Object> input);

    Long submitAsync(final AsyncProcess process, final Map<String, Object> input);

    ProcessStatus getStatus(final Long processId) throws NoSuchElementException;

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

    boolean kill(final Long processId);

    boolean isDone(Long processId);

}