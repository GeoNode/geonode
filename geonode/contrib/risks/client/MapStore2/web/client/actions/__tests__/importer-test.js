/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const expect = require('expect');
const {
    IMPORTS_LOADING,
    loadImports, IMPORTS_LIST_LOADED,
    loadImport, IMPORT_LOADED,
    createImport, IMPORT_CREATED,
    deleteImport, IMPORT_DELETE,
    runImport, IMPORT_RUN_SUCCESS,
    loadLayer, LAYER_LOADED,
    updateLayer,
    loadTask, IMPORTS_TASK_LOADED,
    updateTask, IMPORTS_TASK_UPDATED,
    deleteTask, IMPORTS_TASK_DELETE,
    loadTransform, IMPORTS_TRANSFORM_LOAD,
    updateTransform, IMPORTS_TRANSFORM_UPDATED,
    editTransform, IMPORTS_TRANSFORM_CHANGE,
    deleteTransform, IMPORTS_TRANSFORM_DELETE,
    loadStylerTool,
    selectWorkSpace,
    loadWorkspaces,
    createWorkspace,
    IMPORTER_WORKSPACE_LOADED,
    IMPORTER_WORKSPACE_SELECTED,
    IMPORTER_WORKSPACE_CREATED,
    dismissWorkspaceCreationStatus, IMPORTER_WORKSPACE_STATUS_CHANGE} = require('../importer');
const {MAP_CONFIG_LOADED} = require('../config');

