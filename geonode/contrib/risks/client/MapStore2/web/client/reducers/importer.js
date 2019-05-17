/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {
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
    IMPORTS_TASK_DELETE,
    TASK_PROGRESS_UPDATED,
    LAYER_LOADED,
    LAYER_UPDATED,
    IMPORTS_TRANSFORM_LOAD,
    IMPORTS_TRANSFORM_CHANGE,
    IMPORTS_TRANSFORM_DELETE,
    IMPORTS_FILE_UPLOADED,
    IMPORTS_UPLOAD_PROGRESS,
    IMPORTER_WORKSPACE_LOADED,
    IMPORTER_WORKSPACE_SELECTED,
    IMPORTER_WORKSPACE_CREATED,
    IMPORTER_WORKSPACE_CREATION_ERROR,
    IMPORTER_WORKSPACE_STATUS_CHANGE
} = require('../actions/importer');

const {
    MANAGER_ITEM_SELECTED
} = require('../actions/manager');

const assign = require('object-assign');
const {head, findIndex} = require('lodash');

// constant used to reset the state only if the importer tool is passed to the reducer
// see case: MANAGER_ITEM_SELECTED
const importerTool = "importer";

/******************************************************************************/
/* UTILITY FUNCTIONS **********************************************************/
/******************************************************************************/

function updateArray(tasks, newTask) {
    if (!newTask || !tasks) {
        return tasks;
    }
    let taskIndex = findIndex(tasks, (task) => task.id === newTask.id );
    if (taskIndex >= 0 && newTask !== tasks[taskIndex]) {
        let newTasks = tasks.slice();
        newTasks[taskIndex] = newTask;
        return newTasks;
    }
    return tasks;
}
function updateImportLoadingStatus(state, action, loading = true) {
    let importId = action.importId !== undefined ? action.importId : (action.details && action.details.importId);
    let selectedImport = state && state.selectedImport;
    // TODO state.tasks update this if needed
    // update selected import
    let imports = state && state.imports;
    if (selectedImport && selectedImport.id === importId) {
        selectedImport = assign({}, selectedImport, {loading: loading});
    }
    // update imports list
    imports = updateArray(imports, assign({}, head(imports.filter((imp) => imp.id === importId), {loading: loading})));
    return assign({}, state, {
        uploading: action.details && action.details.uploadingFiles !== undefined || state.uploading,
        loading: loading,
        selectedImport,
        imports
    });
}
function updateImportTaskLoadingStatus(state, action, loading = true) {
    let selectedImport = state && state.selectedImport;
    let selectedTask = state && state.selectedTask;
    // TODO state.tasks update this if needed
    let imports = state && state.imports;
    let importId = action.importId !== undefined ? action.importId : (action.details && action.details.importId);
    let taskId = action.taskId !== undefined ? action.taskId : (action.details && action.details.taskId);
    // update selected import
    if (selectedImport && importId === selectedImport.id) {
        if ( selectedTask && selectedTask.id === taskId ) {
            selectedTask = assign({}, selectedTask, {
                loading: loading,
                message: action.details && action.details.message,
                element: action.details && action.details.element
            });
        }
        let newTask = assign({}, head(selectedImport.tasks.filter((task) => task.id === taskId)), {
            loading: loading,
            message: action.details && action.details.message,
            element: action.details && action.details.element
        });
        // update selected task
        if (selectedImport && selectedImport.tasks && newTask) {
            selectedImport = assign({}, selectedImport);
            selectedImport.tasks = updateArray(selectedImport.tasks, newTask);
        }
    }
    // update imports list's task
    let impIndex = imports && findIndex(imports, (imp) => imp.id === importId);
    if ( imports && impIndex >= 0 ) {
        imports = imports.concat();
        let imp = imports[impIndex];
        let taskIndex = imp && imp.tasks && findIndex(imp.tasks, (task) => task.id === taskId);
        if ( imp && imp.tasks && taskIndex >= 0 ) {
            let task = assign({}, task, {
                loading: loading,
                message: action.details && action.details.message,
                element: action.details && action.details.element
            });
            imports[impIndex] = assign({}, imp);
            imports[impIndex].tasks = updateArray(imports[impIndex].tasks, task);
        }
    }
    return assign({}, state, {
        uploading: action.details && action.details.uploadingFiles !== undefined || state.uploading,
        loading: loading,
        selectedTask,
        selectedImport,
        imports
    });
}

