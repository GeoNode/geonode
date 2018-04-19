# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
