#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute("select layer_id, attribute, description, attribute_label, attribute_type, visible, display_order, count, min, max, average, median, stddev, sum, unique_values, last_stats_updated from layers_attribute a join layers_layer l on a.layer_id = l.resourcebase_ptr_id")

dst_cur.execute("delete from layers_attribute")

for src_row in src_cur:
    assignments = []
    #layer_id
    assignments.append(utils.get_resourceid_by_oldid(src_row[0]))
    #attribute
    assignments.append(src_row[1])
    #description
    assignments.append(src_row[2])
    #attribute_label
    assignments.append(src_row[3])
    #attribute_type
    assignments.append(src_row[4])
    #visible
    assignments.append(src_row[5])
    #display_order
    assignments.append(src_row[6])
    #count
    assignments.append(src_row[7])
    #min
    assignments.append(src_row[8])
    #max
    assignments.append(src_row[9])
    #average
    assignments.append(src_row[10])
    #median
    assignments.append(src_row[11])
    #stddev
    assignments.append(src_row[12])
    #sum
    assignments.append(src_row[13])
    #unique_values
    assignments.append(src_row[14])
    #last_stats_updated
    assignments.append(src_row[15])

    try:
        print assignments
        dst_cur.execute("insert into layers_attribute(layer_id, attribute, description, attribute_label, attribute_type, visible, display_order, count, min, max, average, median, stddev, sum, unique_values, last_stats_updated) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print 
        print type(error)
        print str(error) + "layer_id, attribute, description, attribute_label, attribute_type, visible, display_order, count, min, max, average, median, stddev, sum, unique_values, last_stats_updated from layers_attribute"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
