/*
 *    GeoTools - The Open Source Java GIS Toolkit
 *    http://geotools.org
 *
 *    (C) 2008, Open Source Geospatial Foundation (OSGeo)
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation;
 *    version 2.1 of the License.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 */
package org.geonode.process.batchdownload;

import java.util.Collections;
import java.util.Map;
import java.util.TreeMap;
import java.util.logging.Logger;

import org.geonode.process.control.AsyncProcess;
import org.geonode.process.storage.Resource;
import org.geotools.data.Parameter;
import org.geotools.feature.NameImpl;
import org.geotools.process.impl.SingleProcessFactory;
import org.geotools.text.Text;
import org.geotools.util.logging.Logging;
import org.opengis.util.InternationalString;

/**
 * <p>
 * Inputs:
 * <ul>
 * <li>{@code map}: {@link MapMetadata}. Metadata about the map being downloaded, such as title and
 * author.
 * <li>{@code layers:} {@link LayerReference}, service urls, layernames, and other metadata for the
 * layers to be downloaded in batch.
 * <li>{@code locale}: {@link String}, the locale for status reports against this service.
 * </ul>
 * </p>
 */
public class BatchDownloadFactory extends SingleProcessFactory {

    public static final Logger LOGGER = Logging.getLogger("org.geonode.process");

    private static final String PROCESS_NAMESPACE = "geonode";

    private static final String PROCESS_NAME = "BatchDownload";

    /** Map metadata to include in download bundle. Optional. */
    public static final Parameter<MapMetadata> MAP_METADATA = new Parameter<MapMetadata>("map",
            MapMetadata.class, Text.text("Map Metadata"), Text.text("Map metadata to "
                    + "include in download bundle"), false, 0, 1, null, null);

    /** Service info about layers to download. Cardinality is 1..* */
    public static final Parameter<LayerReference> LAYERS = new Parameter<LayerReference>("LAYERS",
            LayerReference.class, Text.text("Map Layers"), Text.text("Service info for layers "
                    + "to include in the download."), true, 1, -1, null, null);

    /**
     * Map used for getParameterInfo; used to describe operation requirements for user interface
     * creation.
     */
    private static final Map<String, Parameter<?>> prameterInfo;

    static {
        Map<String, Parameter<?>> temp = new TreeMap<String, Parameter<?>>();
        temp.put(MAP_METADATA.key, MAP_METADATA);
        temp.put(LAYERS.key, LAYERS);
        prameterInfo = Collections.unmodifiableMap(temp);
    }

    public static final Parameter<Resource> RESULT_ZIP = new Parameter<Resource>("ZippedFile",
            Resource.class, Text.text("Handle to the zipped layers"),
            Text.text("A zip archive containing the requested datasets and metadata documents."));

    /**
     * Map used to describe operation results.
     */
    static final Map<String, Parameter<?>> resultInfo;

    static {
        Map<String, Parameter<?>> temp = new TreeMap<String, Parameter<?>>();
        temp.put(RESULT_ZIP.key, RESULT_ZIP);
        resultInfo = Collections.unmodifiableMap(temp);
    }

    public BatchDownloadFactory() {
        super(new NameImpl(PROCESS_NAMESPACE, PROCESS_NAME));
    }

    @Override
    public InternationalString getDescription() {
        return Text.text("Download the underlying data for a set of layers as a single archive.");
    }

    @Override
    public Map<String, Parameter<?>> getParameterInfo() {
        return prameterInfo;
    }

    @Override
    public Map<String, Parameter<?>> getResultInfo(Map<String, Object> parameters)
            throws IllegalArgumentException {
        return resultInfo;
    }

    @Override
    public InternationalString getTitle() {
        // please note that this is a title for display purposes only
        // finding an specific implementation by name is not possible
        return Text.text("Batch Downloader");
    }

    /**
     * @return {@code true}
     */
    @Override
    public boolean supportsProgress() {
        return true;
    }

    @Override
    public String getVersion() {
        return "0.1.0";
    }

    @Override
    public AsyncProcess create() throws IllegalArgumentException {
        return new BatchDownload();
    }
}
