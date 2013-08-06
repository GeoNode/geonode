//var host = "http://192.168.1.90:8083"
var host = "http://geops.csail.mit.edu:8083"
//var host = "http://geops.cga.harvard.edu:8083";
//var epochStart = "1350259200"
//var epochEnd = "1350345599"
//var epochStart = 1354318270
//var epochEnd = 1354459598
//var epochStart = 1350259200
//var epochEnd = 1354579199
var epochStart = Math.floor(new Date(2012,9,1).getTime() / 1000);
var epochEnd =  Math.floor(new Date(Date.now() + 86400000).getTime() / 1000);
var numBins = 500;
var graphBounds= [ -124.76,  24.52, -66.93,49.38];
var dataObject;
var data;
var options;
var minuteOffset = new Date().getTimezoneOffset();
var offset = -60 * minuteOffset * 1000.0; 

/*
var operatorMap = {
"bool": ["="],
"int": ["=", "+", "-", "<", "<=", ">", ">="],
"unsigned int": ["=", "+", "-", "<", "<=", ">", ">="], 
"unsigned long": ["=", "+", "-", "<", "<=", ">", ">="], 
"float": ["=", "+", "-", "<", "<=", ">", ">="], 
"double": ["=", "+", "-", "<", "<=", ">", ">="], 
"string": ["like", "iLike", "not like", "not ilike"]
};
*/

function SentData() {

    this.tweetPercents= {
        label: "Percent of Total",
        data: [],
        lines: {show: true}
        //label: "Count",
        //points: {show: true}
    }
//    this.tweetSents = {
//                label: "Tweet Sentiment",
//                data: [],
//                lines: {show: true},
//                yaxis: 2
//                //label: "Sentiment",
//                //points: {show: true}
//            };
}


function initData (domainStart, domainEnd) {

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
            panRange: [domainStart, domainEnd]
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
    if (modePercent)
        data.tweetPercents.data = []
    else
        data.tweetSents.data = []

    var counts = stats["count"];
    var domain = stats["x"];
    var range = stats["y"];
    numElems = counts.length;

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


function RequestInfo (params) {
	// takes path, processor, args callBackTimer
	this.path = params.path;
	this.processor = typeof params.processor !== 'undefined' ? params.processor: null;
	this.args = typeof params.args !== 'undefined' ? params.args: null; // args should usually be an array
	this.callBackTimer = typeof params.callBackTimer !== 'undefined' ? params.callBackTimer: null;
	//this.callBackTimer = callBackTimer;
}



function makeRequest(requestInfo) {
	var xhr = new XMLHttpRequest ();
	var path = requestInfo.path;
	if (requestInfo.args != null) {
	    path += "?"; 
	    for (var i = 0; i < requestInfo.args.length; i++) {
		path += jQuery.param(requestInfo.args[i]);
	    }
	}

	    //for (var i = 0; i < requestInfo.args.length; i++) {
	    //    path += requestInfo.args[i];
	    
	xhr.open("GET", path);
	xhr.onreadystatechange = function () {
	    if (xhr.readyState === 4) {
		var status = xhr.status;
		if ((status >= 200 && status < 300) || status === 304) {
		    if (requestInfo.processor != null)
			requestInfo.processor(xhr.responseText);
		}
		else {
		    alert("Error making request");
		}
		    
	   }
	}

	xhr.send(null);

	if (requestInfo.callBackTimer != null) {
	   setTimeout(function(){makeRequest(requestInfo)}, requestInfo.callBackTimer);
	}
}


function getSent (histStart, histEnd, histBins) {
    var token = encodeURIComponent($("#tweetFilter")[0].value.replace("&",""));
    var sqlRequest = "select time, sent from eg_sent where tweet ilike '" + token + "'"
    var request = host +  "/?Request=Graph&SQL="+sqlRequest + "&histStart=" + histStart + "&histEnd=" + histEnd + "&histBins=" + histBins;

    var getSentRequest = new RequestInfo( {path: request, processor: processSent});     
    makeRequest(getSentRequest);
}
    
function processSent(data) {
    var sentStats = JSON.parse(data);
    processGraphData(sentStats, "sent");
}

function getPercent (histStart, histEnd, histBins) {
    var preToken =  $("#tweetFilter")[0].value.replace("'", "''").replace("&","")
    var token = encodeURIComponent(preToken);
    
    var sqlRequest = "select time, tweet_text ilike '" + token + "' from tweets where time > " + histStart + " and time < " + histEnd + " and goog_x > " + graphBounds[0] + " and goog_x < " + graphBounds[2]  + " and goog_y > " + 
graphBounds[1] + " and goog_y < " + graphBounds[3];
    var request = host +  "/?Request=Graph&SQL="+sqlRequest + "&histStart=" + histStart + "&histEnd=" + histEnd + "&histBins=" + histBins;
    var getPercentRequest = new RequestInfo( {path: request, processor: processPercent});     
    makeRequest(getPercentRequest);
}
    
function processSent(data) {
    var sentStats = JSON.parse(data);
    processGraphData(sentStats, "sent");
}

function processPercent(data) {
    var percentStats = JSON.parse(data);
    processGraphData(percentStats, "percent");
}

function sendQuery(histStart, histEnd, histBins) {
    var stringStart = histStart.toString();
    var stringEnd = histEnd.toString();
    var stringBins = histBins.toString();
    getPercent(stringStart, stringEnd, stringBins);
    //getSent(histStart, histEnd, histBins);
}

function initGraph() {
    $("#numBinsSlider").slider({
        min:4,
        max:1000,
        value:500,
        slide: function (event, ui) {
            numBins = ui.value;
            //sendQuery(true, false);
        },
        stop: function( event, ui ) {
            sendQuery(epochStart, epochEnd, numBins);
        }
    });
    $("#numBinsSlider").width(300);
    initData (epochStart * 1000.0, epochEnd * 1000.0);
    //sendQuery("1329403094", "13411la00805", 60);
    sendQuery(epochStart, epochEnd, numBins);
    $("#tweetFilter").keypress(function(event) {
        var keycode = (event.keyCode ? event.keyCode : event.which);
        if (keycode == '13') {
            sendQuery(epochStart, epochEnd, numBins);
        }
    });
}
