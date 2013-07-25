var dataObject;
var data;
var options;
var minuteOffset = new Date().getTimezoneOffset();
var offset = -60 * minuteOffset * 1000.0; 

function SentData() { 

    this.tweetPercents= {
                label: "Percent of Total",
                data: [],
                lines: {show: true}
                //label: "Count",
                //points: {show: true}
            };
//    this.tweetSents = {
//                label: "Tweet Sentiment",
//                data: [],
//                lines: {show: true},
//                yaxis: 2
//                //label: "Sentiment",
//                //points: {show: true}
//            };
}


function initChartData(domainStart, domainEnd) {
    console.log(domainStart);
    console.log(domainEnd);

    data = new SentData();
    var timeFormat = "%m/%d %H:%M" 
    //if ((domainEnd - domainStart) > 300000000.0)
    //    timeFormat = "%Y-%m-%d";

    options = { 
        xaxes: [{
            mode: "time",
            timeformat: timeFormat,
            //zoomRange: [1329403094000.0, 1341100805000.0],
            zoomRange: null, 
            panRange: [domainStart, domainEnd],
        }],
        yaxes: [{
            min: 0,
            zoomRange: false,
            panRange: false
        }, 
        {min: 0, 
        zoomRange: false, 
        panRange: false,
        position:"right"}],
        zoom: {
            interactive: true
        },
        pan: {
            interactive: true,
            frameRate: 20
        }


    };
}


/*
function makeRandomData(numSteps) {

    series1.data = [ [], [] ]; 
    if (numSteps > 0) {
        series1.data = [];
        var baseValue = 20 + Math.floor(Math.random() * 70);
        var baseTime = (new Date()).getTime() - (numSteps + 1) * 1000;
        series1.data.push([baseTime, baseValue]);
        for (var i = 1; i < numSteps; i++) {
            var x = series1.data[i-1][0] + 1000;
            var y = Math.min(100, Math.max(0,Math.round(series1.data[i-1][1] * ((Math.random() * 0.2) + 0.9)))); 
            series1.data.push([x,y]);
        }
    }
}
*/

function processGraphData(stats, mode ) {
    var dataVar;
    var modePercent = mode == "percent";
    console.log(mode);
    if (modePercent)
        data.tweetPercents.data = []
    else
        data.tweetSents.data = []

    var counts = stats["count"];
    var domain = stats["x"];
    var range = stats["y"];
    console.log(domain);
    console.log(counts);
    console.log(range);
    numElems = counts.length;
    console.log(numElems);

    for (var i = 0; i != numElems; i++) {
        var time = domain[i] * 1000.0 + offset;
        //data.tweetCounts.data.push([time,counts[i]]);
        if (counts[i] == 0) {
            if (modePercent == true)
                data.tweetPercents.data.push([time, null]);
//            else
//                date.tweetSents.data.push([time, null]);
        }
        else {
            if (modePercent == true)
                data.tweetPercents.data.push([time, range[i] * 100.0]);
//            else
//                data.tweetSents.data.push([time, range[i]]);
        }
    }

    drawGraph();
}

    
    /*





    var instanceKeys = Object.keys(instancesData); 
    var start = parseInt(stats["start"]);
    var end = parseInt(stats["end"]);
    if (stats["stats"] == null)
        stats["stats"] = {};
    
    for (var i = 0; i < instanceKeys.length; i++) {
        var instanceId = instanceKeys[i];
        if (stats["stats"][instanceId] != null) {
            for (var sec = start; sec < end; sec++) {
                if (sec in stats["stats"][instanceId]) {
                    instancesData[instanceId].tweetsCollected.data.push([sec * 1000 - gmtOffset,stats["stats"][instanceId][sec][0]]);
                    instancesData[instanceId].tweetsInserted.data.push([sec * 1000 - gmtOffset,stats["stats"][instanceId][sec][1]]);
                            
                }
                else {
                    instancesData[instanceId].tweetsCollected.data.push([sec * 1000 - gmtOffset,0]);
                    instancesData[instanceId].tweetsInserted.data.push([sec * 1000 - gmtOffset,0]);
                }
            }
        }
        else {
            for (var sec = start; sec < end; sec++) {
                instancesData[instanceId].tweetsCollected.data.push([sec * 1000 - gmtOffset,0]);
                instancesData[instanceId].tweetsInserted.data.push([sec * 1000 - gmtOffset,0]);
            }
        }

        var tweetsCollectedLen =  instancesData[instanceId].tweetsCollected.data.length;
        if (tweetsCollectedLen > 1800) {
            instancesData[instanceId].tweetsCollected.data = instancesData[instanceId].tweetsCollected.data.splice(tweetsCollectedLen - 1800);
            tweetsCollectedLen =  instancesData[instanceId].tweetsCollected.data.length;
        }

        var tweetsInsertedLen =  instancesData[instanceId].tweetsInserted.data.length;
        if (tweetsInsertedLen > 1800) {
            instancesData[instanceId].tweetsInserted.data = instancesData[instanceId].tweetsInserted.data.splice(tweetsInsertedLen - 1800);
            tweetsInsertedLen =  instancesData[instanceId].tweetsInserted.data.length;
        }

        if (instanceId != "total") {
            var sparkId = "#sparkCell" + instanceId;
            var numGraphPoints = Math.min(30, tweetsCollectedLen);
            var graphValues = []
            for (var p = 0; p < numGraphPoints; p++) {
                graphValues.unshift(instancesData[instanceId].tweetsCollected.data[tweetsCollectedLen - 1 - p][1]);
            }
            $(sparkId).sparkline(graphValues);

        }


    }
    options.xaxis.min = (end -120) * 1000 - gmtOffset;
    */



function drawGraph() {
    //dataObject = [data.tweetPercents, data.tweetSents];
    dataObject = [data.tweetPercents];
    $.plot($("#chart"), dataObject, options);
}
