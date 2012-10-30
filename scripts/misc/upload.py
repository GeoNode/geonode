import os, sys
import boto
from boto.s3.key import Key

bucket_name = sys.argv[1] 
file_name = sys.argv[2] 

conn = boto.connect_s3(os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
bucket = conn.get_bucket(bucket_name)

k = Key(bucket)
k.key = file_name.split('/')[-1]
k.set_contents_from_filename(file_name)
k.set_acl('public-read')

print file_name + " uploaded to " + bucket_name
