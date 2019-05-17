/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
var API = require('../api/geoserver/Importer');
const Workspaces = require('../api/geoserver/Workspaces');
const {configureMap} = require('./config');
const {isString} = require('lodash');

const assign = require('object-assign');
const IMPORTS_LOADING = 'IMPORTS_LOADING';
const IMPORTS_CREATION_ERROR = 'IMPORTS_CREATION_ERROR';
const IMPORT_CREATED = 'IMPORT_CREATED';

const IMPORTS_TASK_CREATED = 'IMPORTS_TASK_CREATED';
const IMPORTS_TASK_LOADED = 'IMPORTS_TASK_LOADED';
const IMPORTS_TASK_LOAD_ERROR = 'IMPORTS_TASK_LOAD_ERROR';
const IMPORTS_TASK_UPDATED = 'IMPORTS_TASK_UPDATED';
const IMPORTS_TASK_DELETE = 'IMPORTS_TASK_DELETE';
const IMPORTS_TASK_CREATION_ERROR = 'IMPORTS_TASK_CREATION_ERROR';

const LAYER_LOADED = 'LAYER_LOADED';
const LAYER_UPDATED = 'LAYER_UPDATED';

const IMPORTS_TRANSFORM_LOAD = 'IMPORTS_TRANSFORM_LOAD';
const IMPORTS_TRANSFORM_LOAD_ERROR = 'IMPORTS_TRANSFORM_LOAD_ERROR';
const IMPORTS_TRANSFORM_CHANGE = 'IMPORTS_TRANSFORM_CHANGE';

const IMPORTS_TRANSFORM_DELETE = 'IMPORTS_TRANSFORM_DELETE';
const IMPORTS_TRANSFORM_UPDATED = 'IMPORTS_TRANSFORM_UPDATED';

const IMPORTS_FILE_UPLOADED = 'IMPORTS_FILE_UPLOADED';
const IMPORTS_UPLOAD_PROGRESS = 'IMPORTS_UPLOAD_PROGRESS';

const IMPORTS_LIST_LOADED = 'IMPORTS_LIST_LOADED';
const IMPORTS_LIST_LOAD_ERROR = 'IMPORTS_LIST_LOAD_ERROR';
const TASK_PROGRESS_UPDATED = 'TASK_PROGRESS_UPDATED';

const IMPORT_LOADED = 'IMPORT_LOADED';
const IMPORT_LOAD_ERROR = 'IMPORT_LOAD_ERROR';
const IMPORT_RUN_SUCCESS = 'IMPORT_RUN_SUCCESS';
const IMPORT_RUN_ERROR = 'IMPORT_RUN_ERROR';
const IMPORT_DELETE = 'IMPORT_DELETE';
const IMPORT_DELETE_ERROR = 'IMPORT_DELETE_ERROR';

const IMPORTER_WORKSPACE_SELECTED = 'IMPORTER_WORKSPACE_SELECTED';
const IMPORTER_WORKSPACE_LOADED = 'IMPORTER_WORKSPACE_LOADED';
const IMPORTER_WORKSPACE_CREATED = 'IMPORTER_WORKSPACE_CREATED';
const IMPORTER_WORKSPACE_CREATION_ERROR = 'IMPORTER_WORKSPACE_CREATION_ERROR';
const IMPORTER_WORKSPACE_STATUS_CHANGE = 'IMPORTER_WORKSPACE_STATUS_CHANGE';
/*******************/
/* UTILITY         */
/*******************/

/**
 * Check if task matches with the preset.
 * The match is by state, data.file.format and data.file.name
 * (also regex allowed for file name).
 */
