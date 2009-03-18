var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	this.strings = document.getElementById("recap-strings");
	
	var recapPanel = document.getElementById('recap-panel');

	var recapService =
Components.classes["@cs.princeton.edu/recap;1"].getService().wrappedJSObject;
	
	recapService.setXULDOM(recapPanel);
	
    },
    
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);

