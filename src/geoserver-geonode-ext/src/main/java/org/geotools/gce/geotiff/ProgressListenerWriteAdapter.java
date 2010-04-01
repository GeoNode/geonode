package org.geotools.gce.geotiff;

import javax.imageio.ImageWriter;
import javax.imageio.event.IIOWriteProgressListener;

import org.opengis.util.ProgressListener;

public class ProgressListenerWriteAdapter implements IIOWriteProgressListener {

    private final ProgressListener monitor;

    public ProgressListenerWriteAdapter(final ProgressListener monitor) {
        this.monitor = monitor;
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageStarted(javax.imageio.ImageWriter,
     *      int)
     */
    public void imageStarted(ImageWriter source, int imageIndex) {
        System.err.println("image started");
        monitor.started();
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageComplete(javax.imageio.ImageWriter)
     */
    public void imageComplete(ImageWriter source) {
        System.err.println("image complete");
        monitor.complete();
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#writeAborted(javax.imageio.ImageWriter)
     */
    public void writeAborted(ImageWriter source) {
        System.err.println("image aborted");
        monitor.setCanceled(true);
    }

    /**
     * @see javax.imageio.event.IIOWriteProgressListener#imageProgress(javax.imageio.ImageWriter,
     *      float)
     */
    public void imageProgress(ImageWriter source, float percentageDone) {
        System.err.println("image progrss: " + percentageDone);
        monitor.progress(percentageDone);
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