/* This utility function runs a serie of test on an action creator
   with multiple dispatch inside
   You have to pass an array of functions that tests the action dispatched by
   the action creator. TODO evaulate to put in a TestUtils.
*/
const runAsyncTest = (url, action, tests, done, params = [], state) => {
    let count = 0;
    action(url, ...params)((actionResult) => {
        try {
            tests[count](actionResult);
            count++;
            if (count === tests.length - 1) {
                done();
            }
        } catch(e) {
            done(e);
        }


    }, () => (state));
};
// NOTE use # to skip parameters by the API
describe('Test correctness of the importer actions', () => {
    // most common test
    const testLoading = (actionResult) => {
        expect(actionResult.type).toBe(IMPORTS_LOADING);
    };
    it('load imports list loading', (done) => {
        const testImports = (actionResult) => {
            let imports = actionResult && actionResult.imports;
            expect(actionResult.type).toBe(IMPORTS_LIST_LOADED);
            expect(imports).toExist();
            expect(imports.length).toBe(2);
        };
        let url = 'base/web/client/test-resources/importer/imports.json#';
        let tests = [testLoading, testImports, testLoading ];
        runAsyncTest(url, loadImports, tests, done);
    });
    it('single import load', (done) => {
        const testImportCreation = (actionResult) => {
            expect(actionResult.type).toBe(IMPORT_LOADED);
        };
        let url = 'base/web/client/test-resources/importer/import.json#';
        let tests = [testLoading, testImportCreation ];
        runAsyncTest(url, loadImport, tests, done);
    });
    it('import creation', (done) => {
        const testImportCreation = (actionResult) => {
            expect(actionResult.type).toBe(IMPORT_CREATED);
        };
        let url = 'base/web/client/test-resources/importer/import.json#';
        let tests = [testLoading, testImportCreation ];
        runAsyncTest(url, createImport, tests, done, [1]);
    });
    it('import delete', (done) => {
        const testDeleteImport = (actionResult) => {
            expect(actionResult.type).toBe(IMPORT_DELETE);
            expect(actionResult.id).toBe(1);
        };
        let url = 'base/web/client/test-resources/importer/import.json#';
        let tests = [testLoading, testDeleteImport, testLoading ];
        runAsyncTest(url, deleteImport, tests, done, [1]);
    });
    it('import run', (done) => {
        const testRunImport = (actionResult) => {
            expect(actionResult.type).toBe(IMPORT_RUN_SUCCESS);
            expect(actionResult.importId).toBe(1);
        };
        let url = 'base/web/client/test-resources/importer/import.json#';
        let tests = [testLoading, testRunImport, testLoading ];
        runAsyncTest(url, runImport, tests, done, [1]);
    });

    // layer
    it('layer load', (done) => {
        const testLoadLayer = (actionResult) => {
            expect(actionResult.type).toBe(LAYER_LOADED);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.layer).toExist();
        };
        let url = 'base/web/client/test-resources/importer/layer.json#';
        let tests = [testLoading, testLoadLayer, testLoading ];
        runAsyncTest(url, loadLayer, tests, done, [1, 2]);
    });

    it('layer update', (done) => {
        const testLoadLayer = (actionResult) => {
            expect(actionResult.type).toBe(LAYER_LOADED);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
        };
        let url = 'base/web/client/test-resources/importer/task.json#';
        let tests = [testLoading, testLoadLayer, testLoading ];
        runAsyncTest(url, updateLayer, tests, done, [1, 2]);
    });

    // task
    it('task load', (done) => {
        const testLoadLayer = () => {

        };
        const testLoadTask = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TASK_LOADED);
            expect(actionResult.task).toExist();
        };
        let url = 'base/web/client/test-resources/importer/task.json#';
        let tests = [testLoading, testLoadTask, testLoadLayer, testLoading ];
        runAsyncTest(url, loadTask, tests, done);
    });
    // task
    it('task update', (done) => {
        const testLoadLayer = () => {

        };
        const testLoadTask = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TASK_UPDATED);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.task).toExist();
        };
        const testUpdateUI = (fun) => {
            expect(fun).toExist();
            fun('base/web/client/test-resources/importer/task.json#', 1, 2);
        };
        let url = 'base/web/client/test-resources/importer/task.json#';
        let state = {
           importer: {
              selectedImport: {
                 id: 1,
                 targetWorkspace: {
                    workspace: {
                       name: "TEST"
                    }
                 }
              }
           }
       };
        let tests = [testLoading, testLoadTask, testLoadLayer, testUpdateUI];
        runAsyncTest(url, updateTask, tests, done, [1, 2, {}], state );

    });

    it('task element update', (done) => {
        const testLoadLayer = () => {

        };
        const testLoadTask = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TASK_UPDATED);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.task).toExist();
        };
        let url = 'base/web/client/test-resources/importer/task.json#';
        let tests = [testLoading, testLoadTask, testLoadLayer, testLoading ];
        runAsyncTest(url, updateTask, tests, done, [1, 2, {}, "target"]);
    });
    it('task delete', (done) => {
        const testdeleteTask = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TASK_DELETE);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
        };
        let url = 'base/web/client/test-resources/importer/task.json#';
        let tests = [testLoading, testdeleteTask, testLoading ];
        runAsyncTest(url, deleteTask, tests, done, [1, 2, {}]);
    });

    // transform
    it('transform load', (done) => {
        const testLoadTransform = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TRANSFORM_LOAD);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.transformId).toBe(3);
            expect(actionResult.transform).toExist();
        };
        let url = 'base/web/client/test-resources/importer/transform.json#';
        let tests = [testLoading, testLoadTransform, testLoading ];
        runAsyncTest(url, loadTransform, tests, done, [1, 2, 3]);
    });
    // transform
    it('transform update', (done) => {
        const testUpdateTransform = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TRANSFORM_UPDATED);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.transformId).toBe(3);
        };
        let url = 'base/web/client/test-resources/importer/transform.json#';
        let tests = [testLoading, testUpdateTransform, testLoading ];
        runAsyncTest(url, updateTransform, tests, done, [1, 2, 3]);
    });
    // transform
    it('transform delete', (done) => {
        const testdeleteTransform = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTS_TRANSFORM_DELETE);
            expect(actionResult.importId).toBe(1);
            expect(actionResult.taskId).toBe(2);
            expect(actionResult.transformId).toBe(3);
        };
        let url = 'base/web/client/test-resources/importer/transform.json#';
        let tests = [testLoading, testdeleteTransform, testLoading ];
        runAsyncTest(url, deleteTransform, tests, done, [1, 2, 3]);
    });

    it('transform edit', () => {
        let transform = {options: [1, 2, 3]};
        const result = editTransform(transform);
        expect(result.type).toBe(IMPORTS_TRANSFORM_CHANGE);
        expect(result.transform).toBe(transform);
    });
    // load styler
    it('load styler tool', (done) => {
        const testConfigureMap = (actionResult) => {
            expect(actionResult.type).toBe(MAP_CONFIG_LOADED);
            expect(actionResult.config).toExist();
            expect(actionResult.config.map).toExist();
            expect(actionResult.config.map.layers).toExist();
            expect(actionResult.config.map.layers.length).toBe(2);
            done();
        };
        let url = 'base/web/client/test-resources/importer/layer.json#';
        let tests = [testConfigureMap];
        runAsyncTest(url, loadStylerTool, tests, done, [], {importer: {selectedImport: {targetWorkspace: { workspace: {name: "TEST"}}}}});
    });
    // select workspace
    it('load styler tool', () => {
        const wsName = "worskpace_name";
        let res = selectWorkSpace(wsName);
        expect(res).toExist();
        expect(res.type).toBe(IMPORTER_WORKSPACE_SELECTED);
        expect(res.workspace).toBe(wsName);
    });

    // load workspaces
    it('load workspaces', (done) => {
        const testWorkspaces = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTER_WORKSPACE_LOADED);
            done();
        };
        let url = 'base/web/client/test-resources/geoserver/rest/workspaces.json#';
        let tests = [testWorkspaces];
        runAsyncTest(url, loadWorkspaces, tests, done, []);
    });
    // load workspaces
    it('create workspace', (done) => {
        const testWorkspaceCreated = (actionResult) => {
            expect(actionResult.type).toBe(IMPORTER_WORKSPACE_CREATED);
            done();
        };
        let url = 'base/web/client/test-resources/geoserver/rest/workspaces.json#';
        let tests = [testLoading, testWorkspaceCreated];
        runAsyncTest(url, createWorkspace, tests, done, []);
    });
    // load workspaces
    it('update workspace creation status', () => {
        let res = dismissWorkspaceCreationStatus();
        expect(res).toExist();
        expect(res.type).toBe(IMPORTER_WORKSPACE_STATUS_CHANGE);
    });

});
