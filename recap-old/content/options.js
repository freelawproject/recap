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
window.onload = function() {
	toggleRadioButtons(); //initially set
};
