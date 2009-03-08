var recap = {
    
    onLoad: function() {
	// initialization code
	this.initialized = true;
	this.strings = document.getElementById("recap-strings");
    },
    
};

window.addEventListener("load", function(e) { recap.onLoad(e); }, false);