const matchPreset = function(preset, task) {
    if (preset.state && preset.state !== task.state) {
        return false;
    }
    if (preset.data && task.data) {
        if (preset.data.format && preset.data.format !== task.data.format) {
            return false;
        }
        if (preset.data.file && preset.data.file !== task.data.file) {
            try {
                let patt = new RegExp(preset.data.file);
                if (!patt.test(task.data.file)) {
                    return false;
                }
            } catch(e) {
                return false;
            }

        }
    }
    return true;
};
// for the moment supports only dataStore.name with only one change
const applyPlaceholders = function(preset, model) {

    let replaceTargetWorkspace = function(el) {
        if (isString(el)) {
            return el.replace("{targetWorkspace}", model.targetWorkspace && model.targetWorkspace.workspace && model.targetWorkspace.workspace.name);
        }
    };
    if (preset && preset.changes && preset.changes.target && preset.changes.target.dataStore && preset.changes.target.dataStore.name) {
        return assign({}, preset, {
            changes: assign({}, preset.changes, {
                target: assign({}, preset.changes.target, {
                    dataStore: assign({}, preset.changes.target.dataStore, {
                        name: replaceTargetWorkspace(preset.changes.target.dataStore.name)
                    })
                })
            })
        });
    }
    return preset;

};
/*******************/
/* ACTION CREATORS */
/*******************/

function loading(details, isLoading = true) {
    return {
        type: IMPORTS_LOADING,
        loading: isLoading,
        details: details
    };
}
function loadError(e) {
    return {
        type: IMPORTS_LIST_LOAD_ERROR,
        error: e
    };
}

/** IMPORT **/
function importCretationError(e) {
    return {
        type: IMPORTS_CREATION_ERROR,
        error: e
    };
}
function importCreated(importObj) {
    return {
        type: IMPORT_CREATED,
        "import": importObj
    };
}

function importTaskCreated(importId, tasks) {
    return {
        type: IMPORTS_TASK_CREATED,
        importId: importId,
        tasks: tasks
    };
}

function importTaskUpdated(task, importId, taskId) {
    return {
        type: IMPORTS_TASK_UPDATED,
        task,
        importId,
        taskId
    };
}

function importTaskDeleted(importId, taskId) {
    return {
        type: IMPORTS_TASK_DELETE,
        importId,
        taskId
    };
}

function importsLoaded(imports) {
    return {
        type: IMPORTS_LIST_LOADED,
        imports: imports
    };
}

function importLoaded(importObj) {
    return {
        type: IMPORT_LOADED,
        "import": importObj
    };
}
function importLoadError(e) {
    return {
        type: IMPORT_LOAD_ERROR,
        "error": e
    };
}

function importRunSuccess(importId) {
    return {
        type: IMPORT_RUN_SUCCESS,
        importId
    };
}

function importRunError(importId, error) {
    return {
        type: IMPORT_RUN_ERROR,
        importId,
        error
    };
}
function importDeleted(id) {
    return {
        type: IMPORT_DELETE,
        id: id
    };
}

function importDeleteError(id, e) {
    return {
        type: IMPORT_DELETE_ERROR,
        error: e,
        id
    };
}

/** TASKS **/

function importTaskLoaded(task) {
    return {
        type: IMPORTS_TASK_LOADED,
        task: task
    };
}
function importTaskLoadError(e) {
    return {
        type: IMPORTS_TASK_LOAD_ERROR,
        task: e
    };
}
function importTaskCreationError(e) {
    return {
        type: IMPORTS_TASK_CREATION_ERROR,
        error: e
    };
}

function layerLoaded(importId, taskId, layer) {
    return {
        type: LAYER_LOADED,
        importId,
        taskId,
        layer
    };
}

function layerUpdated(importId, taskId, layer) {
    return {
        type: LAYER_LOADED,
        importId,
        taskId,
        layer
    };
}
function taskProgressUpdated(importId, taskId, info) {
    return {
        type: TASK_PROGRESS_UPDATED,
        importId,
        taskId,
        info
    };
}
/** TRANSFORMS **/
function transformLoaded(importId, taskId, transformId, transform) {
    return {
        type: IMPORTS_TRANSFORM_LOAD,
        importId,
        taskId,
        transformId,
        transform
    };
}

function editTransform(transform) {
    return {
        type: IMPORTS_TRANSFORM_CHANGE,
        transform
    };
}

