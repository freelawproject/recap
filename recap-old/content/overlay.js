var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	
	//var recapPanel = document.getElementById('recap-panel');

	var recapService = Cc["@cs.princeton.edu/recap;1"]
	                    .getService().wrappedJSObject;
	
	gBrowser.addProgressListener(recapService.getContentListener(),
				     Ci.nsIWebProgress.NOTIFY_LOCATION);

    },
    
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);

