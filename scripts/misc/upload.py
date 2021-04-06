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

import os.path
import sys
import boto3
import botocore


def upload_file_s3(filename, bucket, obj_name=None):
    """Upload a file to an S3 bucket

    :param filename: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified, filename is used
    :return None if upload was successful, otherwise the associated error code
    """

    if obj_name is None:
        obj_name = filename

    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(filename, bucket, obj_name)
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        return error_code

    return None


if __name__ == '__main__':
    try:
        _, bucket_name, filepath = sys.argv
    except ValueError:
        print(f"Usage:\n    python {sys.argv[0]} bucket_name filepath")

    filename = os.path.basename(filepath)
    error = upload_file_s3(filepath, bucket_name)

    if error is not None:
        print(f"{filename} failed uploading to {bucket_name} with error {error}")
    else:
        print(f"{filename} uploaded to {bucket_name}")
