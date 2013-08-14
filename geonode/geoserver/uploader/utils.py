from zipfile import ZipFile
import tempfile
from os import path
    
def create_zip(fpaths):
    _,payload = tempfile.mkstemp(suffix='.zip')
    zipf = ZipFile(payload,"w")
    for fp in fpaths:
            basename = path.basename(fp)
            zipf.write(fp,basename)
    zipf.close()
    return payload
