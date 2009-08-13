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
	container.addEventListener("TabSelect", tabSelected, false);

    },
   
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);

function tabSelected(event) {
    updateStatusIcon(); 
}

function updateStatusIcon() {
    //log("current domain is PACER domain? " + isPACERHost(gBrowser.selectedBrowser.contentDocument.domain));
  
    var statusIcon = document.getElementById("recap-panel-image");
  
    if (isPACERHost(gBrowser.selectedBrowser.contentDocument.domain) && 
	havePACERCookie()) {
	statusIcon.src = ICON_LOGGED_IN;
	statusIcon.tooltipText = "You are logged into PACER.";

    } else {
	statusIcon.src= ICON_LOGGED_OUT;
	statusIcon.tooltipText = "You are logged out of PACER.";
    }
}

function openPrefs() {
    window.openDialog("chrome://recap/content/options.xul", 
		      "Preferences", 
		      "chrome=yes,titlebar=yes,toolbar=yes,centerscreen");
}



