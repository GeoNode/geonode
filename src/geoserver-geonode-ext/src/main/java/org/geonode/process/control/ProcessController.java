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

    boolean kill(final Long processId);

    boolean isDone(Long processId);

}