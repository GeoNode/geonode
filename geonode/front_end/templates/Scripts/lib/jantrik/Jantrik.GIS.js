window.Jantrik = window.Jantrik || {};
(function (GIS, undefined) {
    var ShapeTypes = {
        0: 'Null',
        1: 'Point',
        3: 'Polyline',
        5: 'Polygon',
        8: 'MultiPoint',
        11: 'PointZ',
        13: 'PolyLineZ',
        15: 'PolygonZ',
        18: 'MultiPointZ',
        21: 'PointM',
        23: 'PolyLineM',
        25: 'PolygonM',
        28: 'MultiPointM',
        31: 'MultiPatch'
    };

    GIS.readShpHeader = function (shpOrShx, onload) {

        shpOrShx.vendorSlice = shpOrShx.slice || shpOrShx.webkitSlice || shpOrShx.mozSlice;
        var headerBlob = shpOrShx.vendorSlice(0, 100);

        var reader = new window.FileReader();
        reader.onload = function () {
            onload(reader.result);
        };
        reader.readAsArrayBuffer(headerBlob);
    };

    GIS.ShapeFileHeader = function (arrayBuffer) {
        var _fileData = new window.DataView(arrayBuffer, 0);
        var _shapeType;
        var _boundingBox;
        var _fileCode;
        var _fileLength;
        var _version;

        function getFileCode() {
            _fileCode = _fileCode != undefined ? _fileCode : _fileData.getInt32(0, false);
            if (_fileCode != 9994) {
                throw (new Error("Unknown file code: " + _fileCode));
            }
            return _shapeType;
        }

        function getShapeTypeCode() {
            _shapeType = _shapeType != undefined ? _shapeType : _fileData.getInt32(32, true);
            return _shapeType;
        }

        function getFileLength() {
            _fileLength = _fileLength != undefined ? _fileLength : _fileData.getInt32(24, false);
            return _fileLength << 1;
        }

        function getVersion() {
            _version = _version != undefined ? _version : _fileData.getInt32(28, true);
            return _version;
        }

        function getShapeType() {
            return ShapeTypes[getShapeTypeCode()];
        }


        function getBoundingBox() {
            _boundingBox = _boundingBox || readBoundingBox();
            return _boundingBox;
        }

        function readBoundingBox() {
            var boundingBox = {};

            boundingBox.xMin = _fileData.getFloat64(36, true);
            boundingBox.yMin = _fileData.getFloat64(44, true);
            boundingBox.xMax = _fileData.getFloat64(52, true);
            boundingBox.yMax = _fileData.getFloat64(60, true);
            boundingBox.zMin = _fileData.getFloat64(68, true);
            boundingBox.zMax = _fileData.getFloat64(76, true);
            boundingBox.mMin = _fileData.getFloat64(84, true);
            boundingBox.mMax = _fileData.getFloat64(92, true);

            return boundingBox;
        }

        this.getBoundingBox = getBoundingBox;
        this.getShapeType = getShapeType;
        this.getVersion = getVersion;
        this.getFileLength = getFileLength;
        this.getShapeTypeCode = getShapeTypeCode;
        this.getFileCode = getFileCode;
    };

    GIS.ShapeFile = function (shpFile) {

        this.shpFile = shpFile;
        var _header;

        function getHeader(callBack) {
            if (!_header) {
                GIS.readShpHeader(shpFile, function (resultBuffer) {
                    _header = new GIS.ShapeFileHeader(resultBuffer);
                    callBack(_header);
                });
            } else {
                callBack(_header);
            }
        }

        function isMultipart(callBack) {

            var _fileLength;

            GIS.readShpHeader(shpFile, function () {
                getHeader(function (header) {
                    switch (_header.getShapeTypeCode()) {
                        case 3:
                        case 5:
                            _fileLength = header.getFileLength();
                            checkRecordIsMultipart(100);
                            break;
                        default:
                            callBack(false);
                            break;
                    }
                });
            });

            function checkRecordIsMultipart(rhs) {
                var _numPartsByteStart;

                getStreamOfBlob(rhs, rhs + 48, function (buffer) {
                    var _fileData = new window.DataView(buffer, 0);
                    var _contentLength = _fileData.getInt32(4, false) << 1;

                    _numPartsByteStart = 44;
                    var _numParts = _fileData.getInt32(_numPartsByteStart, true);
                    if (_numParts > 1) {
                        callBack(true);
                    } else {
                        var nextRHS = rhs + 8 + _contentLength;
                        if (nextRHS < _fileLength) {
                            checkRecordIsMultipart(nextRHS);
                        } else {
                            callBack(false);
                        }
                    }
                });
            }
        }

        function getStreamOfBlob(start, end, callBack) {
            var blob = shpFile.slice(start, end);
            var reader = new window.FileReader();
            reader.onload = function () {
                callBack(reader.result);
            };
            reader.readAsArrayBuffer(blob);
        }

        this.isMultipart = isMultipart;
        this.getHeader = getHeader;
    }
}(window.Jantrik.GIS = window.Jantrik.GIS || {}));