/******************************************************************************/
/* REDUCER ********************************************************************/
/******************************************************************************/

function importer(state = {}, action) {
    switch (action.type) {
        case IMPORTS_LOADING: {
            if (!action.details) {
                // loading full list
                return assign({}, state, {loading: action.loading, uploading: action.details && action.details.uploadingFiles !== undefined || state.uploading});
            } else if (action.details.importId !== undefined && action.details.taskId === undefined) {
                // loading an import
                return updateImportLoadingStatus(state, action, action.loading);
            } else if (action.details.importId !== undefined && action.details.taskId !== undefined) {
                // loading a task
                return updateImportTaskLoadingStatus(state, action, action.loading);
            }
        }
        return state;
        case MANAGER_ITEM_SELECTED: {
            const toolId = action.toolId;
            if (toolId === importerTool) {
                return assign({}, state, {
                    loadingError: null,
                    imports: state.imports,
                    selectedImport: null,
                    selectedTask: null,
                    selectedTransform: null
                });
            }
            return state;
        }
        case IMPORTS_LIST_LOADED:
            return assign({}, state, {
                loadingError: null,
                imports: action.imports,
                selectedImport: null,
                selectedTask: null,
                selectedTransform: null
            });
        case IMPORTS_LIST_LOAD_ERROR:
            return assign({}, {
                loadingError: action.error
            });
        case IMPORT_CREATED:
            return assign({}, state, {
                selectedImport: action.import,
                selectedTask: null,
                selectedTransform: null
            });
        case IMPORTS_TASK_CREATED:
            if (action.importId === (state.selectedImport && state.selectedImport.id) ) {
                let selectedImport = assign({}, state.selectedImport, {
                    tasks: [...(state.selectedImport.tasks || []), ...action.tasks]
                });
                return assign({}, state, {taskCreationError: null, selectedImport});
            }
            return state;
        case IMPORTS_TASK_UPDATED: {
            let selectedTask = state && state.selectedTask;
            if ( action.task && selectedTask && selectedTask.id === action.task.id) {
                selectedTask = action.task;
            }
            let tasks = state.tasks;
            if (tasks && action.task) {
                let index = findIndex(tasks, (task) => task.id === action.task.id);
                if (index >= 0) {
                    tasks = tasks.concat();
                    tasks[index] = action.task;
                }
            }
            return assign({}, state, {
                selectedTask,
                tasks
            });
        }
        case IMPORTS_TASK_CREATION_ERROR: {
            return assign({}, state, {
                uploading: false,
                taskCreationError: action.error
            });
        }
        case TASK_PROGRESS_UPDATED: {
            let selectedTask = state.selectedTask;
            let selectedImport = state.selectedImport;
            let tasks = selectedImport && selectedImport.tasks;
            if (selectedTask && (selectedTask.id === action.taskId)) {
                selectedTask = assign({}, selectedTask, action.info);
            }
            if (selectedImport && (selectedImport.id === action.importId)) {

                let index = findIndex(tasks, (task) => task.id === action.taskId);
                if (index >= 0) {
                    tasks = tasks.concat();
                    tasks[index] = assign({}, tasks[index], action.info);
                    selectedImport = assign({}, selectedImport, {tasks: tasks});
                }
            }
            return assign({}, state, {
                selectedTask,
                selectedImport
            });
        }
        case LAYER_LOADED: {
            let task = state.selectedTask;
            let importObj = state.selectedImport;
            if ( importObj && task && (importObj.id === action.importId) && (task.id === action.taskId)) {
                task = assign({}, task, {
                    layer: action.layer
                });
                return assign({}, state, {
                    selectedTask: task
                });
            }
            return assign({}, state, {
                layer: action.layer
            });
        }
        case LAYER_UPDATED: {
            let task = state.selectedTask;
            let importObj = state.selectedImport;
            if ( importObj && task && importObj.id === action.importId && task.id === action.taskId) {
                task = assign({}, task, {
                    layer: action.layer
                });
                return assign({}, state, {
                    selectedTask: task
                });
            }
            return state;
        }
        case IMPORTS_TRANSFORM_LOAD: {
            let transform = assign({}, action.transform);
            transform.id = action.transformId;
            return assign({}, state, {
                selectedTransform: transform
            });
        }
        case IMPORTS_TRANSFORM_CHANGE: {
            let transform = assign({}, state.selectedTransform || {}, action.transform, {status: "modified"});
            return assign({}, state, {
                selectedTransform: transform
            });
        }
        case IMPORTS_TRANSFORM_DELETE: {
            if (state.selectedTask &&
                state.selectedTask.transformChain &&
                state.selectedTask.transformChain.transforms &&
                state.selectedTask.transformChain.transforms[action.transformId]
                ) {
                let newSelectedTask = assign({}, state.selectedTask, {
                    transformsChain: assign({}, state.selectedTask.transformChain, {
                        transforms: state.selectedTask.transformChain.transforms.filter((obj, index) => index !== action.transformId)
                    })
                });
                return assign({}, state, {
                    selectedTask: newSelectedTask,
                    selectedTransform: state.selectedTransform && state.selectedTransform.id === action.transformId ? null : state.selectedTransform
                });
            }
        }
        case IMPORT_LOADED: {
            return assign({}, state, {
                selectedImport: action.import,
                selectedTask: null,
                selectedTransform: null
            });
        }
        case IMPORT_RUN_SUCCESS: {
            return state;
        }
        case IMPORT_RUN_ERROR: {
            return state;

        }
        case IMPORTS_TASK_LOADED: {
            return assign({}, state, {
                selectedTask: action.task,
                selectedTransform: null
            });
        }
        case IMPORTS_TASK_DELETE: {
            let task = state.selectedTask;
            let selectedImport = state.selectedImport;
            if (task && task.id === action.taskId && selectedImport && selectedImport.id === action.importId) {
                task = null;
            }
            if (selectedImport && selectedImport.id === action.importId) {
                selectedImport = assign({}, selectedImport);
                selectedImport.tasks = selectedImport.tasks.filter((tasko) => tasko.id !== action.taskId);
            }
            return assign({}, state, {
                selectedTask: task,
                selectedImport
            });
        }
        case IMPORT_DELETE: {
            let imports = state && state.imports;
            let importIndex = imports && findIndex(imports, (imp) => imp.id === action.id);
            if (importIndex >= 0) {
                imports = state.imports.filter((imp) => imp.id !== action.id);
            }
            if (state && state.selectedImport && state.selectedImport.id === action.id) {
                return assign({}, state, {
                    imports,
                    selectedImport: null,
                    selectedTask: null,
                    selectedTransform: null
                });
            }
            return assign({}, state, {
                imports
            });
        }
        case IMPORT_DELETE_ERROR: {
            let imports = state && state.imports;
            imports = imports && imports.map((imp) => {
                if (imp.id === action.id) {
                    return {...imp, error: action.error};
                }
                return imp;
            });
            return assign({}, state, {
                imports
            });
        }
        case IMPORTS_FILE_UPLOADED: {
            return assign({}, state, {
                uploading: false
            });
        }
        case IMPORTS_UPLOAD_PROGRESS: {
            return assign({}, state, {
                uploading: {
                    progress: action.progress
                }
            });
        }
        case IMPORTER_WORKSPACE_LOADED: {
            return assign({}, state, {
                workspaces: action.workspaces
            });
        }
        case IMPORTER_WORKSPACE_SELECTED: {
            return assign({}, state, {
                selectedWorkSpace: action.workspace
            });
        }
        case IMPORTER_WORKSPACE_CREATED: {
            let workspaces = state.workspaces.concat({
                name: action.name,
                href: action.href
            });
            return assign({}, state, {
                workspaces,
                workspaceCreationStatus: {status: "success", workspace: action.name}
            });
        }
        case IMPORTER_WORKSPACE_CREATION_ERROR: {
            return assign({}, state, {
                workspaceCreationStatus: {status: "error", error: action.error}
            });
        }
        case IMPORTER_WORKSPACE_STATUS_CHANGE: {
            return assign({}, state, {
                workspaceCreationStatus: action.state
            });
        }
        default:
            return state;
    }
}

module.exports = importer;
