var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	this.strings = document.getElementById("recap-strings");
	
	var recapPanel = document.getElementById('recap-panel');

	var recapService = Cc["@cs.princeton.edu/recap;1"]
	                    .getService().wrappedJSObject;
	
	recapService.setStatusXUL(recapPanel);
	
    },
    
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);

