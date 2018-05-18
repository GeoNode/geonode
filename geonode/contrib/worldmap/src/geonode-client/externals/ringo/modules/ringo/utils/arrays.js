/*
 * Copyright 1998-2006 Helma Project
 * Copyright 2010 Hannes Wallnöfer
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

/**
 * @fileoverview Provides utility functions for working with JavaScript Arrays.
 */

export('contains', 'peek', 'remove', 'union', 'intersection', 'max', 'min', 'partition');

/**
 * Check if an array passed as argument contains
 * a specific value (start from end of array).
 * @param {Array} array the array
 * @param {Object} val the value to check
 * @returns {boolean} true if the value is contained
 */
function contains(array, val) {
       return array.indexOf(val) > -1;
}

/**
 * Return the last element of the array. This is like pop(), but
 * without modifying the array.
 * @param {Array} array the array
 * @returns {Object} the last element of the array, or undefined if the array is empty.
 */
function peek(array) {
    return array[array.length - 1];
}

/**
 * Remove the first occurrence of the argument value from the array. This method
 * mutates and returns the array on which it is called and does not create a
 * new array instance.
 * @param {Array} array the array
 * @param {Object} val the value to remove
 * @returns {Array} the array
 */
function remove(array, val) {
    var index = array.indexOf(val);
    if(index > -1) {
        array.splice(index, 1);
    }
    return array;
}

/**
 * Retrieve the union set of a bunch of arrays.
 * @param {Array} array1,... the arrays to unify
 * @returns {Array} the union set
 */
function union() {
    var result = [];
    var map = new java.util.HashMap();
    for (var i = 0; i < arguments.length; i += 1) {
        for (var n in arguments[i]) {
            var item = arguments[i][n];
            if (!map.containsKey(item)) {
                result.push(item);
                map.put(item, true);
            }
        }
    }
    return result;
}

/**
 * Retrieve the intersection set of a bunch of arrays.
 * @param {Array} array1,... the arrays to intersect
 * @returns {Array} the intersection set
 */
function intersection(array) {
    var all = union.apply(null, arguments);
    var result = [];
    for (var n in all) {
        var chksum = 0;
        var item = all[n];
        for (var i = 0; i < arguments.length; i += 1) {
            if (contains(arguments[i], item))
                chksum += 1;
            else
                break;
        }
        if (chksum == arguments.length)
            result.push(item);
    }
    return result;
}

/**
 * @param {Array} array the array
 * @returns the maximal element in an array obtained by calling Math.max().
 */
function max(array) {
    return Math.max.apply(Math, array);
}

/**
 * @param {Array} array the array
 * @returns the minimal element in an array obtained by calling Math.min().
 */
function min(array) {
    return Math.min.apply(Math, array);
}

function partition(fn) {
    var trues = [], falses = [];
    for (var i=0; i<this.length; i++) {
        if (fn(this[i], i)) {
            trues.push(this[i]);
        } else {
            falses.push(this[i]);
        }
    }
    return [trues, falses]
}
