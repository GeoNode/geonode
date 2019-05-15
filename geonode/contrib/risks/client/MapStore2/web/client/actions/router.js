/**
 * Copyright 2016, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */
const GO_TO_PAGE = 'GO_TO_PAGE';


function goToPage(page, router) {
    if (router) {
        router.push(page);
    }
    return {
        type: GO_TO_PAGE,
        page
    };
}
module.exports = {GO_TO_PAGE, goToPage};
