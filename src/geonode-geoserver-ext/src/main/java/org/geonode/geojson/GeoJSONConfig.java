package org.geonode.geojson;

import com.vividsolutions.jts.geom.CoordinateSequence;
import com.vividsolutions.jts.geom.Point;

/**
 * This class is work in progress and intended to abstract out the object model from the GeoJSON
 * parsing/writing. Thus, when it's interface is better defined it's gonna be abstracted out as an
 * interface and this is gonna be the GeoTools oriented (aka, SimpleFeature/Type + JTS Geometry)
 * implementation.
 * 
 */
public class GeoJSONConfig {

    public Object getCoordinateSequence(Object point) {
        CoordinateSequence coordinateSequence = ((Point) point).getCoordinateSequence();
        return coordinateSequence;
    }

    /**
     * Returns the dimension (usually 2 or 3) for the given {@code coordinate} object.
     * 
     * @param coordinate
     * @return
     */
    public int getDimension(Object coordinateSequence) {
        if (coordinateSequence instanceof CoordinateSequence) {
            return ((CoordinateSequence) coordinateSequence).getDimension();
        }
        throw new IllegalArgumentException("unrecognized coordinateSequence type: "
                + (coordinateSequence == null ? "null" : coordinateSequence.getClass().getName()));
    }

    public double getOrdinate(final Object coordinatesequence, final int index, final int ordinate) {
        return ((CoordinateSequence) coordinatesequence).getOrdinate(index, ordinate);
    }

    public int getSize(final Object coordinateSequence) {
        if (coordinateSequence instanceof CoordinateSequence) {
            return ((CoordinateSequence) coordinateSequence).size();
        }
        throw new IllegalArgumentException("unrecognized coordinateSequence type: "
                + (coordinateSequence == null ? "null" : coordinateSequence.getClass().getName()));
    }

    public GeoJSONObjectType getGeometryType(Object geometry) {
        return GeoJSONObjectType.POINT;
    }

}
