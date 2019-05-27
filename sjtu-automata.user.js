// ==UserScript==
// @name         sjtu-automata
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  show classid under classname.
// @author       MXWXZ
// @match        *://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbIndex.html*
// @homepageURL  https://github.com/MXWXZ/sjtu-automata/
// @supportURL   https://github.com/MXWXZ/sjtu-automata/issues/
// @downloadURL  https://raw.githubusercontent.com/MXWXZ/sjtu-automata/master/sjtu-automata.user.js
// @updateURL    https://raw.githubusercontent.com/MXWXZ/sjtu-automata/master/sjtu-automata.user.js
// @grant        none
// ==/UserScript==

function waitForKeyElements(selectorTxt, actionFunction, bWaitOnce, iframeSelector) {
    var targetNodes, btargetsFound;
    if (typeof iframeSelector == "undefined")
        targetNodes = jQuery(selectorTxt);
    else
        targetNodes = jQuery(iframeSelector).contents()
            .find(selectorTxt);

    if (targetNodes && targetNodes.length > 0) {
        btargetsFound = true;
        targetNodes.each(function () {
            var jThis = jQuery(this);
            var alreadyFound = jThis.data('alreadyFound') || false;

            if (!alreadyFound) {
                var cancelFound = actionFunction(jThis);
                if (cancelFound)
                    btargetsFound = false;
                else
                    jThis.data('alreadyFound', true);
            }
        });
    }
    else {
        btargetsFound = false;
    }

    var controlObj = waitForKeyElements.controlObj || {};
    var controlKey = selectorTxt.replace(/[^\w]/g, "_");
    var timeControl = controlObj[controlKey];

    if (btargetsFound && bWaitOnce && timeControl) {
        clearInterval(timeControl);
        delete controlObj[controlKey]
    }
    else {
        if (!timeControl) {
            timeControl = setInterval(function () {
                waitForKeyElements(selectorTxt,
                    actionFunction,
                    bWaitOnce,
                    iframeSelector
                );
            }, 300);
            controlObj[controlKey] = timeControl;
        }
    }
    waitForKeyElements.controlObj = controlObj;
}

function showid(node){
    let id=node.children().children()[0].innerHTML;
    node.children('.jxbmc').append('<p>'+id+'</p>');
}

(function() {
    'use strict';

    let node=$('.nav.nav-tabs.sl_nav_tabs li');
    node.each(function(){
        let str=$(this).children('a')[0].getAttribute("onclick");
        $(this).append('<p>'+str.substr(str.indexOf("','")+3,32)+' &nbsp;</p>');
    });
    waitForKeyElements('.body_tr', showid, false);
})();