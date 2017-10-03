mapModule.factory('SurfFeature', ['attributeTypes', 'fidColumnName', 'imageColumnName', 'imageUrlRoot', 'imageFileExtension',
    function (attributeTypes, fidColumnName, imageColumnName, imageUrlRoot, imageFileExtension) {
        function SurfFeature(wrappedFeature, surfLayer) {
            var _thisFeature = this;

            var _lastAttributeUpdateTime = new Date(0);
            var _attributesWithType = [];
            var _images = [];
            var _attributeChanged = false;

            this.layer = surfLayer;

            this.getFid = function () {
                return wrappedFeature.getProperties()[fidColumnName];
            };

            this.setFid = function (fid) {
                var fidObject = {};
                fidObject[fidColumnName] = fid;
                wrappedFeature.setProperties(fidObject);
            };

            this.clone = function () {
                var clonedWrapped = wrappedFeature.clone();
                var clone = new SurfFeature(clonedWrapped, _thisFeature.layer);
                clone.setFid(_thisFeature.getFid());
                return clone;
            };

            function setAttributeValue(id, value) {
                if (id) {
                    wrappedFeature.attributes[id] = value;

                    for (var i in _attributesWithType) {
                        if (_attributesWithType[i].id == id) {
                            _attributesWithType[i].value = value;
                            break;
                        }
                    }
                }
            }

            function hasAttributes() {
                return !!wrappedFeature.attributes;
            }

            function getCoordinates() {
                var openLayerVerices = wrappedFeature.geometry.getVertices();

                return openLayerVerices;
            }

            this.isAttributesChanged = function () {
                if (!_thisFeature.hasAttributes()) {
                    return false;
                }
                if (_attributeChanged) {
                    _attributeChanged = false;
                    return true;
                }

                for (var i in _attributesWithType) {
                    var aAndT = _attributesWithType[i];
                    if (aAndT.value != getAttributes()[aAndT.id]) {
                        return true;
                    }
                }

                return false;
            };

            this.setAttributeChanged = function () {
                _attributeChanged = true;
            };

            this.setGeometry = function (geometry) {
                wrappedFeature.geometry = geometry;
            };

            this.isVisible = function () {
                return wrappedFeature.getVisibility();
            };

            function clearAttributes() {
                setAttributesWithType([]);
                _lastAttributeUpdateTime = undefined;
            }

            this.requiresAttributeLoad = function () {
                return !hasAttributes() ||
                    (_thisFeature.layer.getLastAttributeDefinitionUpdateTime() > _lastAttributeUpdateTime);
            };

            this.getAttributeValue = function (id) {
                return wrappedFeature.attributes[id];
            };

            this.setAttributeValue = setAttributeValue;

            this.addImages = function (imageIds) {
                for (var i in imageIds) {
                    _images.push(getImageObject(imageIds[i]));
                }
                var imagesString = wrappedFeature.getProperties()[imageColumnName];
                imagesString = [imagesString, imageIds.join(',')].join(',');
                var imageNameProperty = {};
                imageNameProperty[imageColumnName] = imagesString;
                wrappedFeature.setProperties(imageNameProperty);
            };

            function setImages() {
                var imagesString = wrappedFeature.getProperties()[imageColumnName];
                var imageIds = imagesString ? imagesString.split(',') : [];

                var images = imageIds.map(getImageObject);
                _images.length = 0;

                for (var i in images) {
                    _images.push(images[i]);
                }
            }

            function getImageObject(item) {
                var name = item.split(';');
                var type = getTypeFromExt(name[0]);
                var url = imageUrlRoot + name[0];
                return {
                    id: item,
                    url: getPreviewImageFromType(type, imageUrlRoot, url),
                    type: type,
                    link: url,
                    oname: name[1]
                };
            }

            function getPreviewImageFromType(type, imageUrlRoot, url) {
                if (type === "image") {
                    return url;
                }
                else if (type === "audio/video") {
                    return imageUrlRoot + "/previewVideoFile.png";
                } else {
                    return imageUrlRoot + "/previewOtherFile.png";

                }
            }

            function getTypeFromExt(name) {
                var re = /(?:\.([^.]+))?$/;
                var ext = re.exec(name)[1];
                switch (ext) {
                    case "jpeg":
                    case "jpg":
                    case "png":
                    case "gif":
                        return "image";
                    case "avi":
                    case "megp":
                    case "mp3":
                    case "mp4":
                        return "audio/video";
                    default:
                        return "document/other";

                }
            }

            this.removeImage = function (image) {
                _images = _.without(_images, image);
                var imagesString = wrappedFeature.getProperties()[imageColumnName];
                imagesString = _.without(imagesString.split(','), image.id).join(',');
                var imageNameProperty = {};
                imageNameProperty[imageColumnName] = imagesString;
                wrappedFeature.setProperties(imageNameProperty);
                setImages();
            };

            this.getImages = function () {
                return _images;
            };

            this.getFeatureType = function () {
                return _thisFeature.layer.getFeatureType();
            };

            this.hasAttributes = hasAttributes;
            function getAttributes() {
                return wrappedFeature.attributes;
            };

            this.getAttributes = getAttributes;

            this.getAttributesWithType = function () {
                return _attributesWithType;
            };

            function setAttributesWithType(attributesWithType) {
                _attributesWithType = attributesWithType;
                _thisFeature.updateAttributes();
            };

            this.updateAttributes = function () {
                _lastAttributeUpdateTime = new Date();

                var attributes = {};
                for (var i in _attributesWithType) {
                    var aAndT = _attributesWithType[i];
                    var typedValue = attributeTypes.toTypedValue(aAndT.type, aAndT.value);
                    attributes[aAndT.id] = typedValue;
                    aAndT.value = typedValue;
                }

                wrappedFeature.attributes = attributes;
            };

            this.setAttributes = function (attributes) {
                attributes = attributes || {};
                var attributesWithType = [];
                var attrDef = _thisFeature.layer.getAttributeDefinition();

                for (var i in attrDef) {
                    var def = attrDef[i];
                    attributesWithType.push({
                        id: def.Id,
                        name: def.Name,
                        type: def.Type,
                        value: attributes[def.Id],
                        unit: _thisFeature.layer.LinearUnit,
                        precision: def.Precision,
                        scale: def.Scale,
                        length: def.Length,
                        isPublished: def.IsPublished
                    });
                }

                setAttributesWithType(attributesWithType);
            };
            this.setAttributes(wrappedFeature.getProperties());
            _lastAttributeUpdateTime = new Date(0);
            this.clearAttributes = clearAttributes;
            this.getCoordinates = getCoordinates;
            this.getWkt = function () {
                return new ol.format.WKT().writeFeature(wrappedFeature);
            };
            this.redoList = [];
            this.undoList = [];
            this.reloadImages = setImages;
            // TODO: Implement strategy. Remove conditions
            this.isValid = function () {
                if (!wrappedFeature.getGeometry()) {
                    return false;
                }

                var verticeCount;
                switch (_thisFeature.getFeatureType()) {
                    case "point":
                        return true;
                    case "polyline":
                        verticeCount = wrappedFeature.getGeometry().getCoordinates().length;
                        return verticeCount >= 2;
                    case "polygon":
                        verticeCount = wrappedFeature.getGeometry().getCoordinates()[0].length;
                        return verticeCount >= 3;
                    default:
                        return false;
                }
            };

            setImages();
        };

        return SurfFeature;
    }
]);

