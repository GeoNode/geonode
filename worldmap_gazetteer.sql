-- Table: gazetteer_placename

-- DROP TABLE gazetteer_placename;

CREATE TABLE gazetteer_placename
(
  id serial NOT NULL,
  layer_name character varying(256) NOT NULL,
  layer_attribute character varying(256) NOT NULL,
  feature_type character varying(50) NOT NULL,
  feature_fid bigint NOT NULL,
  latitude double precision,
  longitude double precision,
  place_name character varying(2048) NOT NULL,
  start_date date,
  end_date date,
  project character varying(256),
  feature geometry NOT NULL,
  CONSTRAINT gazetteer_placename_pkey PRIMARY KEY (id ),
  CONSTRAINT enforce_dims_feature CHECK (st_ndims(feature) = 2),
  CONSTRAINT enforce_srid_feature CHECK (st_srid(feature) = 4326)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE gazetteer_placename
  OWNER TO wmuser;

-- Index: gazetteer_placename_feature_id

-- DROP INDEX gazetteer_placename_feature_id;

CREATE INDEX gazetteer_placename_feature_id
  ON gazetteer_placename
  USING gist
  (feature );

-- Index: gazetteer_placename_layer_attribute

-- DROP INDEX gazetteer_placename_layer_attribute;

CREATE INDEX gazetteer_placename_layer_attribute
  ON gazetteer_placename
  USING btree
  (layer_attribute COLLATE pg_catalog."default" );

-- Index: gazetteer_placename_layer_name

-- DROP INDEX gazetteer_placename_layer_name;

CREATE INDEX gazetteer_placename_layer_name
  ON gazetteer_placename
  USING btree
  (layer_name COLLATE pg_catalog."default" );