function transformLoadError(importId, taskId, transformId, error) {
    return {
        type: IMPORTS_TRANSFORM_LOAD_ERROR,
        importId,
        taskId,
        transformId,
        error
    };
}
function transformDeleted(importId, taskId, transformId) {
    return {
        type: IMPORTS_TRANSFORM_DELETE,
        importId,
        taskId,
        transformId
    };
}
function transformUpdated(importId, taskId, transformId, transform) {
    return {
        type: IMPORTS_TRANSFORM_UPDATED,
        importId,
        taskId,
        transformId,
        transform
    };
}
/** FILE UPLOAD **/
function fileUploaded(files) {
    return {
        type: IMPORTS_FILE_UPLOADED,
        "files": files
    };
}

function uploadProgress(progress) {
    return {
        type: IMPORTS_UPLOAD_PROGRESS,
        progress: progress
    };
}

/** WORKSPACES **/
function selectWorkSpace(workspace) {
    return {
        type: IMPORTER_WORKSPACE_SELECTED,
        workspace: workspace
    };
}
function workspacesLoaded(workspaces) {
    return {
        type: IMPORTER_WORKSPACE_LOADED,
        workspaces: workspaces
    };
}

function workspaceCreated(name) {
    return {
        type: IMPORTER_WORKSPACE_CREATED,
        name
    };
}
function workspaceCreationError(name, error) {
    return {
        type: IMPORTER_WORKSPACE_CREATION_ERROR,
        name,
        error
    };
}
/*******************/
/* DISPATCHERS     */
/*******************/

/** IMPORT **/
function createImport(geoserverRestURL, body = {}) {
    return (dispatch) => {
        dispatch(loading());
        let options = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        API.createImport(geoserverRestURL, body, options).then((response) => {
            dispatch(importCreated(response && response.data && response.data.import));
            dispatch(loading(null, false));
        }).catch((e) => {
            dispatch(importCretationError(e));
            dispatch(loading(null, false));
        });
    };
}
function loadImports(geoserverRestURL) {
    return (dispatch) => {
        dispatch(loading());
        API.getImports(geoserverRestURL).then((response) => {
            dispatch(importsLoaded(response && response.data && response.data.imports));
            dispatch(loading(null, false));
        }).catch((e) => {
            dispatch(loadError(e));
            dispatch(loading(null, false));
        });
    };
}

function loadImport(geoserverRestURL, importId) {
    return (dispatch) => {
        dispatch(loading({importId: importId}));
        API.loadImport(geoserverRestURL, importId).then((response) => {
            dispatch(importLoaded(response && response.data && response.data.import));
            dispatch(loading({importId: importId}, false));
        }).catch((e) => {
            dispatch(importLoadError(e));
            dispatch(loading({importId: importId}, false));
        });
    };
}
function deleteImport(geoserverRestURL, importId) {
    return (dispatch) => {
        dispatch(loading({importId: importId, message: "deleting"}));
        API.deleteImport(geoserverRestURL, importId).then(() => {
            dispatch(importDeleted(importId));
            dispatch(loading({importId: importId, message: "deleting"}, false));
        }).catch((e) => {
            dispatch(importDeleteError(importId, e));
            dispatch(loading({importId: importId, message: "deleting"}, false));
        });
    };
}

function runImport(geoserverRestURL, importId) {
    return (dispatch, getState) => {
        dispatch(loading({importId}));
        API.runImport(geoserverRestURL, importId).then(() => {
            dispatch(importRunSuccess(importId));
            if (getState && getState().selectedImport && getState().selectedImport.id === importId) {
                dispatch(loading({importId}, false));
                dispatch(loadImport(geoserverRestURL, importId));

            } else {
                dispatch(loading({importId}, false));
                dispatch(loadImports(geoserverRestURL));

            }
        }).catch((e) => {importRunError(importId, e); });
    };
}
/** LAYER **/

