# DOCUMENT_TYPE_MAP and DOCUMENT_MIMETYPE_MAP
# match values in settings.ALLOWED_DOCUMENT_TYPES

DOCUMENT_TYPE_MAP = {
    'txt': 'text',
    'log': 'text',
    'doc': 'text',
    'docx': 'text',
    'ods': 'text',
    'odt': 'text',
    'sld': 'text',
    'xls': 'text',
    'xlsx': 'text',
    'xml': 'text',

    'gif': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'tif': 'image',
    'tiff': 'image',

    'odp': 'presentation',
    'ppt': 'presentation',
    'pptx': 'presentation',
    'pdf': 'presentation',

    'rar': 'archive',
    'gz': 'archive',
    'zip': 'archive',
}


DOCUMENT_MIMETYPE_MAP = {
    'txt': 'text/plain',
    'log': 'text/plain',
    'doc': 'text/plain',
    'docx': 'text/plain',
    'ods': 'text/plain',
    'odt': 'text/plain',
    'sld': 'text/plain',
    'xls': 'text/plain',
    'xlsx': 'text/plain',
    'xml': 'text/xml',

    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',

    'odp': 'text/plain',
    'ppt': 'text/plain',
    'pptx': 'text/plain',
    'pdf': 'application/pdf',

    'rar': 'application/x-rar-compressed',
    'gz': 'application/x-gzip',
    'zip': 'application/zip',
}
