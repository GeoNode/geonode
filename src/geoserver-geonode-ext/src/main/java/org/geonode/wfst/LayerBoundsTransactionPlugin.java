/** 
 * Copyright (c) 2001 - 2009 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, available at the root
 * application directory.
 * 
 * @author Arne Kepp / OpenGeo
 */
package org.geonode.wfst;

import java.lang.reflect.Proxy;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.xml.namespace.QName;

import net.opengis.wfs.DeleteElementType;
import net.opengis.wfs.InsertElementType;
import net.opengis.wfs.TransactionResponseType;
import net.opengis.wfs.TransactionType;
import net.opengis.wfs.UpdateElementType;

import org.geoserver.catalog.Catalog;
import org.geoserver.catalog.CatalogInfo;
import org.geoserver.catalog.FeatureTypeInfo;
import org.geoserver.catalog.LayerInfo;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.catalog.impl.ModificationProxy;
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

	static Logger log = org.geotools.util.logging.Logging.getLogger("org.geoserver.wfs");
    private Catalog catalog;

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
        log.log(Level.FINE, "DataStoreChange: " + event.getLayerName() + " " + event.getType());
        final Object source = event.getSource();
        log.info("DataStoreChange class is " + source.getClass().toString());
        TransactionEventType eventType = event.getType();
        if (!(eventType == TransactionEventType.POST_UPDATE || eventType == TransactionEventType.PRE_INSERT )) {
            log.log(Level.FINE, "Incorrect type, do nothing");
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
                log.log(Level.FINE,"Get layer");
                
                ResourceInfo resource = this.catalog.getResourceByName(featureTypeName.getLocalPart().toString(),  FeatureTypeInfo.class);
                log.log(Level.FINE,"Original bounding box:" + resource.getNativeBoundingBox());
                
                
                /* Calculate new bounds */
                log.info("Calculate bounds");
                ReferencedEnvelope nativeBounds = event.getAffectedFeatures().getBounds(); 
                ReferencedEnvelope newBounds = resource.getNativeBoundingBox();
                newBounds.expandToInclude(nativeBounds);
                log.log(Level.FINE,"New bounding box:" + newBounds);

                /* Save new bounds */
                log.log(Level.FINE,"Set resource bounds");
                resource.setNativeBoundingBox(newBounds);
                resource.setLatLonBoundingBox(newBounds.transform(CRS.decode("EPSG:4326"), true));
                log.log(Level.FINE,"DIRECT Save resource via catalog");
                //this.catalog.save(resource);  //Takes too long, save directly, may be a bad idea?
                
                
                ModificationProxy realResource = 
                    (ModificationProxy) Proxy.getInvocationHandler(resource);
                //commit to the original object
                realResource.commit();    
                log.log(Level.FINE,"Layer bounds updated");
        } catch (Exception e)
        {
        	log.log(Level.WARNING, "Exception occurred" + e);
        }
    }


}
