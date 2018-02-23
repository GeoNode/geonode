var doc = (new OpenLayers.Format.XML).read(
'<?xml version="1.0" encoding="UTF-8"?>' +
'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:gml="http://www.opengis.net/gml" xmlns:topp="http://www.openplans.org/topp" elementFormDefault="qualified" targetNamespace="http://www.openplans.org/topp">' +
  '<xsd:import namespace="http://www.opengis.net/gml" schemaLocation="http://sigma.openplans.org:80/geoserver/schemas/gml/3.1.1/base/gml.xsd"/>' +
  '<xsd:complexType name="statesType">' +
    '<xsd:complexContent>' +
      '<xsd:extension base="gml:AbstractFeatureType">' +
        '<xsd:sequence>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="the_geom" nillable="true" type="gml:MultiSurfacePropertyType"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="STATE_NAME" nillable="false">' +
            '<xsd:simpleType>' +
              '<xsd:restriction base="xsd:string">' +
                '<xsd:maxLength value="10"/>' +
                '<xsd:minLength value="5"/>' +
              '</xsd:restriction>' +
            '</xsd:simpleType>' +
          '</xsd:element>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="SAMP_POP" nillable="true">' +
            '<xsd:simpleType>' +
              '<xsd:restriction base="xsd:double">' +
                '<xsd:maxInclusive value="10"/>' +
                '<xsd:minInclusive value="5"/>' +
              '</xsd:restriction>' +
            '</xsd:simpleType>' +
          '</xsd:element>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="BOOLEAN" nillable="true" type="xsd:boolean"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="DATETIME" nillable="true" type="xsd:dateTime"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="DATE" nillable="true" type="xsd:date"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="STATE_FIPS" nillable="true" type="xsd:string"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="SUB_REGION" nillable="true" type="xsd:string"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="STATE_ABBR" nillable="true" type="xsd:string"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="LAND_KM" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="WATER_KM" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="PERSONS" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="FAMILIES" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="HOUSHOLD" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="MALE" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="FEMALE" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="WORKERS" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="DRVALONE" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="CARPOOL" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="PUBTRANS" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="EMPLOYED" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="UNEMPLOY" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="SERVICE" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="MANUAL" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="P_MALE" nillable="true" type="xsd:double"/>' +
          '<xsd:element maxOccurs="1" minOccurs="0" name="P_FEMALE" nillable="true" type="xsd:double"/>' +
          '<xsd:element name="DRINK_NAME" minOccurs="0" nillable="true">' +
            '<xsd:simpleType>' +
              '<xsd:restriction base="xs:string">' +
                '<xsd:enumeration value="pop"/>' +
                '<xsd:enumeration value="soda"/>' +
                '<xsd:enumeration value="other"/>' +
              '</xsd:restriction>' +
            '</xsd:simpleType>' +
          '</xsd:element>' +
        '</xsd:sequence>' +
      '</xsd:extension>' +
    '</xsd:complexContent>' +
  '</xsd:complexType>' +
  '<xsd:element name="states" substitutionGroup="gml:_Feature" type="topp:statesType"/>' +
'</xsd:schema>'
);

