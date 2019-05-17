# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import traceback
import psycopg2

from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis import geos

from geonode.contrib.risks.models import Region, AdministrativeDivision
from geonode.contrib.risks.models import RiskAnalysis, RiskApp
from geonode.contrib.risks.models import RiskAnalysisDymensionInfoAssociation
from geonode.contrib.risks.models import RiskAnalysisAdministrativeDivisionAssociation

import xlrd
from xlrd.sheet import ctype_text


class Command(BaseCommand):
    """
    For each Scenario / Round Period, check the Administrative Unit
    and store the value on the db:

    e.g.:

      Feature ==> Layer {dim1: "Hospital", dim2: "10", adm_code: "AF", value: 30000000}
      Feature ==> Layer {dim1: "Hospital", dim2: "10", adm_code: "AF15", value: 3000000}
      Feature ==> Layer {dim1: "SSP2", dim2: "250", adm_code: "AF29", value: 44340000}

    Example Usage:
    $> python manage.py importriskdata -r Afghanistan \
        -k "WP6_future_proj_Hospital" -x WP6__Impact_analysis_results_future_projections_Hospital.xlsx
    $> python manage.py importriskdata -r Afghanistan \
        -k "WP6_future_proj_Population" -x WP6__Impact_analysis_results_future_projections_Population.xlsx
    $> python manage.py importriskdata -r Afghanistan \
        -k "WP6_loss_Afg_PML_split" -x WP6\ -\ 2050\ Scenarios\ -...\ Afghanistan\ PML\ Split.xlsx

    To import Metadata also, specify the Risk Metadada File wih the 'm' option

    $> python manage.py importriskdata -r Afghanistan -k "WP6_future_proj_Population" \
                    -x WP6__Impact_analysis_results_future_projections_Population.xlsx \
                    -m WP6_Impact_analysis_results_future_projections_Population\ -\ metadata.xlsx

    The procedure requires a layer on GeoServer based on the following table definition:
        CREATE TABLE public.test
        (
          fid serial not null,
          the_geom geometry(MultiPolygon,4326),
          risk_analysis character varying(80),
          hazard_type character varying(30),
          admin character varying(150),
          adm_code character varying(30),
          region character varying(80),
          CONSTRAINT test_pkey PRIMARY KEY (fid)
        )
        WITH (
          OIDS=FALSE
        );
        ALTER TABLE public.test
          OWNER TO geonode;

        CREATE INDEX spatial_test_the_geom
          ON public.test
          USING gist
          (the_geom);

        CREATE INDEX test_idx_nulls_low
          ON public.test (risk_analysis NULLS FIRST, hazard_type, adm_code, region);

        --

        CREATE TABLE public.dimension
        (
          dim_id serial not null,
          dim_col character varying(30),
          dim_value character varying(255),
          dim_order int not null default 0,
          CONSTRAINT dimension_pkey PRIMARY KEY (dim_id)
        )
        WITH (
          OIDS=FALSE
        );
        ALTER TABLE public.dimension
          OWNER TO geonode;

        CREATE INDEX dimension_idx
          ON public.dimension (dim_col, dim_value);

        --

        CREATE TABLE public.test_dimensions
        (
          test_fid integer,
          dim1_id integer,
          dim2_id integer,
          dim3_id integer,
          dim4_id integer,
          dim5_id integer,
          value character varying(255),
          CONSTRAINT test_dimensions_dim1_id_fkey FOREIGN KEY (dim1_id)
              REFERENCES public.dimension (dim_id) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_dim2_id_fkey FOREIGN KEY (dim2_id)
              REFERENCES public.dimension (dim_id) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_dim3_id_fkey FOREIGN KEY (dim3_id)
              REFERENCES public.dimension (dim_id) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_dim4_id_fkey FOREIGN KEY (dim4_id)
              REFERENCES public.dimension (dim_id) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_dim5_id_fkey FOREIGN KEY (dim5_id)
              REFERENCES public.dimension (dim_id) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_test_fid_fkey FOREIGN KEY (test_fid)
              REFERENCES public.test (fid) MATCH SIMPLE
              ON UPDATE NO ACTION ON DELETE CASCADE,
          CONSTRAINT test_dimensions_unique_constraint UNIQUE (test_fid, dim1_id, dim2_id, dim3_id, dim4_id, dim5_id)
        )
        WITH (
          OIDS=FALSE
        );
        ALTER TABLE public.test_dimensions
          OWNER TO geonode;


    The GeoServer Parametric Layer should be defined as follows

    SELECT public.test.*, value, dim1_value, dim2_value, dim3_value, dim4_value, dim5_value
      FROM public.test
        JOIN (
          SELECT join_table.test_fid, join_table.value,
                 d1.dim_col dim1_col, d1.dim_value dim1_value,
                 d2.dim_col dim2_col, d2.dim_value dim2_value,
                 d3.dim_col dim3_col, d3.dim_value dim3_value,
                 d4.dim_col dim4_col, d4.dim_value dim4_value,
                 d5.dim_col dim5_col, d5.dim_value dim5_value
            FROM
    	  public.test_dimensions join_table
    	    LEFT JOIN public.dimension d1 ON (d1.dim_id = join_table.dim1_id)
    	    LEFT JOIN public.dimension d2 ON (d2.dim_id = join_table.dim2_id)
    	    LEFT JOIN public.dimension d3 ON (d3.dim_id = join_table.dim3_id)
    	    LEFT JOIN public.dimension d4 ON (d4.dim_id = join_table.dim4_id)
    	    LEFT JOIN public.dimension d5 ON (d5.dim_id = join_table.dim5_id)
        ) rd ON (rd.test_fid = fid)
    WHERE
      risk_analysis = '%ra%' AND
      hazard_type = '%ha%' AND
      (region = '%region%' OR admin = '%admin%' OR adm_code = '%adm_code%' OR
         (coalesce('%adm_code%', '') = '' AND
           adm_code LIKE '%sub_adm_code%__' AND adm_code <> '%super_adm_code%')
      ) AND
      (dim1_value = '%d1%' OR dim1_value is NULL) AND
      (dim2_value = '%d2%' OR dim2_value is NULL) AND
      (dim3_value = '%d3%' OR dim3_value is NULL) AND
      (dim4_value = '%d4%' OR dim4_value is NULL) AND
      (dim5_value = '%d5%' OR dim5_value is NULL)


    With ordering:

    SELECT public.test.*, value, dim1_value, dim2_value, dim3_value, dim4_value, dim5_value
      FROM public.test
        JOIN (
          SELECT join_table.test_fid, join_table.value,
                 d1.dim_col dim1_col, d1.dim_value dim1_value, d1.dim_order dim1_order,
                 d2.dim_col dim2_col, d2.dim_value dim2_value, d2.dim_order dim2_order,
                 d3.dim_col dim3_col, d3.dim_value dim3_value, d3.dim_order dim3_order,
                 d4.dim_col dim4_col, d4.dim_value dim4_value, d4.dim_order dim4_order,
                 d5.dim_col dim5_col, d5.dim_value dim5_value, d5.dim_order dim5_order
            FROM
    	  public.test_dimensions join_table
    	    LEFT JOIN public.dimension d1 ON (d1.dim_id = join_table.dim1_id)
    	    LEFT JOIN public.dimension d2 ON (d2.dim_id = join_table.dim2_id)
    	    LEFT JOIN public.dimension d3 ON (d3.dim_id = join_table.dim3_id)
    	    LEFT JOIN public.dimension d4 ON (d4.dim_id = join_table.dim4_id)
    	    LEFT JOIN public.dimension d5 ON (d5.dim_id = join_table.dim5_id)
        ) rd ON (rd.test_fid = fid)

    WHERE
      risk_analysis = '%ra%' AND
      hazard_type = '%ha%' AND
      (region = '%region%' OR admin = '%admin%' OR adm_code = '%adm_code%' OR
        (coalesce('%adm_code%', '') = '' AND
         adm_code LIKE '%sub_adm_code%__' AND adm_code <> '%super_adm_code%')
      ) AND
      (dim1_value = '%d1%' OR dim1_value is NULL) AND
      (dim2_value = '%d2%' OR dim2_value is NULL) AND
      (dim3_value = '%d3%' OR dim3_value is NULL) AND
      (dim4_value = '%d4%' OR dim4_value is NULL) AND
      (dim5_value = '%d5%' OR dim5_value is NULL)

      order by %order_by%



    Querying GeoServer means passing through "viewparams" similar to the following ones:

    viewparams=ra:WP6_future_proj_Hospital;ha:EQ;region:Afghanistan;adm_code:AF;d1:Hospital;d2:10


    An example of a full WMS GetMap Request to the "test" Layer will be something like:

    http://localhost:8080/geoserver/geonode/wms?
        service=WMS&
        version=1.1.0&
        request=GetMap&
        layers=geonode:test&
        styles=&
        bbox=-180,-90,180,90&
        width=768&
        height=768&
        srs=EPSG:4326&
        format=application/openlayers&
        viewparams=ra:WP6_future_proj_Hospital;ha:EQ;region:Afghanistan;adm_code:AF;d1:Hospital;d2:10

    Add the following parameter if you need to filter out geometries or some other field

        propertyname=risk_analysis,hazard_type,region,adm_code,dim1_value,dim2_value,dim3_value,dim4_value,dim5_value,value


    Tabbed Data can be obtained by defining a SQL Parametric View like this:

    SELECT public.test.*, value,
       	dim1_col, dim1_value,
    	dim2_col, dim2_value,
    	dim3_col, dim3_value,
    	dim4_col, dim4_value,
    	dim5_col, dim5_value
      FROM public.test
        JOIN (
          SELECT join_table.test_fid, join_table.value,
                 d1.dim_col dim1_col, d1.dim_value dim1_value, d1.dim_order dim1_order,
                 d2.dim_col dim2_col, d2.dim_value dim2_value, d2.dim_order dim2_order,
                 d3.dim_col dim3_col, d3.dim_value dim3_value, d3.dim_order dim3_order,
                 d4.dim_col dim4_col, d4.dim_value dim4_value, d4.dim_order dim4_order,
                 d5.dim_col dim5_col, d5.dim_value dim5_value, d5.dim_order dim5_order
            FROM
    	  public.test_dimensions join_table
    	    LEFT JOIN public.dimension d1 ON (d1.dim_id = join_table.dim1_id)
    	    LEFT JOIN public.dimension d2 ON (d2.dim_id = join_table.dim2_id)
    	    LEFT JOIN public.dimension d3 ON (d3.dim_id = join_table.dim3_id)
    	    LEFT JOIN public.dimension d4 ON (d4.dim_id = join_table.dim4_id)
    	    LEFT JOIN public.dimension d5 ON (d5.dim_id = join_table.dim5_id)
        ) rd ON (rd.test_fid = fid)
        order by dim1_order, dim2_order



    And perform queries using "cql_filter" parameter

    http://localhost:8080/geoserver/geonode/ows?
        service=WFS&
        version=1.0.0&
        request=GetFeature&
        typeName=geonode:test_data&
        outputFormat=application%2Fjson&
        cql_filter=(risk_analysis=%27WP6_future_proj_Hospital%27%20and%20hazard_type=%27EQ%27%20and%20adm_code=%27AF%27%20and%20dim1_value=%27Hospital%27)&
        propertyname=risk_analysis,hazard_type,region,adm_code,dim1_value,dim2_value,dim3_value,dim4_value,dim5_value,value

    """

    help = 'Import Risk Data: Loss Impact and Impact Analysis Types.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--commit',
            action='store_true',
            dest='commit',
            default=True,
            help='Commits Changes to the storage.')
        parser.add_argument(
            '-r',
            '--region',
            dest='region',
            type=str,
            help='Destination Region.')
        parser.add_argument(
            '-x',
            '--excel-file',
            dest='excel_file',
            type=str,
            help='Input Risk Data Table as XLSX File.')
        parser.add_argument(
            '-m',
            '--excel-metadata-file',
            dest='excel_metadata_file',
            type=str,
            help='Input Risk Metadata Table as XLSX File.')
        parser.add_argument(
            '-k',
            '--risk-analysis',
            dest='risk_analysis',
            type=str,
            help='Name of the Risk Analysis associated to the File.')
        parser.add_argument(
            '-a',
            '--risk-app',
            dest='risk_app',
            type=str,
            # nargs=1,
            default=RiskApp.APP_DATA_EXTRACTION,
            help="Name of Risk App, default: {}".format(RiskApp.APP_DATA_EXTRACTION),
            )
        return parser

    def handle(self, **options):
        commit = options.get('commit')
        region = options.get('region')
        excel_file = options.get('excel_file')
        risk_analysis = options.get('risk_analysis')
        excel_metadata_file = options.get('excel_metadata_file')
        risk_app =  options.get('risk_app')
        app = RiskApp.objects.get(name=risk_app)

        if region is None:
            raise CommandError("Input Destination Region '--region' is mandatory")

        if risk_analysis is None:
            raise CommandError("Input Risk Analysis associated to the File \
'--risk_analysis' is mandatory")

        if not excel_file or len(excel_file) == 0:
            raise CommandError("Input Risk Data Table '--excel_file' is mandatory")

        risk = RiskAnalysis.objects.get(name=risk_analysis, app=app)

        wb = xlrd.open_workbook(filename=excel_file)
        region = Region.objects.get(name=region)
        region_code = region.administrative_divisions.filter(parent=None)[0].code

        scenarios = RiskAnalysisDymensionInfoAssociation.objects.filter(riskanalysis=risk, axis='x')
        round_periods = RiskAnalysisDymensionInfoAssociation.objects.filter(riskanalysis=risk, axis='y')

        table_name = risk.layer.typename.split(":")[1] \
            if ":" in risk.layer.typename else risk.layer.typename

        for scenario in scenarios:
            # Dump Vectorial Data from DB
            datastore = settings.OGC_SERVER['default']['DATASTORE']
            if (datastore):
                ogc_db_name = settings.DATABASES[datastore]['NAME']
                ogc_db_user = settings.DATABASES[datastore]['USER']
                ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                ogc_db_host = settings.DATABASES[datastore]['HOST']
                ogc_db_port = settings.DATABASES[datastore]['PORT']

            sheet = wb.sheet_by_name(scenario.value)
            row_headers = sheet.row(0)
            for rp_idx, rp in enumerate(round_periods):
                col_num = -1
                if app.name == RiskApp.APP_DATA_EXTRACTION:
                    for idx, cell_obj in enumerate(row_headers):
                        # cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
                        # print('(%s) %s %s' % (idx, cell_type_str, cell_obj.value))
                        try:
                            # if int(cell_obj.value) == int(rp.value):
                            if cell_obj.value == rp.value:
                                # print('[%s] (%s) RP-%s' % (scenario.value, idx, rp.value))
                                col_num = idx
                                break
                        except:
                            traceback.print_exc()
                            pass
                elif app.name == RiskApp.APP_COST_BENEFIT:
                     col_num = 0

                if col_num >= 0:
                    conn = self.get_db_conn(ogc_db_name, ogc_db_user, ogc_db_port, ogc_db_host, ogc_db_passwd)
                    try:
                        if app.name == RiskApp.APP_DATA_EXTRACTION:
                            for row_num in range(1, sheet.nrows):
                                cell_obj = sheet.cell(row_num, 5)
                                cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
                                # print('(%s) %s %s' % (idx, cell_type_str, cell_obj.value))
                                if cell_obj.value:
                                    adm_code = cell_obj.value \
                                        if cell_type_str == 'text' \
                                        else region_code + '{:04d}'.format(int(cell_obj.value))
                                    adm_div = AdministrativeDivision.objects.get(code=adm_code)
                                    value = sheet.cell_value(row_num, col_num)
                                    print('[%s] (%s) %s / %s' % (scenario.value, rp.value, adm_div.name, value))

                                    db_values = {
                                        'table': table_name,  # From rp.layer
                                        'the_geom': geos.fromstr(adm_div.geom, srid=adm_div.srid),
                                        'dim1': scenario.value,
                                        'dim1_order': scenario.order,
                                        'dim2': rp.value,
                                        'dim2_order': rp.order,
                                        'dim3': None,
                                        'dim4': None,
                                        'dim5': None,
                                        'risk_analysis': risk_analysis,
                                        'hazard_type': risk.hazard_type.mnemonic,
                                        'admin': adm_div.name,
                                        'adm_code': adm_div.code,
                                        'region': region.name,
                                        'value': value
                                    }
                                    self.insert_db(conn, db_values)
                                    risk_adm = RiskAnalysisAdministrativeDivisionAssociation.\
                                        objects.\
                                        filter(riskanalysis=risk, administrativedivision=adm_div)
                                    if len(risk_adm) == 0:
                                        RiskAnalysisAdministrativeDivisionAssociation.\
                                            objects.\
                                            create(riskanalysis=risk, administrativedivision=adm_div)
                        elif app.name == RiskApp.APP_COST_BENEFIT:
                            cell_obj = sheet.cell(rp_idx + 1, 0)
                            cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
                            if cell_obj.value:
                                adm_div = AdministrativeDivision.objects.get(name=region)
                                value = sheet.cell_value(rp_idx + 1, 1)
                                print('[%s] (%s) %s / %s' % (scenario.value, rp.value, adm_div.name, value))

                                db_values = {
                                'table': table_name,  # From rp.layer
                                'the_geom': geos.fromstr(adm_div.geom, srid=adm_div.srid),
                                'dim1': scenario.value,
                                'dim1_order': scenario.order,
                                'dim2': rp.value,
                                'dim2_order': rp.order,
                                'dim3': None,
                                'dim4': None,
                                'dim5': None,
                                'risk_analysis': risk_analysis,
                                'hazard_type': risk.hazard_type.mnemonic,
                                'admin': adm_div.name,
                                'adm_code': adm_div.code,
                                'region': region.name,
                                'value': value
                                }
                                self.insert_db(conn, db_values)
                                risk_adm = RiskAnalysisAdministrativeDivisionAssociation.\
                                objects.\
                                filter(riskanalysis=risk, administrativedivision=adm_div)
                                if len(risk_adm) == 0:
                                    RiskAnalysisAdministrativeDivisionAssociation.\
                                    objects.\
                                    create(riskanalysis=risk, administrativedivision=adm_div)

                        # Finished Import: Commit on DB
                        conn.commit()
                    except Exception:
                        try:
                            conn.rollback()
                        except:
                            pass

                        traceback.print_exc()
                    finally:
                        conn.close()

        # Import or Update Metadata if Metadata File has been specified/found
        if excel_metadata_file:
            call_command('importriskmetadata',
                         region=region.name,
                         excel_file=excel_metadata_file,
                         risk_analysis=risk_analysis,
                         risk_app=[app.name])
            risk.metadata_file = excel_metadata_file

        # Finalize
        risk.data_file = excel_file
        if commit:
            risk.save()

        return risk_analysis

    def get_db_conn(self, db_name, db_user, db_port, db_host, db_passwd):
        """Get db conn (GeoNode)"""
        db_host = db_host if db_host is not None else 'localhost'
        db_port = db_port if db_port is not None else 5432
        conn = psycopg2.connect(
            "dbname='%s' user='%s' port='%s' host='%s' password='%s'" % (db_name, db_user, db_port, db_host, db_passwd)
        )
        return conn

    def insert_db(self, conn, values):
        """Remove spurious records from GeoNode DB"""
        curs = conn.cursor()

        insert_template = """INSERT INTO {table} (
                          the_geom,
                          risk_analysis, hazard_type,
                          admin, adm_code,
                          region)
                  SELECT '{the_geom}',
                          '{risk_analysis}', '{hazard_type}',
                          '{admin}', '{adm_code}',
                          '{region}'
                  WHERE
                  NOT EXISTS (SELECT fid FROM {table} WHERE
                    risk_analysis = '{risk_analysis}' AND
                    hazard_type = '{hazard_type}' AND
                    admin = '{admin}' AND
                    adm_code = '{adm_code}' AND
                    region = '{region}')
                  RETURNING fid;"""

        curs.execute(insert_template.format(**values))
        id_of_new_row = curs.fetchone()
        next_table_fid = None
        if id_of_new_row:
            next_table_fid = id_of_new_row[0]
        else:
            next_table_fid = None

        if next_table_fid is None:
            select_template = """SELECT fid FROM {table} WHERE
                    risk_analysis = '{risk_analysis}' AND
                    hazard_type = '{hazard_type}' AND
                    admin = '{admin}' AND
                    adm_code = '{adm_code}' AND
                    region = '{region}'"""

            curs.execute(select_template.format(**values))
            id_of_new_row = curs.fetchone()
            if id_of_new_row:
                next_table_fid = id_of_new_row[0]
            else:
                raise CommandError("Could not find any suitable Risk Analysis on target DB!")

        dim_ids = {
            'fid': next_table_fid,
            'table': values['table'],
            'value': values['value']
        }
        for dim_idx in range(1, 6):
            dim_col = 'dim{}'.format(dim_idx)
            dim_order = 'dim{}_order'.format(dim_idx)
            if values[dim_col]:
                values['dim_col'] = dim_col
                values['dim_order'] = values[dim_order]
                values['dim_value'] = values[dim_col]
                insert_dimension_template = "INSERT INTO public.dimension(dim_col, dim_value, dim_order) " +\
                                            "SELECT %(dim_col)s, %(dim_value)s, %(dim_order)s " +\
                                            "WHERE NOT EXISTS " +\
                                            "(SELECT dim_id FROM public.dimension " +\
                                            "WHERE dim_col = %(dim_col)s AND dim_value = %(dim_value)s) " +\
                                            "RETURNING dim_id;"

                curs.execute(insert_dimension_template.format(**values), values)
                id_of_new_row = curs.fetchone()
                next_dim_id = None
                if id_of_new_row:
                    next_dim_id = id_of_new_row[0]

                if next_dim_id is None:
                    select_dimension_template = "SELECT dim_id FROM public.dimension " +\
                        "WHERE dim_col = %(dim_col)s AND dim_value = %(dim_value)s;"


                    curs.execute(select_dimension_template.format(**values), values)
                    id_of_new_row = curs.fetchone()
                    if id_of_new_row:
                        next_dim_id = id_of_new_row[0]
                    else:
                        raise CommandError("Could not find any suitable Dimension on target DB!")

                dim_ids[dim_col] = next_dim_id
            else:
                dim_ids[dim_col] = 'NULL'

        insert_dimension_value_template = "INSERT INTO {table}_dimensions({table}_fid, dim1_id, dim2_id, dim3_id, dim4_id, dim5_id, value) " +\
                                          "SELECT {fid}, {dim1}, {dim2}, {dim3}, {dim4}, {dim5}, '{value}' " +\
                                          "WHERE NOT EXISTS (SELECT {table}_fid FROM public.{table}_dimensions WHERE " +\
                                          " {table}_fid = {fid} AND " +\
                                          " (dim1_id IS NULL OR dim1_id = {dim1}) AND " +\
                                          " (dim2_id IS NULL OR dim2_id = {dim2}) AND " +\
                                          " (dim3_id IS NULL OR dim3_id = {dim3}) AND " +\
                                          " (dim4_id IS NULL OR dim4_id = {dim4}) AND " +\
                                          " (dim5_id IS NULL OR dim5_id = {dim5}) " +\
                                          ") RETURNING {table}_fid;"
        curs.execute(insert_dimension_value_template.format(**dim_ids))
