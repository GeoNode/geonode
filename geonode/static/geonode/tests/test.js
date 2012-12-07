/*global $:true, requirejs: true, define: true, module: true, test: true, ok:true, strictEqual:true */

requirejs.config({
    baseUrl: 'js/',
    paths: {
        underscore: '../libs/underscore'
    }
});

var deps = [
    'upload/FileType',
    'upload/FileTypes',
    'upload/LayerInfo'
];

define(deps, function (FileType, FileTypes, LayerInfo) {
    'use strict';

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
    test('LayerInfo should work on a valid shapefile', function () {
        var shpInfo = new LayerInfo({
            name: 'nybb',
            files: [{name: 'nybb.shp'}, {name: 'nybb.dbf'}, {name: 'nybb.prj'}, {name: 'nybb.shx'}]
        }),
            res = {},
            errors,
            mock_form_data = {append: function (key, value) { res[key] = value; }};

        strictEqual(shpInfo instanceof LayerInfo,
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


    // describe('The LayerInfo object on an unknown type', function () {
    //     var unknownType = new LayerInfo({
    //         name: 'pdf',
    //         files: [{name: 'test.pdf'}]
    //     });

    //     it('Should return the correct class', function () {
    //         expect(unknownType instanceof LayerInfo).toBeTruthy();
    //     });

    //     it('Should return one error', function () {
    //         expect(unknownType.errors.length).toEqual(1);
    //     });

    // });


    // describe('The LayerInfo type on a CSV file', function () {
    //     var csvInfo = new LayerInfo({
    //         name: 'test-csv',
    //         files: [{name: 'test.csv'}]
    //     });

    //     it('Should return the correct class', function () {
    //         expect(csvInfo instanceof LayerInfo).toBeTruthy();
    //     });

    //     it('Should return the correct type', function () {
    //         expect(csvInfo.type).toEqual(FileTypes.CSV);
    //     });

    //     it('Should return no errors', function () {
    //         expect(csvInfo.errors.length).toEqual(0);
    //     });

    // });

    // describe('The LayerInfo type on a Tiff file', function () {
    //     var tifInfo = new LayerInfo({name: 'test-tif', files: [{name: 'test.tif'}]});

    //     it('Should return the correcet class', function () {
    //         expect(tifInfo instanceof LayerInfo).toBeTruthy();
    //     });

    //     it('Should return the correct file type', function () {
    //         expect(tifInfo.type).toEqual(FileTypes.TIF);
    //     });

    //     it('Should return no errors', function () {
    //         expect(tifInfo.errors.length).toEqual(0);
    //     });
    // });

    // describe('The LayerInfo type on a Zip file', function () {
    //     var tifInfo = new LayerInfo({name: 'test-zip', files: [{name: 'test.zip'}]});

    //     it('Should return the correcet class', function () {
    //         expect(tifInfo instanceof LayerInfo).toBeTruthy();
    //     });

    //     it('Should return the correct file type', function () {
    //         expect(tifInfo.type).toEqual(FileTypes.ZIP);
    //     });

    //     it('Should return no errors', function () {
    //         expect(tifInfo.errors.length).toEqual(0);
    //     });
    // });

    // describe('The UploadSession should be able', function () {
    //     var ses = new UploadSession({
    //         name: 'test session',
    //         id: 1,
    //         layer_name: 'test',
    //         layer_id: 1,
    //         state: 'PEDDING',
    //         url: '',
    //         date: 'Date',
    //     });

    //     it('Should return the correct class', function () {
    //         expect(ses instanceof UploadSession).toBeTruthy();
    //     });

    // });

});