function loadLayer(geoserverRestURL, importId, taskId) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId, element: "layer", message: "loadinglayer"}));
        return API.loadLayer(geoserverRestURL, importId, taskId).then((response) => {
            dispatch(layerLoaded(importId, taskId, response && response.data && response.data.layer));
            dispatch(loading({importId: importId, taskId: taskId, element: "layer", message: "loadinglayer"}, false));
        });
    };
}
function updateLayer(geoserverRestURL, importId, taskId, layer) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId, element: "layer", message: "loadinglayer"}));

        return API.updateLayer(geoserverRestURL, importId, taskId, layer).then((response) => {
            dispatch(layerUpdated(importId, taskId, response && response.data && response.data.layer));
            dispatch(loading({importId: importId, taskId: taskId, element: "layer", message: "loadinglayer"}, false));
        });
    };
}
/** TASKS **/
function loadTask(geoserverRestURL, importId, taskId) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId}));
        API.loadTask(geoserverRestURL, importId, taskId).then((response) => {
            dispatch(importTaskLoaded(response && response.data && response.data.task));
            dispatch(loadLayer(geoserverRestURL, importId, taskId));
            dispatch(loading({importId: importId, taskId: taskId}, false));
        }).catch((e) => {
            dispatch(importTaskLoadError(e));
            dispatch(loading({importId: importId, taskId: taskId}, false));
        });
    };
}
function updateUI(geoserverRestURL, importId, taskId) {
    return (dispatch, getState) => {
        let state = getState && getState() && getState().importer;
        if (state && state.selectedImport && state.selectedImport.id === importId && state.selectedTask && state.selectedTask.id === taskId) {
            dispatch(loadTask(geoserverRestURL, importId, taskId));
            dispatch(loading({importId, taskId}, false));
        } else if (state && state.selectedImport && state.selectedImport.id === importId) {
            dispatch(loadImport(geoserverRestURL, importId));
            dispatch(loading({importId}, false));
        }else {
            dispatch(loadImports(geoserverRestURL));
            dispatch(loading({importId}, false));
        }
    };
}
function updateTask(geoserverRestURL, importId, taskId, body, element, message = "updating") {
    return (dispatch) => {
        let opts = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        dispatch(loading({importId: importId, taskId: taskId, message}));
        return API.updateTask(geoserverRestURL, importId, taskId, element, body, opts).then((response) => {
            dispatch(importTaskUpdated(response && response.data && response.data.task, importId, taskId));
            dispatch(loading({importId: importId, taskId: taskId}, false));
            dispatch(updateUI(geoserverRestURL, importId, taskId));
        });
    };
}

function deleteTask(geoserverRestURL, importId, taskId) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId, message: "deleting"}));
        return API.deleteTask(geoserverRestURL, importId, taskId).then(() => {
            dispatch(importTaskDeleted(importId, taskId));
            dispatch(loading({importId: importId, taskId: taskId, message: "deleting"}, false));
            dispatch(loading({importId: importId, message: "deleting"}, false));
        });
    };
}

function updateProgress(geoserverRestURL, importId, taskId) {
    return (dispatch) => {
        return API.getTaskProgress(geoserverRestURL, importId, taskId).then((response) => {
            dispatch(taskProgressUpdated(importId, taskId, response.data));
        });
    };
}
/** TRANFORMS **/
function loadTransform(geoserverRestURL, importId, taskId, transformId) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}));
        return API.loadTransform(geoserverRestURL, importId, taskId, transformId).then((response) => {
            let transform = response && response.data;
            dispatch(transformLoaded(importId, taskId, transformId, transform));
            dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}, false));
        }).catch((e) => {transformLoadError(importId, taskId, transformId, e); });
    };
}
function deleteTransform(geoserverRestURL, importId, taskId, transformId) {
    return (dispatch, getState) => {
        dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}));
        return API.deleteTransform(geoserverRestURL, importId, taskId, transformId).then(() => {
            dispatch(transformDeleted(importId, taskId, transformId));
            dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}, false));
            let state = getState().importer;
            if (state.selectedTask && state.selectedTask.id === taskId) {
                dispatch(loadTask(geoserverRestURL, importId, taskId));
                dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}, false));
            }
        }).catch((e) => {transformLoadError(importId, taskId, transformId, e); }); // TODO transform delete error
    };
}

