/* eslint-env browser */
/* globals gBrowser, CCGS */

var recap = {
    onLoad: function() {
        "use strict";
        // initialization code
        this.initialized = true;

        var container = gBrowser.tabContainer;
        container.addEventListener("TabSelect", this.tabSelected, false);

        //For ff4, we need to add our icon to the addon bar
        var prefs = CCGS(
          "@mozilla.org/preferences-service;1",
          "nsIPrefService"
        ).getBranch("extensions.recap.");

        var hasBeenInitialized = prefs.getBoolPref("has_been_initialized");

        if(!hasBeenInitialized){
            var addonBar = document.getElementById("addon-bar");

            if(addonBar) {
                var currentSet = addonBar.currentSet;
                if (currentSet.indexOf("recap-panel") === -1) {
                    addonBar.currentSet += ",recap-panel";
                    addonBar.setAttribute("currentset", addonBar.currentSet);
                    document.persist("addon-bar", "currentset");
                    addonBar.collapsed = false;
                }
                prefs.setBoolPref("has_been_initialized", true);
            }
        }
    },

    tabSelected: function(event){
        "use strict";
        updateStatusIcon();
    },
    openPrefs: function(){
        window.openDialog(
          "chrome://recap/content/options.xul",
          "Preferences",
          "chrome=yes,titlebar=yes,toolbar=yes,centerscreen"
        );
    }
};

window.addEventListener(
  "load",
  function(e) {recap.onLoad(e); },
  false
);
