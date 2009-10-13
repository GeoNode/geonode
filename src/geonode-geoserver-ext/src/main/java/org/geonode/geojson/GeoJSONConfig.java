package org.geonode.geojson;

import com.vividsolutions.jts.geom.CoordinateSequence;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryCollection;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.MultiLineString;
import com.vividsolutions.jts.geom.MultiPoint;
import com.vividsolutions.jts.geom.MultiPolygon;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;

/**
 * This class is work in progress and intended to abstract out the object model from the GeoJSON
 * parsing/writing. Thus, when it's interface is better defined it's gonna be abstracted out as an
 * interface and this is gonna be the GeoTools oriented (aka, SimpleFeature/Type + JTS Geometry)
 * implementation.
 * 
 */
public class GeoJSONConfig {

    public Object getCoordinateSequence(Object geometry) {
        CoordinateSequence coordinateSequence;
        if (geometry instanceof Point) {
            coordinateSequence = ((Point) geometry).getCoordinateSequence();
        } else if (geometry instanceof LineString) {
            coordinateSequence = ((LineString) geometry).getCoordinateSequence();
        } else {
            throw new IllegalArgumentException(
                    "Geometry is not composed of a single coordinate sequence:" + geometry);
        }
        return coordinateSequence;
    }

    /**
     * Returns the dimension (usually 2 or 3) for the given {@code coordinate} object.
     * 
     * @param coordinate
     * @return
     */
    public int getDimension(final Object geom) {
        if (geom instanceof CoordinateSequence) {
            return ((CoordinateSequence) geom).getDimension();
        }
        if (geom instanceof Geometry) {
            return getDimension(((Geometry) geom).getInteriorPoint().getCoordinateSequence());
        }
        throw new IllegalArgumentException("unrecognized coordinateSequence type: "
                + (geom == null ? "null" : geom.getClass().getName()));
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
        if (geometry instanceof Point) {
            return GeoJSONObjectType.POINT;
        }
        if (geometry instanceof MultiPoint) {
            return GeoJSONObjectType.MULTIPOINT;
        }
        if (geometry instanceof LineString) {
            return GeoJSONObjectType.LINESTRING;
        }
        if (geometry instanceof MultiLineString) {
            return GeoJSONObjectType.MULTILINESTRING;
        }
        if (geometry instanceof Polygon) {
            return GeoJSONObjectType.POLYGON;
        }
        if (geometry instanceof MultiPolygon) {
            return GeoJSONObjectType.MULTIPOLYGON;
        }
        if (geometry instanceof GeometryCollection) {
            return GeoJSONObjectType.GEOMETRYCOLLECTION;
        }
        throw new IllegalArgumentException("Unknown geometry type: " + geometry);
    }

    public Object getExteriorRing(final Object polygon) {
        return getCoordinateSequence(((Polygon) polygon).getExteriorRing());
    }

    public int getNumInteriorRings(final Object polygon) {
        return ((Polygon) polygon).getNumInteriorRing();
    }

    public Object getInteriorRingN(final Object polygon, final int holeN) {
        return getCoordinateSequence(((Polygon) polygon).getInteriorRingN(holeN));
    }

    public int getNumGeometries(final Object geometryCollection) {
        return ((GeometryCollection) geometryCollection).getNumGeometries();
    }

    public Object getGeometryN(final Object geometryCollection, final int geomN) {
        return ((GeometryCollection) geometryCollection).getGeometryN(geomN);
    }

}
