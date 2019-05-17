/**
 * Copyright 2017, GeoSolutions Sas.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree.
 */

const {Promise} = require('es6-promise');
const canvg = require('canvg-browser');
const html2canvas = require('html2canvas');
function chartToImg(svgs) {
    return Promise.all([].slice.call(svgs, 0, 2).map((svg, idx) => {
        return new Promise((resolve, reject) => {
            let svgOffsetX;
            let svgOffsetY;
            let svgH;
            let svgW;
            const svgCanv = document.createElement('canvas');
            const svgString = svg.outerHTML;
            [svgOffsetX = 0, svgOffsetY = 0, svgW =0, svgH = 0] = svg.getAttribute('viewBox').split(' ');
            svg.setAttribute("style", "");
            svgOffsetX = svgOffsetX ? svgOffsetX : 0;
            svgOffsetY = svgOffsetY ? svgOffsetY : 0;
            svgCanv.setAttribute("width", svgW);
            svgCanv.setAttribute("height", svgH);
            svgCanv.getContext('2d').scale(2, 2);
            canvg(svgCanv, svgString, {
                ignoreMouse: true,
                ignoreAnimation: true,
                ignoreDimensions: false,
                ignoreClear: true,
                offsetX: svgOffsetX,
                offsetY: svgOffsetY,
                renderCallback: () => {
                    try {
                        const data = svgCanv.toDataURL("image/png");
                        resolve({name: `chart_${idx}`, data});
                    }catch (e) {
                        reject(e);
                    }
                }
            });
        });
    })).then((result) => {
        return {name: 'charts', data: result};
    }).catch ((e) => {throw e; });
}
function legendToImg(img) {
    return new Promise(function(resolve, reject) {
        html2canvas(img, {
            logging: false,
            allowTaint: false,
            useCORS: true,
            removeContainer: true
        }).then((canvas) => {
            if (img.height !== canvas.height) {
                reject(new Error("Error in legend generation"));
            }else {
                try {
                    const data = canvas.toDataURL("img/png");
                    // window.open(data, '_blank');
                    resolve({name: 'legend', data});
                }catch (e) {
                    reject(e);
                }
            }
        }).catch((e) => {
            reject(e);
        });
    });
}
module.exports = {chartToImg, legendToImg};
