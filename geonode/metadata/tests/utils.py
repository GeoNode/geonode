from unittest.mock import MagicMock

# Mock subhandler class
class MockSubHandler:

    @classmethod
    def update_subschema(cls, subschema, lang=None):
        subschema["oneOf"] = [
            {"const": "fake const", "title": "fake title"}
        ]

    @classmethod
    def serialize(cls, db_value):
        if isinstance(db_value, MagicMock):
            return db_value.identifier
        return db_value
    
    @classmethod
    def deserialize(cls, field_value):
        return MagicMock.objects.get(identifier=field_value)