/*global $:true, requirejs: true, define: true, module: true, test: true, ok:true, strictEqual:true */
'use strict';
requirejs.config({
    baseUrl: 'js/',

    paths: {
        underscore: '../libs/underscore',
        jquery: '../../libs/js/jquery'
    }
});

define(function (require) {

    var FileType      = require('upload/FileType'),
        FileTypes     = require('upload/FileTypes'),
        LayerInfo     = require('upload/LayerInfo'),
        UploadSession = require('status/UploadSession'),
        getBase       = require('upload/path').getBase,
        getExt        = require('upload/path').getExt,
        getName       = require('upload/path').getName;



    module('Test correctly splitting the file name');
    test('That layer names without an extension are correctly parsed', function () {
        var n1 = {name: 'test.shp'},
            n2 = {name: 'test'},
            awfulName = {name: 'This --- []is .an awful.shp.shpfile.shp'};


        ok(getBase(n1), 'Make sure getBase works with name with an extension');

        strictEqual(
            getBase(n2)[0],
            'test',
            'Make sure getBase works with names without an extension'
        );

        strictEqual(
            getBase({name: 'thingaf [(.shp'})[0],
            'thingaf [(',
            'Make sure that the getBase function can handle file names with strange chars'
        );

        strictEqual(
            getExt({name: 'name.shp'}),
            'shp',
            'Make sure that getExt works with names with an extension'
        );

        strictEqual(
            getExt({name: 'name'}),
            null,
            'Make sure that getExt works with a file without an extension'
        );


        strictEqual(
            getExt({name: 'name.SHP'}),
            'shp',
            'Make sure case does not matter'
        );

        strictEqual(
            getExt(awfulName),
            'shp',
            'Make sure getExt (get extension) works on a poor file name'
        );

        strictEqual(
            getName(awfulName),
            'This --- []is .an awful.shp.shpfile',
            'Make sure getName (get name) works on a poor file name'
        );

        strictEqual(
            getName({name: 'File Name without extension'}),
            'File Name without extension',
            'Make sure that file names without extensions work'
        );



    });


    module('FileType');
    test('if FileType class works', function () {
        var type = new FileType({
            name: 'Test type',
            main: 'test',
            requires: ['test']
        });

        ok(type instanceof FileType, 'Make sure the FileType constructor returns the correct type');

        strictEqual(
            type.isType({name: 'this-is-not.ls'}),
            false,
            'Make sure the type can check files that are not its type'
        );

        strictEqual(
            type.isType({name: 'this-is.test'}),
            true,
            'Make sure the type can correctly identify its own type'
        );

        strictEqual(
            type.findTypeErrors(['test']).length,
            0,
            'Make sure no errors are returned for the correct type'
        );

    });



    module('LayerInfo');
    test('Make sure that the file selector is safe', function () {
        var unSafe = '[a](b)';
        strictEqual(
            LayerInfo.safeSelector(unSafe),
            '_a__b_'
        );
    });

    test('LayerInfo should work on a valid shapefile', function () {
        var shpInfo = new LayerInfo({
            name: 'nybb',
            files: [{name: 'nybb.shp'}, {name: 'nybb.dbf'}, {name: 'nybb.prj'}, {name: 'nybb.shx'}]
        }),
            res = {},
            errors,
            mock_form_data = {append: function (key, value) { res[key] = value; }};

        strictEqual(
            shpInfo instanceof LayerInfo,
            true,
            'The constructor should return the correct type'
        );

        shpInfo.prepareFormData(mock_form_data);
        $.each(['base_file', 'permissions', 'prj_file', 'dbf_file', 'shx_file'], function (i, thing) {
            strictEqual(res.hasOwnProperty(thing), true, 'Do we have a ' + thing + ' ?');
        });

        strictEqual(shpInfo.type, FileTypes.SHP, 'Should be the correct file type');
        strictEqual(shpInfo.files.length, 4, 'Should have the correct amount of associated files');

        shpInfo.removeFile('nybb.dbf');
        strictEqual(shpInfo.files.length, 3, 'Should correctly remove an associated file');
        errors = shpInfo.collectErrors();
        strictEqual(errors.length, 1, 'Should build the errors when need');


    });

    module('Layer Info of unknown type');
    test('The LayerInfo object on an unknown type', function () {
        var unknownType = new LayerInfo({
            name: 'pdf',
            files: [{name: 'test.pdf'}]
        });

        strictEqual(unknownType instanceof LayerInfo, true);
        strictEqual(unknownType.errors.length, 1, 'Should return one error');

    });

    // can we roll this into a single test case?
    // module('LayerInfo csv file');
    // test('The LayerInfo type on a CSV file', function () {
    //     var csvInfo = new LayerInfo({
    //         name: 'test-csv',
    //         files: [{name: 'test.csv'}]
    //     });
    //     strictEqual(csvInfo instanceof LayerInfo, true, 'Should return the correct class');
    //     strictEqual(csvInfo.type, FileTypes.CSV, 'Should return the correct type');
    //     strictEqual(csvInfo.errors.length, 0, 'Should return no errors');

    // });

    module('LayerInfo Tiff');
    test('The LayerInfo type on a Tiff file', function () {
        var tifInfo = new LayerInfo({name: 'test-tif', files: [{name: 'test.tif'}]});
        strictEqual(tifInfo instanceof LayerInfo, true, 'Should return the correct class');
        strictEqual(tifInfo.type, FileTypes.TIF, 'Should return the correct file type');
        strictEqual(tifInfo.errors.length, 0, 'Should return no errors');
    });

    // module('LayerInfo Zip');
    // test('The LayerInfo type on a Zip file', function () {
    //     var tifInfo = new LayerInfo({name: 'test-zip', files: [{name: 'test.zip'}]});
    //     strictEqual(tifInfo instanceof LayerInfo, true, 'Should return the correct class');
    //     strictEqual(tifInfo.type, FileTypes.ZIP, 'Should return the correct file type');
    //     strictEqual(tifInfo.errors.length, 0, 'Should return on errors');
    // });

    module('Upload Session');
    test('The UploadSession should be able', function () {
        var ses = new UploadSession({
            name: 'test session',
            id: 1,
            layer_name: 'test',
            layer_id: 1,
            state: 'PEDDING',
            url: '',
            date: 'Date',
        });
        strictEqual(ses instanceof UploadSession, true, 'Should return the correct class');

    });

    // describe('The UploadSession should be able', function () {

    //     it('Should return the correct class', function () {
    //         expect(ses instanceof UploadSession).toBeTruthy();
    //     });

    // });

});
