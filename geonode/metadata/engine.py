from abc import abstractmethod
from typing import List, Optional
from rest_framework import serializers


class Field(object):
    """
    Field object used to convert the metadata into a
    serializer field For example:
    Field(
        name="title", # mandatory
        type="int", # mandatory
        kwargs={ # optional
            "max_length": 255,
            "help_text": "name by which the cited resource is known"
        }
    )
    """

    def __init__(self, name: str, type: str, kwargs: dict = {}) -> None:
        self.name = name
        self.type = type
        self.kwargs = kwargs


class MetadataEngine:
    """
    Abstract base class for the metadata engine or its concrete implementation
    All the method decorated as @abstractmethod should be overwritten
    by the concrete implementation
    """

    def get_engine_lists(self) -> List:
        """
        Returns the list of the metadata engine registered
        """

    @abstractmethod
    def validate_fields(self) -> bool:
        """
        Should perform some basic validation steps like:
        - duplicated fields
        - ordering of the metadata handlers
        - input validation from the concrete handlers
        """

    @abstractmethod
    def get_fields(self) -> List[Field]:
        """
        Returns the list of the field
        """

    @abstractmethod
    def get_data(self) -> List[dict]:
        """
        Return the list of the metadata to be used in the
        serializer listing functionality
        """
        # return [{"title": "abc"}]

    @abstractmethod
    def get_data_by_pk(self, pk) -> List[dict]:
        """
        Return the dict of the metadata to be used in the
        serializer listing functionality for a specific resource
        """
        # return {"title": pk, "name": "this is my name"}

    @abstractmethod
    def save_metadata(self, payload):
        """
        create the metadata
        """

    @abstractmethod
    def set_metadata(self, payload, pk):
        """
        Create the metadata for a specific resource
        """
        # return pk


class FieldsConverter:
    """
    Class with take care of converting the field returned by the metadata
    into a serializer-like object. The example in the metadata field should
    converted into something like the following:
    "title": serializers.CharField(max_lenght=250, help_text="name by which the cited resource is known")
    """

    MAPPING = {"int": serializers.IntegerField, "str": serializers.CharField, "choice": serializers.ChoiceField}

    def convert_fields(self, input_fields=list, bind: bool = True) -> List[dict]:
        """
        Convert the input coming from the metadata engine into a serializerLike object
        input_fields = {
            "title": serializers.CharField(
                max_length=255, help_text="name by which the cited resource is known"
            ),
            "name": serializers.CharField(
                max_length=255, help_text="name by which the cited resource is known", required=False
            )
        }
        """

        output_fileds = {}
        for field in input_fields:
            # getting field object
            output_fileds[field.name] = self.MAPPING.get(field.type)(**field.kwargs)

        self.validate(output_fileds)
        if bind and output_fileds:
            output_fileds = self.bind_fileld(output_fileds)

        return output_fileds

    def bind_fileld(self, fields: list) -> Optional[None]:
        # since the fields are dynamic, we need to bind the field
        # to the serializer
        for x, y in fields.items():
            y.bind(x, None)
        return fields

    def validate(self, converted_fields=list) -> list[dict]:
        """
        Helps to validate each converted field like:
        - some attributes are mandatory so we have to enforce it, otherwise we can add a default
        - if one of the kwargs is not in the field attribute, we just discard it
        """


engine = MetadataEngine()