function updateTransform(geoserverRestURL, importId, taskId, transformId, transform) {
    return (dispatch) => {
        dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}));
        return API.updateTransform(geoserverRestURL, importId, taskId, transformId, transform).then((response) => {
            dispatch(transformUpdated(importId, taskId, transformId, response && response.data));
            dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}, false));
        }).catch((e) => {
            transformLoadError(importId, taskId, transformId, e); // TODO transform update error
            dispatch(loading({importId: importId, taskId: taskId, transformId: transformId, message: "loading"}, false));
        });
    };
}
/** PRESETS **/
function applyPreset(geoserverRestURL, importId, task, preset) {

    return (dispatch) => {
        const applyChange = (element, change) => { // TODO better as an action
            dispatch(updateTask(geoserverRestURL, importId, task.id, change, element, "applyPresets"));
        };
        if (preset.changes) {
            // update target, layer
            Object.keys(preset.changes).forEach((element) => {
                let values = preset.changes[element];
                if (Array.isArray(values)) {
                    values.forEach(applyChange.bind(null, element));
                } else {
                    applyChange(element, values);
                }
            });
        }
        if (preset.transforms) {
            preset.transforms.forEach( (transform) => {
                dispatch(loading({importId: importId, taskId: task.id, message: "applyPresets"}));
                API.addTransform(geoserverRestURL, importId, task.id, transform).then(() => {
                    dispatch(loading({importId: importId, taskId: task.id, message: "applyPresets"}, false));
                });
            });
        }
    };
}
function applyPresets(geoserverRestURL, importId, tasks, presets) {
    return (dispatch) => {
        if (tasks) {
            tasks.forEach( (task) => {
                presets.forEach( (preset) => {
                    if (task.data) {
                        if (matchPreset(preset, task)) {
                            dispatch(applyPreset(geoserverRestURL, importId, task, preset));
                        }
                    } else {
                        dispatch(loading({importId: importId, taskId: task.id, message: "analyzing"}));
                        API.loadTask(geoserverRestURL, importId, task.id).then((response) => {
                            dispatch(loading({importId: importId, taskId: task.id}, false));
                            let completeTask = response && response.data && response.data.task;
                            if (matchPreset(preset, completeTask)) {
                                dispatch(applyPreset(geoserverRestURL, importId, completeTask, preset));
                            }
                        });
                    }

                });
            });
        }
    };
}

function loadWorkspaces(geoserverRestURL) {
    return (dispatch) => {
        Workspaces.getWorkspaces(geoserverRestURL).then((result) => {
            dispatch(workspacesLoaded(result.workspaces.workspace));
        });
    };
}

function createWorkspace(geoserverRestURL, name, datastores = []) {
    return (dispatch) => {
        dispatch(loading());
        Workspaces.createWorkspace(geoserverRestURL, name).then(() => {
            dispatch(workspaceCreated(name));

            let count = datastores.length;
            if (count === 0) {
                dispatch(loading(null, false));
            } else {
                datastores.forEach((ds) => {
                    // replace placeholder (this is required because in the importer the datastore name have to be unique, out of workspace)
                    let datastore = ds;
                    let dsname = ds.dataStore && ds.dataStore.name;
                    let datastoreobj = assign({}, ds.dataStore, {name: dsname.replace("{workspace}", name)});
                    datastore = assign({}, ds, {dataStore: datastoreobj});

                    Workspaces.createDataStore(geoserverRestURL, name, datastore).then(() => {
                        count--;
                        if (count === 0) {
                            dispatch(loading(null, false));
                        }
                    });
                });
            }
        }).catch((error) => {
            dispatch(workspaceCreationError(name, error));
            dispatch(loading(null, false));

        });
    };
}

function dismissWorkspaceCreationStatus() {
    return {
        type: IMPORTER_WORKSPACE_STATUS_CHANGE,
        state: null
    };
}

