
/*
 * Envjs timer.1.2.13 
 * Pure JavaScript Browser Environment
 * By John Resig <http://ejohn.org/> and the Envjs Team
 * Copyright 2008-2010 John Resig, under the MIT License
 * 
 * Parts of the implementation were originally written by:\
 * Steven Parkes
 * 
 * requires Envjs.wait, Envjs.sleep, Envjs.WAIT_INTERVAL
 */
var setTimeout,
    clearTimeout,
    setInterval,
    clearInterval;
    
/*
 * Envjs timer.1.2.13 
 * Pure JavaScript Browser Environment
 * By John Resig <http://ejohn.org/> and the Envjs Team
 * Copyright 2008-2010 John Resig, under the MIT License
 */

//CLOSURE_START
(function(){




/*
*       timer.js
*   implementation provided by Steven Parkes
*/

//private
var $timers = [],
    EVENT_LOOP_RUNNING = false;

$timers.lock = function(fn){
    Envjs.sync(fn)();
};

//private internal class
var Timer = function(fn, interval){
    this.fn = fn;
    this.interval = interval;
    this.at = Date.now() + interval;
    // allows for calling wait() from callbacks
    this.running = false;
};

Timer.prototype.start = function(){};
Timer.prototype.stop = function(){};

//static
Timer.normalize = function(time) {
    time = time*1;
    if ( isNaN(time) || time < 0 ) {
        time = 0;
    }

    if ( EVENT_LOOP_RUNNING && time < Timer.MIN_TIME ) {
        time = Timer.MIN_TIME;
    }
    return time;
};
// html5 says this should be at least 4, but the parser is using
// a setTimeout for the SAX stuff which messes up the world
Timer.MIN_TIME = /* 4 */ 0;

/**
 * @function setTimeout
 * @param {Object} fn
 * @param {Object} time
 */
setTimeout = function(fn, time){
    var num;
    time = Timer.normalize(time);
    $timers.lock(function(){
        num = $timers.length+1;
        var tfn;
        if (typeof fn == 'string') {
            tfn = function() {
                try {
                    // eval in global scope
                    eval(fn, null);
                } catch (e) {
                    console.log('timer error %s %s', fn, e);
                } finally {
                    clearInterval(num);
                }
            };
        } else {
            tfn = function() {
                try {
                    fn();
                } catch (e) {
                    console.log('timer error %s %s', fn, e);
                } finally {
                    clearInterval(num);
                }
            };
        }
        //console.log("Creating timer number %s", num);
        $timers[num] = new Timer(tfn, time);
        $timers[num].start();
    });
    return num;
};

/**
 * @function setInterval
 * @param {Object} fn
 * @param {Object} time
 */
setInterval = function(fn, time){
    //console.log('setting interval %s %s', time, fn.toString().substring(0,64));
    time = Timer.normalize(time);
    if ( time < 10 ) {
        time = 10;
    }
    if (typeof fn == 'string') {
        var fnstr = fn;
        fn = function() {
            eval(fnstr);
        };
    }
    var num;
    $timers.lock(function(){
        num = $timers.length+1;
        //Envjs.debug("Creating timer number "+num);
        $timers[num] = new Timer(fn, time);
        $timers[num].start();
    });
    return num;
};

/**
 * clearInterval
 * @param {Object} num
 */
clearInterval = clearTimeout = function(num){
    //console.log("clearing interval "+num);
    $timers.lock(function(){
        if ( $timers[num] ) {
            $timers[num].stop();
            delete $timers[num];
        }
    });
};

// wait === null/undefined: execute any timers as they fire,
//  waiting until there are none left
// wait(n) (n > 0): execute any timers as they fire until there
//  are none left waiting at least n ms but no more, even if there
//  are future events/current threads
// wait(0): execute any immediately runnable timers and return
// wait(-n): keep sleeping until the next event is more than n ms
//  in the future
//
// TODO: make a priority queue ...

Envjs.wait = function(wait) {
    //console.log('wait %s', wait);
    var delta_wait,
        start = Date.now(),
        was_running = EVENT_LOOP_RUNNING;

    if (wait < 0) {
        delta_wait = -wait;
        wait = 0;
    }
    EVENT_LOOP_RUNNING = true;
    if (wait !== 0 && wait !== null && wait !== undefined){
        wait += Date.now();
    }

    var earliest,
        timer,
        sleep,
        index,
        goal,
        now,
        nextfn;

    for (;;) {
        //console.log('timer loop');
        earliest = sleep = goal = now = nextfn = null;
        $timers.lock(function(){
            for(index in $timers){
                if( isNaN(index*0) ) {
                    continue;
                }
                timer = $timers[index];
                // determine timer with smallest run-at time that is
                // not already running
                if( !timer.running && ( !earliest || timer.at < earliest.at) ) {
                    earliest = timer;
                }
            }
        });
        //next sleep time
        sleep = earliest && earliest.at - Date.now();
        if ( earliest && sleep <= 0 ) {
            nextfn = earliest.fn;
            try {
                //console.log('running stack %s', nextfn.toString().substring(0,64));
                earliest.running = true;
                nextfn();
            } catch (e) {
                console.log('timer error %s %s', nextfn, e);
            } finally {
                earliest.running = false;
            }
            goal = earliest.at + earliest.interval;
            now = Date.now();
            if ( goal < now ) {
                earliest.at = now;
            } else {
                earliest.at = goal;
            }
            continue;
        }

        // bunch of subtle cases here ...
        if ( !earliest ) {
            // no events in the queue (but maybe XHR will bring in events, so ...
            if ( !wait || wait < Date.now() ) {
                // Loop ends if there are no events and a wait hasn't been
                // requested or has expired
                break;
            }
        // no events, but a wait requested: fall through to sleep
        } else {
            // there are events in the queue, but they aren't firable now
            /*if ( delta_wait && sleep <= delta_wait ) {
                //TODO: why waste a check on a tight
                // loop if it just falls through?
            // if they will happen within the next delta, fall through to sleep
            } else */if ( wait === 0 || ( wait > 0 && wait < Date.now () ) ) {
                // loop ends even if there are events but the user
                // specifcally asked not to wait too long
                break;
            }
            // there are events and the user wants to wait: fall through to sleep
        }

        // Related to ajax threads ... hopefully can go away ..
        var interval =  Envjs.WAIT_INTERVAL || 100;
        if ( !sleep || sleep > interval ) {
            sleep = interval;
        }
        //console.log('sleeping %s', sleep);
        Envjs.sleep(sleep);

    }
    EVENT_LOOP_RUNNING = was_running;
};


/**
 * @author john resig & the envjs team
 * @uri http://www.envjs.com/
 * @copyright 2008-2010
 * @license MIT
 */
//CLOSURE_END
}());
