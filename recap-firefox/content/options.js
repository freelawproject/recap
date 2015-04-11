/* eslint-env browser */
/* global Components */

function toggleRadioButtons(){
    "use strict";
    var fileNamesEnabled = window.document.getElementById("pretty_filenames").checked;
    var radiogroup = window.document.getElementById("pretty_filenames_choices");
    if(fileNamesEnabled === true){
        radiogroup.removeAttribute("disabled");
        radiogroup.disabled = false;
    } else {
        radiogroup.disabled = true;
        radiogroup.setAttribute("disabled", true);
    }
}

function checkForGrowlAndNotify(){
    // Returns "WINNT" on Windows Vista, XP, 2000, and NT systems;
    // "Linux" on GNU/Linux; and "Darwin" on Mac OS X.
    "use strict";
    try {
        var osString = Components
          .classes["@mozilla.org/xre/app-info;1"]
          .getService(Components.interfaces.nsIXULRuntime)
          .OS;
    } catch (e) {
    }

    if (osString === "Darwin") {
        var growlWarnMessage = window.document.getElementById("growlWarn");
        try {
            Components
              .classes["@mozilla.org/alerts-service;1"]
              .getService(Components.interfaces.nsIAlertsService);
        } catch (e) {
            growlWarnMessage.value = "Alert: Growl must be installed and active: http://growl.info/";
        }
    }
}

window.onload = function() {
    "use strict";
    toggleRadioButtons(); //initially set
    checkForGrowlAndNotify();
};
