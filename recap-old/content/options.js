function toggleRadioButtons(){

	var filenames_enabled = window.document.getElementById("pretty_filenames").checked;

	var radiogroup = window.document.getElementById("pretty_filenames_choices");
	var radiobutton1 =window.document.getElementById("pretty_filenames_IAFilename");
	var radiobutton2 =window.document.getElementById("pretty_filenames_FancyFilename");

	if(filenames_enabled == true){
		radiogroup.removeAttribute("disabled");
		radiogroup.disabled = false;
		//radiobutton1.disabled = false;
		//radiobutton2.disabled = false;
	}
	else{
		radiogroup.disabled = true;
		radiogroup.setAttribute("disabled", true);
	//	radiobutton1.disabled = true;
	//	radiobutton2.disabled = true;
	}

}

function checkForGrowlAndNotify(){

	// Returns "WINNT" on Windows Vista, XP, 2000, and NT systems;  
    // "Linux" on GNU/Linux; and "Darwin" on Mac OS X.  
    try {
    	var osString = 
		Components.classes["@mozilla.org/xre/app-info;1"] .getService(Components.interfaces.nsIXULRuntime).OS; 
    } catch (e) {
    }
    
	if (osString == "Darwin") {
		var growlWarnMessage = window.document.getElementById("growlWarn");
		try {		
			var alertsService = 
			Components.classes["@mozilla.org/alerts-service;1"] .getService(Components.interfaces.nsIAlertsService); 
		} catch (e) {
			growlWarnMessage.value = "Alert: Growl must be installed and active: http://growl.info/";			
		}
	}	
}

window.onload = function() {
	toggleRadioButtons(); //initially set
	checkForGrowlAndNotify();	
};

