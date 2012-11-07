/*global define: true, jasmine: true, describe: true, it: true, expect: true */
requirejs.config({
    baseUrl: '../libs'
});


define(['jquery',
        '../js/upload/FileType',
        '../js/upload/LayerInfo',
        '../js/upload/FileTypes',
        '../js/status/UploadSession'], function ($, FileType, LayerInfo, FileTypes, UploadSession) {

    'use strict';

    describe('FileType constructor', function () {
        var type = new FileType({
            name: 'Test type',
            main: 'test',
            requires: ['test']
        });

        it('Should the correct class', function () {
            expect(type instanceof FileType).toBeTruthy();
        });

        it('Should be able to correctly identify its own type', function () {

            expect(type.isType({name: 'this-is-not.ls'})).toBeFalsy();
            expect(type.isType({name: 'this-is.test'})).toBeTruthy();
        });

        it('Should be able to check the type errors correctly', function () {
            expect(type.findTypeErrors(['test'])).toEqual([]);
            expect(type.findTypeErrors(['false'])).toEqual(['Missing a test file, which is required']);
        });

    });

    describe('LayerInfo should work on a valid shapefile', function () {
        var shpInfo = new LayerInfo({
            name: 'nybb',
            files: [{name: 'nybb.shp'}, {name: 'nybb.dbf'}, {name: 'nybb.prj'}, {name: 'nybb.shx'}]
        }),
            res = {},
            mock_form_data = {append: function (key, value) { res[key] = value; }};

        it('Should return the correct class', function () {

            expect(shpInfo instanceof LayerInfo).toBeTruthy();
        });

        it('Should prepare the FormData object correctly', function () {
            shpInfo.prepareFormData(mock_form_data);
            expect(res.hasOwnProperty('base_file')).toBeTruthy();
            expect(res.hasOwnProperty('permissions')).toBeTruthy();
            expect(res.hasOwnProperty('prj_file')).toBeTruthy();
            expect(res.hasOwnProperty('dbf_file')).toBeTruthy();
            expect(res.hasOwnProperty('shx_file')).toBeTruthy();
        });

        it('Should be the correct file type', function () {
            expect(shpInfo.type).toBe(FileTypes.SHP);
        });

        it('Should return the correct extensions', function () {
            expect(shpInfo.getExtensions()).toEqual(['shp', 'dbf', 'prj', 'shx']);
        });

        it('Should return no errors', function () {
            expect(shpInfo.errors.length).toEqual(0);
        });

        it('Should have the correct amount of associated files', function () {
            expect(shpInfo.files.length).toEqual(4);
        });

        it('Should correctly remove an associated file', function () {
            var errors;
            shpInfo.removeFile('nybb.dbf');
            expect(shpInfo.files.length).toEqual(3);
            errors = shpInfo.collectErrors();
            expect(errors.length).toEqual(1);
        });

    });

    describe('The LayerInfo object on an unknown type', function () {
        var unknownType = new LayerInfo({
            name: 'pdf',
            files: [{name: 'test.pdf'}]
        });

        it('Should return the correct class', function () {
            expect(unknownType instanceof LayerInfo).toBeTruthy();
        });

        it('Should return one error', function () {
            expect(unknownType.errors.length).toEqual(1);
        });

    });


    describe('The LayerInfo type on a CSV file', function () {
        var csvInfo = new LayerInfo({
            name: 'test-csv',
            files: [{name: 'test.csv'}]
        });

        it('Should return the correct class', function () {
            expect(csvInfo instanceof LayerInfo).toBeTruthy();
        });

        it('Should return the correct type', function () {
            expect(csvInfo.type).toEqual(FileTypes.CSV);
        });

        it('Should return no errors', function () {
            expect(csvInfo.errors.length).toEqual(0);
        });

    });

    describe('The LayerInfo type on a Tiff file', function () {
        var tifInfo = new LayerInfo({name: 'test-tif', files: [{name: 'test.tif'}]});

        it('Should return the correcet class', function () {
            expect(tifInfo instanceof LayerInfo).toBeTruthy();
        });

        it('Should return the correct file type', function () {
            expect(tifInfo.type).toEqual(FileTypes.TIF);
        });

        it('Should return no errors', function () {
            expect(tifInfo.errors.length).toEqual(0);
        });
    });

    describe('The LayerInfo type on a Zip file', function () {
        var tifInfo = new LayerInfo({name: 'test-zip', files: [{name: 'test.zip'}]});

        it('Should return the correcet class', function () {
            expect(tifInfo instanceof LayerInfo).toBeTruthy();
        });

        it('Should return the correct file type', function () {
            expect(tifInfo.type).toEqual(FileTypes.ZIP);
        });

        it('Should return no errors', function () {
            expect(tifInfo.errors.length).toEqual(0);
        });
    });

    describe('The UploadSession should be able', function () {
        var ses = new UploadSession({
            name: 'test session',
            id: 1,
            layer_name: 'test',
            layer_id: 1,
            state: 'PEDDING',
            url: '',
            date: 'Date',
        });

        it('Should return the correct class', function () {
            expect(ses instanceof UploadSession).toBeTruthy();
        });

    });

    jasmine.getEnv().addReporter(new jasmine.TrivialReporter());
    jasmine.getEnv().execute();

});