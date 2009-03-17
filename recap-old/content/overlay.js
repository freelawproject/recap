var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	this.strings = document.getElementById("recap-strings");
	
	// once we combine XPCOM and overlay, we can reset the status bar like:
	//var recapPanel = document.getElementById('recap-panel'); 
	//recapPanel.label="foo";
	
    },
    
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);

