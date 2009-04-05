
function addModal(num) {
    $('#recapdialog' + num).jqm();
    $('#recapdialog' + num).jqmShow();
}

var pdfHeadersCheckbox;
if (pdfHeadersCheckbox = document.getElementsByName("pdf_header")) {
	
	pdfHeadersCheckbox[0].checked=true;
}

