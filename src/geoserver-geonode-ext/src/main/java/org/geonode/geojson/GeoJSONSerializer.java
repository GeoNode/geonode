package org.geonode.geojson;

import java.io.Writer;

import net.sf.json.JSONException;
import net.sf.json.util.JSONBuilder;

public class GeoJSONSerializer extends JSONBuilder {

    private GeoJSONConfig config = new GeoJSONConfig();

    public GeoJSONSerializer(final Writer w) {
        super(w);
    }

    public GeoJSONSerializer writeGeometry(final Object geometry) {
        final GeoJSONObjectType geometryType = config.getGeometryType(geometry);
        switch (geometryType) {
        case POINT:
            point(geometry);
            break;
        case LINESTRING:
            lineString(geometry);
            break;
        case POLYGON:
            polygon(geometry);
            break;
        case MULTIPOINT:
            multiPoint(geometry);
            break;
        case MULTILINESTRING:
            multiLineString(geometry);
            break;
        case MULTIPOLYGON:
            multiPolygon(geometry);
            break;
        case GEOMETRYCOLLECTION:
            geometryCollection(geometry);
            break;
        default:
            throw new IllegalArgumentException("Unrecognized geometry type: " + geometryType);
        }
        return this;
    }

    private GeoJSONSerializer coordinates(final Object coordinates) throws JSONException {
        this.key("coordinates");

        coordinatesInternal(coordinates);

        return this;
    }

    private void coordinatesInternal(final Object coordinates) {
        this.array();
        final int dimension = config.getDimension(coordinates);
        final int size = config.getSize(coordinates);

        for (int coordN = 0; coordN < size; coordN++) {
            coordinate(coordinates, dimension, coordN);
        }
        this.endArray();
    }

    private void coordinate(final Object coordinates, final int dimension, int coordN) {
        double ordinate;
        this.array();
        for (int ordinateN = 0; ordinateN < dimension; ordinateN++) {
            ordinate = config.getOrdinate(coordinates, coordN, ordinateN);
            if (Double.isNaN(ordinate)) {
                ordinate = 0D;
            }
            this.value(ordinate);
        }
        this.endArray();
    }

    private GeoJSONSerializer point(final Object point) throws JSONException {
        this.object();
        this.key("type").value(GeoJSONObjectType.POINT.getJSONName());

        this.key("coordinates");

        final Object coordinateSequence = config.getCoordinateSequence(point);
        final int dimension = config.getDimension(coordinateSequence);
        this.coordinate(coordinateSequence, dimension, 0);

        crs(point);

        this.endObject();
        return this;
    }

    private GeoJSONSerializer lineString(final Object lineString) {
        this.object();
        this.key("type").value(GeoJSONObjectType.LINESTRING.getJSONName());

        final Object coordinateSequence = config.getCoordinateSequence(lineString);
        this.coordinates(coordinateSequence);

        crs(lineString);

        this.endObject();
        return this;
    }

    private GeoJSONSerializer polygon(final Object polygon) {
        this.object();
        this.key("type").value(GeoJSONObjectType.POLYGON.getJSONName());

        this.key("coordinates");
        polygonInternal(polygon);

        crs(polygon);

        this.endObject();
        return this;
    }

    private void crs(Object geometryOrFeature) {
        String crsName = config.getCRSName(geometryOrFeature);
        if (crsName != null) {
            this.key("crs");
            this.object();
            this.key("type").value("name");
            this.key("properties");
            this.object();
            this.key("name").value(crsName);
            this.endObject();
            this.endObject();
        }
    }

    private void polygonInternal(final Object polygon) {
        this.array();

        final Object shell = config.getExteriorRing(polygon);
        this.coordinatesInternal(shell);

        final int numHoles = config.getNumInteriorRings(polygon);
        for (int holeN = 0; holeN < numHoles; holeN++) {
            Object interiorRingCoordSeq = config.getInteriorRingN(polygon, holeN);
            coordinatesInternal(interiorRingCoordSeq);
        }

        this.endArray();
    }

    private GeoJSONSerializer multiPoint(final Object multiPoint) {
        this.object();
        this.key("type").value(GeoJSONObjectType.MULTIPOINT.getJSONName());

        this.key("coordinates");
        final int dimension = config.getDimension(multiPoint);
        final int numGeoms = config.getNumGeometries(multiPoint);
        this.array();
        for (int geomN = 0; geomN < numGeoms; geomN++) {
            Object geometryN = config.getGeometryN(multiPoint, geomN);
            Object coordinates = config.getCoordinateSequence(geometryN);
            this.coordinate(coordinates, dimension, 0);
        }
        this.endArray();

        crs(multiPoint);

        this.endObject();
        return this;
    }

    private GeoJSONSerializer multiLineString(final Object multiLineString) {
        this.object();
        this.key("type").value(GeoJSONObjectType.MULTILINESTRING.getJSONName());

        this.key("coordinates");
        final int numGeoms = config.getNumGeometries(multiLineString);
        this.array();
        for (int geomN = 0; geomN < numGeoms; geomN++) {
            Object geometryN = config.getGeometryN(multiLineString, geomN);
            Object coordinates = config.getCoordinateSequence(geometryN);
            this.coordinatesInternal(coordinates);
        }
        this.endArray();

        crs(multiLineString);

        this.endObject();
        return this;
    }

    private GeoJSONSerializer multiPolygon(final Object multiPolygon) {
        this.object();
        this.key("type").value(GeoJSONObjectType.MULTIPOLYGON.getJSONName());

        this.key("coordinates");
        final int numGeoms = config.getNumGeometries(multiPolygon);
        this.array();
        for (int geomN = 0; geomN < numGeoms; geomN++) {
            Object geometryN = config.getGeometryN(multiPolygon, geomN);
            polygonInternal(geometryN);
        }
        this.endArray();

        crs(multiPolygon);

        this.endObject();
        return this;
    }

    private GeoJSONSerializer geometryCollection(final Object geometryCollection) {
        this.object();
        this.key("type").value(GeoJSONObjectType.GEOMETRYCOLLECTION.getJSONName());

        this.key("geometries");
        final int numGeoms = config.getNumGeometries(geometryCollection);
        this.array();
        for (int geomN = 0; geomN < numGeoms; geomN++) {
            Object geometryN = config.getGeometryN(geometryCollection, geomN);
            writeGeometry(geometryN);
        }
        this.endArray();
        crs(geometryCollection);
        this.endObject();
        return this;
    }
}
