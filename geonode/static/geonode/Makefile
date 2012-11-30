GEONODE_LESS = less/base.less
CSS_OUTPUT_FILENAME = css/base.css
LESS_COMPRESSOR ?= `which lessc`

#
# BUILD SITE MEDIA
# lessc is required
#

build:
	lessc --yui-compress ${GEONODE_LESS} > ${CSS_OUTPUT_FILENAME}
