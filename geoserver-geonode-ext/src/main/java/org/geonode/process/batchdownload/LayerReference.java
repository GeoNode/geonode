package org.geonode.process.batchdownload;

import java.net.URL;

import org.geotools.coverage.grid.io.AbstractGridCoverage2DReader;
import org.geotools.data.FeatureSource;
import org.geotools.geometry.jts.ReferencedEnvelope;
import org.opengis.feature.Feature;
import org.opengis.feature.type.FeatureType;

public class LayerReference {

    public static enum Kind {
        VECTOR, RASTER
    }

    private final Kind kind;

    private final String name;

    private final FeatureSource<? extends FeatureType, ? extends Feature> vectorSource;

    private final AbstractGridCoverage2DReader rasterSource;

    private URL metadataURL;

    private ReferencedEnvelope clipBounds;

    private URL defaultStyleURL;

    public LayerReference(String name,
            FeatureSource<? extends FeatureType, ? extends Feature> source) {
        kind = Kind.VECTOR;
        this.name = name;
        vectorSource = source;
        rasterSource = null;
    }

    public LayerReference(String name, AbstractGridCoverage2DReader source) {
        kind = Kind.RASTER;
        this.name = name;
        vectorSource = null;
        rasterSource = source;
    }

    public Kind getKind() {
        return kind;
    }

    public FeatureSource<? extends FeatureType, ? extends Feature> getVectorSource() {
        return vectorSource;
    }

    public AbstractGridCoverage2DReader getRasterSource() {
        return rasterSource;
    }

    public void setMetadataURL(URL metadataURL) {
        this.metadataURL = metadataURL;
    }

    public URL getMetadataURL() {
        return this.metadataURL;
    }

    public void setDefaultStyleURL(final URL styleURL) {
        this.defaultStyleURL = styleURL;
    }

    public URL getDefaultStyleURL() {
        return defaultStyleURL;
    }

    public String getName() {
        return name;
    }
}
