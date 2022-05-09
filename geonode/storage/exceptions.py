from rest_framework.exceptions import APIException


class DataRetrieverExcepion(APIException):
    status_code = 500
    default_detail = "Error during the data retrieveing"
    default_code = "data_retriever_exception"
    category = 'data_retriever_exception'
