#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()
 
src_cur = src.cursor()
dst_cur = dst.cursor()

dst_cur.execute('DELETE from base_resourcebase;')    

def migrate_resourcebase(resource_type):

    sql = "select uuid, owner_id, title, date, date_type, edition, abstract, purpose, maintenance_frequency, restriction_code_type_id, constraints_other, language, category_id, spatial_representation_type_id, temporal_extent_start, temporal_extent_end, supplemental_information, distribution_url, distribution_description, data_quality_statement, bbox_x0, bbox_x1, bbox_y0, bbox_y1, srid, csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry, metadata_uploaded, metadata_xml, thumbnail_id from base_resourcebase"
    
    if resource_type == 'layer':
        sql = sql + ' where id in (select resourcebase_ptr_id from layers_layer)'
    if resource_type == 'map':
        sql = sql + ' where id in (select resourcebase_ptr_id from maps_map)'
    if resource_type == 'document':
        sql = sql + ' where id in (select resourcebase_ptr_id from documents_document)'

    polymorphic_ctype_id = utils.get_content_type_id(resource_type)

    src_cur.execute(sql)

    for src_row in src_cur:
        assignments = []
        #polymorphic_ctype_id
        assignments.append(polymorphic_ctype_id)
        #uuid
        uuid = src_row[0]
        assignments.append(uuid)
        #owner_id
        assignments.append(utils.get_userid_by_oldid(src_row[1]))
        #title
        title = src_row[2]
        assignments.append(title)
        #date
        assignments.append(src_row[3])
        #date_type
        assignments.append(src_row[4])
        #edition
        assignments.append(src_row[5])
        #abstract
        assignments.append(src_row[6])
        #purpose
        assignments.append(src_row[7])
        #maintenance_frequency
        assignments.append(src_row[8])
        #restriction_code_type_id
        # TODO we need to make sure we use the correct id
        assignments.append(src_row[9])
        #constraints_other
        assignments.append(src_row[10])
        #license_id
        # TODO we need to make sure we use the correct id
        assignments.append(None)
        #language
        assignments.append(src_row[11])
        #category_id
        assignments.append(utils.get_categoryid_by_oldid(src_row[12]))
        # TODO we need to make sure we use the correct id
        #spatial_representation_type_id
        assignments.append(utils.get_spatrepid_by_oldid(src_row[13]))
        #temporal_extent_start
        assignments.append(src_row[14])
        #temporal_extent_end
        assignments.append(src_row[15])
        #supplemental_information
        assignments.append(src_row[16])
        #distribution_url
        assignments.append(src_row[17])
        #distribution_description
        assignments.append(src_row[18])
        #data_quality_statement
        assignments.append(src_row[19])
        #bbox_x0
        assignments.append(src_row[20])
        #bbox_x1
        assignments.append(src_row[21])
        #bbox_y0
        assignments.append(src_row[22])
        #bbox_y1
        assignments.append(src_row[23])
        #srid
        assignments.append(src_row[24])
        #csw_typename
        assignments.append(src_row[25])
        #csw_schema
        assignments.append(src_row[26])
        #csw_mdsource
        assignments.append(src_row[27])
        #csw_insert_date
        assignments.append(src_row[28])
        #csw_type
        assignments.append(src_row[29])
        #csw_anytext
        assignments.append(src_row[30])
        #csw_wkt_geometry
        assignments.append(src_row[31])
        #metadata_uploaded
        assignments.append(src_row[32])
        #metadata_xml
        assignments.append(src_row[33])
        #popular_count, share_count
        attributes = utils.get_attributes_by_uuid(uuid, resource_type)
        assignments.append(attributes[0])
        assignments.append(attributes[1])
        #featured TODO update it later
        assignments.append(False)
        #is_published
        assignments.append(False)
        #thumbnail_url
        assignments.append(None)
        #detail_url
        assignments.append(None)
        #rating TODO update it later
        assignments.append(None)

        try:
            print 'Migrating %s %s' % (resource_type, title)
            dst_cur.execute("insert into base_resourcebase(polymorphic_ctype_id, uuid, owner_id, title, date, date_type, edition, abstract, purpose, maintenance_frequency, restriction_code_type_id, constraints_other, license_id, language, category_id, spatial_representation_type_id, temporal_extent_start, temporal_extent_end, supplemental_information, distribution_url, distribution_description, data_quality_statement, bbox_x0, bbox_x1, bbox_y0, bbox_y1, srid, csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry, metadata_uploaded, metadata_xml, popular_count, share_count, featured, is_published, thumbnail_url, detail_url, rating) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
            dst.commit()
        except Exception as error:
            print 
            print type(error)
            print str(error) + "select uuid, owner_id, title, date, date_type, edition, abstract, purpose, maintenance_frequency, restriction_code_type_id, constraints_other, language, category_id, spatial_representation_type_id, temporal_extent_start, temporal_extent_end, supplemental_information, distribution_url, distribution_description, data_quality_statement, bbox_x0, bbox_x1, bbox_y0, bbox_y1, srid, csw_typename, csw_schema, csw_mdsource, csw_insert_date, csw_type, csw_anytext, csw_wkt_geometry, metadata_uploaded, metadata_xml, thumbnail_id from base_resourcebase"
            dst.rollback()

migrate_resourcebase('layer')
migrate_resourcebase('map')
migrate_resourcebase('document')

src_cur.close()
dst_cur.close()
src.close()
dst.close()
