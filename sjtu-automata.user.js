// ==UserScript==
// @name         sjtu-automata
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  show classid under classname.
// @author       MXWXZ
// @match        *://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbIndex.html*
// @match        *://i.sjtu.edu.cn/design/viewFunc_cxDesignFuncPageIndex.html*
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

function showid(node) {
    node.children('.jxbmc').append('<br><button type="button" class="btn btn-primary btn-sm" onclick="copyid(this)">复制ID</button>');
}

function showid2(node) {
    node.show();
}

(function () {
    'use strict';

    if (location.href.indexOf("zzxkyzb_cxZzxkYzbIndex") > -1) {
        var script = document.createElement("script");
        script.type = "text/javascript";
        script.appendChild(document.createTextNode("function copyid(t) {const el = document.createElement('textarea');el.value =t.parentNode.parentNode.childNodes[2].innerHTML+' '+t.parentNode.parentNode.childNodes[1].innerHTML;document.body.appendChild(el);el.select();document.execCommand('copy');document.body.removeChild(el);alert(\"copy ok\");}"));
        document.body.appendChild(script);

        let node = $('.nav.nav-tabs.sl_nav_tabs li');
        node.each(function () {
            let str = $(this).children('a')[0].getAttribute("onclick");
            let pos1 = str.indexOf("this,'");
            let pos2 = str.indexOf("','");
            $(this).append('<p>' + str.substr(str.indexOf("this,'") + 6, pos2 - pos1 - 6) + ' &nbsp;</p>');
        });
        waitForKeyElements('.body_tr', showid, false);
    }
    /*
    To be fix
    else if(location.href.indexOf("viewFunc_cxDesignFuncPageIndex") > -1) {
        $('[id$=_jxb_id]').show();
        $('[id$=_jxb_id]').css('width','270px');
        let row=$('.jqgfirstrow').children('td:eq(1)');
        row.show();
        row.css('width','270px');
        waitForKeyElements("[aria-describedby$='_jxb_id']", showid2, false);
    }
    */
})();
