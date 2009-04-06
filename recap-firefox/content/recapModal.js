
function addModal(num) {
    $('#recapdialog' + num).jqm();
    $('#recapdialog' + num).jqmShow();
}

var pdfHeadersCheckbox;
pdfHeadersCheckbox = document.getElementsByName("pdf_header");
if (pdfHeadersCheckbox.length > 0) {	
	pdfHeadersCheckbox[0].checked=true;
}

