/** 
 * Copyright (c) 2001 - 2009 TOPP - www.openplans.org. All rights reserved.
 * This code is licensed under the GPL 2.0 license, available at the root
 * application directory.
 * 
 * @author Arne Kepp / OpenGeo
 */
package org.geonode.wfst;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.xml.namespace.QName;

import net.opengis.wfs.DeleteElementType;
import net.opengis.wfs.InsertElementType;
import net.opengis.wfs.TransactionResponseType;
import net.opengis.wfs.TransactionType;
import net.opengis.wfs.UpdateElementType;

import org.eclipse.emf.ecore.EObject;
import org.geoserver.catalog.Catalog;
import org.geoserver.catalog.CatalogBuilder;
import org.geoserver.catalog.CatalogFacade;
import org.geoserver.catalog.LayerGroupInfo;
import org.geoserver.catalog.LayerInfo;
import org.geoserver.catalog.ResourceInfo;
import org.geoserver.catalog.WMSLayerInfo;
import org.geoserver.config.GeoServer;
import org.geoserver.web.GeoServerApplication;
import org.geoserver.wfs.TransactionEvent;
import org.geoserver.wfs.TransactionEventType;
import org.geoserver.wfs.TransactionPlugin;
import org.geoserver.wfs.WFSException;
import org.geotools.data.simple.SimpleFeatureCollection;
import org.geotools.geometry.jts.ReferencedEnvelope;
import org.geotools.util.logging.Logging;
import org.opengis.referencing.FactoryException;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import org.opengis.referencing.operation.TransformException;
import org.springframework.util.Assert;

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
     * Update layer bounds if transaction type = UPDATE or INSERT
     * 
     * @see org.geoserver.wfs.TransactionListener#dataStoreChange(org.geoserver.wfs.TransactionEvent)
     */
    public void dataStoreChange(final TransactionEvent event) throws WFSException {
        log.info("DataStoreChange: " + event.getLayerName() + " " + event.getType());
        TransactionEventType eventType = event.getType();
        if (eventType == TransactionEventType.POST_UPDATE || eventType == TransactionEventType.POST_INSERT )
        try {
            dataStoreChangeInternal(event);
        } catch (RuntimeException e) {
            // Do never make the transaction fail due to a GWC error. Yell on the logs though
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
                
                
                /* Calculate new bounds using Catalog Builder */
                final CatalogBuilder cb = new CatalogBuilder(this.catalog);
                ReferencedEnvelope nativeBounds = cb.getNativeBounds(resource);  
                ReferencedEnvelope latlonBounds = cb.getLatLonBounds(nativeBounds, resource.getCRS());
                log.info("New bounding box:" + nativeBounds);

                /* Save new bounds */
                resource.setNativeBoundingBox(nativeBounds);
                resource.setLatLonBoundingBox(latlonBounds);
                this.catalog.save(resource);
                log.info("Layer bounds updated");
        } catch (Exception ef)
        {
        	log.info("Exception occurred" + ef.toString());
        }
    }


}
