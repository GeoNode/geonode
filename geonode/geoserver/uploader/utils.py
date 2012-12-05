from zipfile import ZipFile
import tempfile
from os import path

_shp_exts = ["dbf","prj","shx"]
_shp_exts = _shp_exts + map(lambda s: s.upper(), _shp_exts)

def shp_files(fpath):
    basename, ext = path.splitext(fpath)
    paths = [ "%s.%s" % (basename,ext) for ext in _shp_exts ]
    paths.append(fpath)
    return filter(lambda f: path.exists(f),  paths)
    
def create_zip(fpaths):
    _,payload = tempfile.mkstemp(suffix='.zip')
    zipf = ZipFile(payload,"w")
    for fp in fpaths:
            basename = path.basename(fp)
            zipf.write(fp,basename)
    zipf.close()
    return payload
