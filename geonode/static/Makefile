SHELL := /bin/bash
NODE_PATH = $(shell ./find-node-or-install)
PATH := $(NODE_PATH):$(shell echo $$PATH)


all: install css js

install:
	npm install

css:
	less geonode/less/base.less >> geonode/css/base.css
	less geonode/less/activity.less >> geonode/css/activity.css
	less geonode/less/bootstrap.less >> geonode/css/bootstrap.css
	less geonode/less/grayscale.less >> geonode/css/grayscale.css

js:
	bower install
	grunt copy

.PHONY: all clean
