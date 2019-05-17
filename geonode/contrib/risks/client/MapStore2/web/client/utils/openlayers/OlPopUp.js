/**
 * Copyright 2015, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

require('./olPopUp.css');

let popUp = function() {
    let pop = document.createElement('div');
    pop.setAttribute("class", "ol-popup");
    let popDismis = document.createElement('a');
    popDismis.setAttribute("class", "ol-popup-close-btn");
    popDismis.setAttribute("href", "#close");
    popDismis.innerHTML = "x";
    let popCntWrap = document.createElement('div');
    popCntWrap.setAttribute("class", "ol-popup-cnt-wrapper");
    let popCnt = document.createElement('div');
    popCnt.setAttribute("class", "ol-popup-cnt");
    popCntWrap.appendChild(popCnt);
    let popTipWrap = document.createElement('div');
    popTipWrap.setAttribute("class", "ol-popup-tip-wrapper");
    let popTip = document.createElement('div');
    popTip.setAttribute("class", "ol-popup-tip");
    popTipWrap.appendChild(popTip);
    pop.appendChild(popDismis);
    pop.appendChild(popCntWrap);
    pop.appendChild(popTipWrap);
    return pop;
};
module.exports = popUp;
