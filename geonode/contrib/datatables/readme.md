# Using curl to test the api

## Test upload_lat_lon

curl -u admin:admin -X POST -F 'title=test_latlong_upload' -F 'abstract=abstract' -F 'delimiter="\t"' -F 'lng_attribute=longitude' -F 'lat_attribute=latitude' -F 'uploaded_file=@coded_data_2007_09.txt' http://192.168.33.16:8000/datatables/api/upload_lat_lon
