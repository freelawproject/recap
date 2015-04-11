/* 
 *  This file is part of the RECAP Firefox Extension.
 *
 *  Copyright 2009 Harlan Yu, Timothy B. Lee, Stephen Schultze.
 *  Website: http://www.recapthelaw.org
 *  E-mail: info@recapthelaw.org
 *
 *  The RECAP Firefox Extension is free software: you can redistribute it 
 *  and/or modify it under the terms of the GNU General Public License as
 *  published by the Free Software Foundation, either version 3 of the 
 *  License, or (at your option) any later version.
 *
 *  The RECAP Firefox Extension is distributed in the hope that it will be
 *  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with the RECAP Firefox Extension.  If not, see 
 *  <http://www.gnu.org/licenses/>.
 *
 */

var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	
	var container = gBrowser.tabContainer;
	container.addEventListener("TabSelect", this.tabSelected, false);

    //For ff4, we need to add our icon to the addon bar
    var prefs = CCGS("@mozilla.org/preferences-service;1",
                        "nsIPrefService").getBranch("extensions.recap.");
       
    var has_been_initialized = prefs.getBoolPref("has_been_initialized");

    if(!has_been_initialized){
        var addonBar = document.getElementById("addon-bar");

        if(addonBar) {
            var currentSet = addonBar.currentSet;
            if (currentSet.indexOf("recap-panel") == -1) {
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
        updateStatusIcon(); 
    },
    openPrefs: function(){
        window.openDialog("chrome://recap/content/options.xul", 
		          "Preferences", 
		          "chrome=yes,titlebar=yes,toolbar=yes,centerscreen");
    }
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);
