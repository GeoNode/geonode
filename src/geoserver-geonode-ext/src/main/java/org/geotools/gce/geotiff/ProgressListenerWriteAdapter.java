package org.geotools.gce.geotiff;

import java.util.logging.Logger;

import javax.imageio.ImageWriter;
import javax.imageio.event.IIOWriteProgressListener;

import org.geotools.util.logging.Logging;
import org.opengis.util.ProgressListener;

public class ProgressListenerWriteAdapter implements IIOWriteProgressListener {

    private static final Logger LOGGER = Logging.getLogger(ProgressListenerWriteAdapter.class);

    private final ProgressListener monitor;

    /**
     * Indicates whether the {@link #writeAborted(ImageWriter)} method was called externally, or as
     * a consecuence of checking on {@link ProgressListener#isCanceled() monitor.isCAnceled()} and
     * hence we need to call {@link ImageWriter#abort()}
     */
    private boolean selfAbort;

    public ProgressListenerWriteAdapter(final ProgressListener monitor) {
        this.monitor = monitor;
    }

    private boolean checkCancelled(ImageWriter writer) {
        if (monitor.isCanceled()) {
            selfAbort = true;
            writer.abort();
            return true;
        }
        return false;
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageStarted(javax.imageio.ImageWriter,
     *      int)
     */
    public void imageStarted(ImageWriter source, int imageIndex) {
        LOGGER.finest("image started");
        monitor.started();
        checkCancelled(source);
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageComplete(javax.imageio.ImageWriter)
     */
    public void imageComplete(ImageWriter source) {
        if (!checkCancelled(source)) {
            LOGGER.finest("image complete");
            monitor.complete();
        }
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#writeAborted(javax.imageio.ImageWriter)
     */
    public void writeAborted(ImageWriter source) {
        LOGGER.finest("image aborted");
        if (!selfAbort) {
            monitor.setCanceled(true);
        }
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageProgress(javax.imageio.ImageWriter,
     *      float)
     */
    public void imageProgress(ImageWriter source, float percentageDone) {
        if (!checkCancelled(source)) {
            LOGGER.finest("image progrss: " + percentageDone);
            monitor.progress(percentageDone);
        }
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#thumbnailComplete(javax.imageio.ImageWriter)
     */
    public void thumbnailComplete(ImageWriter source) {
        // TODO Auto-generated method stub

    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#thumbnailProgress(javax.imageio.ImageWriter,
     *      float)
     */
    public void thumbnailProgress(ImageWriter source, float percentageDone) {
        // TODO Auto-generated method stub

    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#thumbnailStarted(javax.imageio.ImageWriter,
     *      int, int)
     */
    public void thumbnailStarted(ImageWriter source, int imageIndex, int thumbnailIndex) {
        // TODO Auto-generated method stub

    }

}
