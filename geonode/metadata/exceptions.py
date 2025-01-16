class MetadataFieldException(Exception):
    pass


class UnsetFieldException(MetadataFieldException):
    pass


class UnparsableFieldException(MetadataFieldException):
    pass
