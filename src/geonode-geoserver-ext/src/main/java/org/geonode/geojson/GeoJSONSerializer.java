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
        default:
            throw new IllegalArgumentException("Unrecognized geometry type: " + geometryType);
        }
        return this;
    }

    public GeoJSONSerializer coordinates(final Object coordinates) throws JSONException {
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

    public GeoJSONSerializer point(final Object point) throws JSONException {
        this.object();
        this.key("type").value(GeoJSONObjectType.POINT.getJSONName());

        this.key("coordinates");

        final Object coordinateSequence = config.getCoordinateSequence(point);
        final int dimension = config.getDimension(coordinateSequence);
        this.coordinate(coordinateSequence, dimension, 0);
        this.endObject();
        return this;
    }

    public void lineString(final Object lineString) {
        this.object();
        this.key("type").value(GeoJSONObjectType.LINESTRING.getJSONName());

        final Object coordinateSequence = config.getCoordinateSequence(lineString);
        this.coordinates(coordinateSequence);

        this.endObject();
    }

    public void polygon(final Object polygon) {
        this.object();
        this.key("type").value(GeoJSONObjectType.POLYGON.getJSONName());

        this.key("coordinates");
        this.array();

        final Object shell = config.getExteriorRing(polygon);
        this.coordinatesInternal(shell);

        final int numHoles = config.getNumInteriorRings(polygon);
        for (int holeN = 0; holeN < numHoles; holeN++) {
            Object interiorRingCoordSeq = config.getInteriorRingN(polygon, holeN);
            coordinatesInternal(interiorRingCoordSeq);
        }

        this.endArray();
        this.endObject();
    }

}
