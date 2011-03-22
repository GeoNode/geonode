from django.conf import settings # import the settings file


def custom_group_name(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'CUSTOM_GROUP_NAME': settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else ''}