/** UPLOAD **/
function uploadImportFiles(geoserverRestURL, importId, files, presets) {
    return (dispatch, getState) => {
        dispatch(loading({importId: importId, uploadingFiles: files}));
        let progressOpts = {
            progress: (progressEvent) => {
                dispatch(uploadProgress(progressEvent.loaded / progressEvent.total));
            }
        };
        API.uploadImportFiles(geoserverRestURL, importId, files, progressOpts).then((response) => {
            let tasks = response && response.data && response.data.tasks || response && response.data && [response.data.task];
            dispatch(fileUploaded(files));
            dispatch(importTaskCreated(importId, tasks));
            let state = getState();
            let impState = state.importer;
            if (impState && impState.selectedImport && impState.selectedImport.id === importId && tasks && tasks.length > 1) {
                dispatch(loadImport(geoserverRestURL, importId));
            }
            if (presets) {
                let newPreset = presets.map((preset) => (applyPlaceholders(preset, state && state.importer && state.importer.selectedImport)));
                dispatch(applyPresets(geoserverRestURL, importId, tasks, newPreset));
            }
            dispatch(loading({importId: importId}, false));
        }).catch((e) => {
            dispatch(importTaskCreationError(e));
            dispatch(loading({importId: importId}, false));
        });
    };
}

/** STYLER **/
function loadStylerTool(geoserverRestURL, importId, taskId) {
    return (dispatch, getState) => {
        return API.loadLayer(geoserverRestURL, importId, taskId).then((layerResponse) => {
            let layer = layerResponse && layerResponse.data && layerResponse.data.layer;

            let importObj = getState && getState().importer && getState().importer.selectedImport;
            let workspace = importObj.targetWorkspace && importObj.targetWorkspace.workspace.name;
            let stylerMapConfig = {
                  "version": 2,
                  "map": {
                    "projection": "EPSG:3857",
                    "units": "m",
                    "center": {"x": 0, "y": 0, "crs": "EPSG:3857"},
                    "zoom": 2,
                    "maxExtent": [
                      -20037508.34, -20037508.34,
                      20037508.34, 20037508.34
                    ],
                    "layers": [{
                      "type": "osm",
                      "title": "Open Street Map",
                      "name": "mapnik",
                      "source": "osm",
                      "group": "background",
                            "visibility": true
                        }]
                  }
              };
            let config = stylerMapConfig;
            config.map.layers = (config.map.layers || []).concat({
                "type": "wms",
                "url": "/geoserver/wms",
                "visibility": true,
                "title": layer.title,
                "name": workspace + ":" + layer.name,
                "group": "Styler",
                "format": "image/png8"
            });
            dispatch(configureMap(config));
        });

    };
}

module.exports = {
    loadImports, createImport, uploadImportFiles,
    loadImport, runImport, deleteImport,
    updateTask, deleteTask, loadTask,
    updateProgress,
    loadLayer, updateLayer,
    loadTransform, updateTransform, deleteTransform, editTransform,
    loadStylerTool,
    loadWorkspaces,
    createWorkspace,
    selectWorkSpace,
    dismissWorkspaceCreationStatus,
    IMPORTS_LOADING,
    IMPORTS_LIST_LOADED,
    IMPORTS_LIST_LOAD_ERROR,
    IMPORT_CREATED,
    IMPORT_LOADED,
    IMPORT_RUN_SUCCESS,
    IMPORT_RUN_ERROR,
    IMPORT_DELETE,
    IMPORT_DELETE_ERROR,
    IMPORTS_TASK_CREATED,
    IMPORTS_TASK_CREATION_ERROR,
    IMPORTS_TASK_LOADED,
    IMPORTS_TASK_UPDATED,
    TASK_PROGRESS_UPDATED,
    LAYER_LOADED,
    LAYER_UPDATED,
    IMPORTS_TRANSFORM_LOAD,
    IMPORTS_TRANSFORM_UPDATED,
    IMPORTS_TRANSFORM_CHANGE,
    IMPORTS_TRANSFORM_DELETE,
    IMPORTS_TRANSFORM_LOAD_ERROR,
    IMPORTS_TASK_DELETE,
    IMPORTS_FILE_UPLOADED,
    IMPORTS_UPLOAD_PROGRESS,
    IMPORTER_WORKSPACE_SELECTED,
    IMPORTER_WORKSPACE_LOADED,
    IMPORTER_WORKSPACE_CREATED,
    IMPORTER_WORKSPACE_CREATION_ERROR,
    IMPORTER_WORKSPACE_STATUS_CHANGE
};
