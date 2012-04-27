/**
 * Copyright (c) 2001 - 2009 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, available at the root
 * application directory.
 *
 * @author Arne Kepp / OpenGeo
 */
package org.geonode.wfst;

import java.util.logging.Level;
import java.util.logging.Logger;
import javax.xml.namespace.QName;

import net.opengis.wfs.DeleteElementType;
import net.opengis.wfs.InsertElementType;
import net.opengis.wfs.TransactionResponseType;
import net.opengis.wfs.TransactionType;
import net.opengis.wfs.UpdateElementType;

import org.geoserver.catalog.Catalog;
import org.geoserver.catalog.LayerInfo;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.wfs.TransactionEvent;
import org.geoserver.wfs.TransactionEventType;
import org.geoserver.wfs.TransactionPlugin;
import org.geoserver.wfs.WFSException;
import org.geotools.geometry.jts.ReferencedEnvelope;
import org.geotools.referencing.CRS;
import org.geotools.util.logging.Logging;


/**
 * Listens to transactions (so far only issued by WFS) and updates bounds for layers involved in the transaction.
 * <p>
 * A Spring bean singleton of this class needs to be declared in order for GeoServer transactions to
 * pick it up automatically and forward transaction events to it.
 *
 */
public class LayerBoundsTransactionPlugin implements TransactionPlugin {

    private static Logger log = Logging.getLogger(LayerBoundsTransactionPlugin.class);
    private final Catalog catalog;

    public LayerBoundsTransactionPlugin(final Catalog catalog) {
    	this.catalog = catalog;
    	log.info("LayerBoundsTransactionPlugin bean instantiated");
    }

    /* Give this higher priority than WCS*/
    public int getPriority()
    {
    	return 1;
    }

    /**
     * Not used, we're interested in the {@link #dataStoreChange} hook only
     *
     * @see org.geoserver.wfs.TransactionPlugin#beforeTransaction(net.opengis.wfs.TransactionType)
     */
    public TransactionType beforeTransaction(TransactionType request) throws WFSException {
        // nothing to do
        return request;
    }

    /**
     * Not used, we're interested in the {@link #dataStoreChange} hook only
     *
     * @see org.geoserver.wfs.TransactionPlugin#beforeCommit(net.opengis.wfs.TransactionType)
     */
    public void beforeCommit(TransactionType request) throws WFSException {
        // nothing to do
    }

    /**
     * Not used, we're interested in the {@link #dataStoreChange} hook only
     *
     * @see org.geoserver.wfs.TransactionPlugin#afterTransaction
     */
    public void afterTransaction(final TransactionType request, TransactionResponseType result,
            boolean committed) {
    	// nothing to do
    }




    /**
     * Update layer bounds if transaction source type = UPDATE or INSERT or DELETE
     *
     * @see org.geoserver.wfs.TransactionListener#dataStoreChange(org.geoserver.wfs.TransactionEvent)
     */
    public void dataStoreChange(final TransactionEvent event) throws WFSException {
        log.info("DataStoreChange: " + event.getLayerName() + " " + event.getType());
        final Object source = event.getSource();
        log.info("DataStoreChange class is " + source.getClass().toString());
        TransactionEventType eventType = event.getType();
        if (!(eventType == TransactionEventType.POST_UPDATE || eventType == TransactionEventType.PRE_INSERT )) {
            log.info("Incorrect type, do nothing");
        	return;
        }
        try {
            dataStoreChangeInternal(event);
        } catch (RuntimeException e) {
            // Never make the transaction fail due to an error. Yell on the logs though
            log.log(Level.WARNING, "Error pre computing the transaction's affected area", e);
        }
    }


    /**
     * Update layer bounds
     *
     * @see org.geoserver.wfs.TransactionListener#dataStoreChange(org.geoserver.wfs.TransactionEvent)
     */
    private void dataStoreChangeInternal(final TransactionEvent event) {
        final QName featureTypeName = event.getLayerName();
        try {
                /* Get layer resource */
                LayerInfo layer = this.catalog.getLayerByName(featureTypeName.getLocalPart().toString());
                ResourceInfo resource = layer.getResource();
                log.info("Original bounding box:" + resource.getNativeBoundingBox());


                /* Calculate new bounds */
                ReferencedEnvelope nativeBounds = event.getAffectedFeatures().getBounds();
                ReferencedEnvelope newBounds = resource.getNativeBoundingBox();
                newBounds.expandToInclude(nativeBounds);
                log.info("New bounding box:" + newBounds);

                /* Save new bounds */
                resource.setNativeBoundingBox(newBounds);
                resource.setLatLonBoundingBox(newBounds.transform(CRS.decode("EPSG:4326"), true));
                this.catalog.save(resource);
                log.info("Layer bounds updated");
        } catch (Exception e)
        {
        	log.log(Level.WARNING, "Exception occurred" + e);
        }
    }


}
