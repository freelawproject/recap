var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
				     
	var container = gBrowser.tabContainer;
	container.addEventListener("TabSelect", exampleTabSelected, false);

    },
    
};


window.addEventListener("load", function(e) { recap.onLoad(e); }, false);


function exampleTabSelected(event)
{
  updateStatusIcon(); 
}

function updateStatusIcon() {
  //log("current domain is PACER domain? " + isPACERHost(gBrowser.selectedBrowser.contentDocument.domain));
  
  var statusIcon = document.getElementById("recap-panel-image");
  
  	if (isPACERHost(gBrowser.selectedBrowser.contentDocument.domain) && havePACERCookie()) {
	    statusIcon.src = ICON_LOGGED_IN;
	    statusIcon.tooltipText = "You are logged into PACER.";

	} else {
	    statusIcon.src= ICON_LOGGED_OUT;
	    statusIcon.tooltipText = "You are logged out of PACER.";
	}
}

function openPrefs() {
	window.openDialog("chrome://recap/content/options.xul", "Preferences", "chrome=yes,titlebar=yes,toolbar=yes,centerscreen");
}



