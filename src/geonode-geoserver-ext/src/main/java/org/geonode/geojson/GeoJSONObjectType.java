package org.geonode.geojson;

/**
 * Enumeration for the defined GeoJSON objects as per the <a
 * href="http://geojson.org/geojson-spec.html">1.0 spec</a>.
 */
public enum GeoJSONObjectType {
    /**
     * <a href="http://geojson.org/geojson-spec.html#feature-objects">GeoJSON Feature type</a>
     */
    FEATURE("Point"),

    /**
     * <a href="http://geojson.org/geojson-spec.html#feature-collection-objects">GeoJSON
     * FeatureCollection type</a>
     */
    FEATURECOLLECTION("FeatureCollection"),

    /**
     * <a href="http://geojson.org/geojson-spec.html#point">GeoJSON Point Geometry type</a>
     */
    POINT("Point"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#multipoint">GeoJSON MultiPoint Geometry
     * type</a>
     */
    MULTIPOINT("MultiPoint"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#linestring">GeoJSON LineString Geometry
     * type</a>
     */
    LINESTRING("LineString"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#multilinestring">GeoJSON MultiLineString
     * Geometry type</a>
     */
    MULTILINESTRING("MultiLineString"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#polygon">GeoJSON Polygon Geometry type</a>
     */
    POLYGON("Polygon"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#multipolygon">GeoJSON MultiPolygon Geometry
     * type</a>
     */
    MULTIPOLYGON("MultiPolygon"),
    /**
     * <a href="http://geojson.org/geojson-spec.html#geometry-collection">GeoJSON GeometryCollection
     * Geometry type</a>
     */
    GEOMETRYCOLLECTION("GeometryCollection");

    private String jsonName;

    private GeoJSONObjectType(final String jsonName) {
        this.jsonName = jsonName;
    }

    /**
     * Returns the geometry type name as it shall appear in the {@code type} attribute, like in
     * {@code "type": "Point", "coordinates": [100.0, 0.0] }
     * 
     * @return the geometry type name for the geometry's JSON representation
     */
    public String getJSONName() {
        return jsonName;
    }

    public static GeoJSONObjectType fromJSONTypeName(final String jsonType) {
        return valueOf(jsonType.toUpperCase());
    }
}
