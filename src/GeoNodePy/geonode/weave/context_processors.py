from django.conf import settings

def weave_media(context):
	# return WEAVE settings
	return {
		'WEAVE_URL': settings.WEAVE_URL
	}