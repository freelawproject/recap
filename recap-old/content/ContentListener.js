/* 
 *  This file is part of the RECAP Firefox Extension.
 *
 *  Copyright 2009 Harlan Yu, Timothy B. Lee, Stephen Schultze.
 *  Website: http://www.recapthelaw.org
 *  E-mail: info@recapthelaw.org
 *
 *  The RECAP Firefox Extension is free software: you can redistribute it 
 *  and/or modify it under the terms of the GNU General Public License as
 *  published by the Free Software Foundation, either version 3 of the 
 *  License, or (at your option) any later version.
 *
 *  The RECAP Firefox Extension is distributed in the hope that it will be
 *  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with the RECAP Firefox Extension.  If not, see 
 *  <http://www.gnu.org/licenses/>.
 *
 */

function ContentListener() {
    this._register();
    this.active = false;
    this.winMediator = CCGS("@mozilla.org/appshell/window-mediator;1",
			    "nsIWindowMediator");
    
    this.ioService = CCGS("@mozilla.org/network/io-service;1",
			  "nsIIOService");
    this.scriptableStream = CCGS("@mozilla.org/scriptableinputstream;1",
				 "nsIScriptableInputStream");
    this.images = this.initImages();
}

ContentListener.prototype = {

    initImages: function() {

	var retdict = {};
	
	var srcs = new Array("recap-icon.png", 
			     "close-x-button.png", 
			     "recap-logo.png");
	
	for (var i in srcs) {
	    var src = srcs[i];
	    var embeddedImageSrc = "data:image/png;base64,";
	    embeddedImageSrc += this.localFileToBase64(RECAP_SKIN_PATH + src);
	    retdict[src] = embeddedImageSrc;

	}
	
	return retdict;
    },

    // Implementing nsIWebProgressListener
    onStateChange: function(webProgress, request, stateFlags, status) {
	
	const WPL = Ci.nsIWebProgressListener;

	// Ensure that the document is done loading
	var isNetwork = stateFlags & WPL.STATE_IS_NETWORK;
	var isStop = stateFlags & WPL.STATE_STOP;
	var doneLoading = isNetwork && isStop;
	if (!doneLoading) {
	    return;
	}

	var navigation = webProgress.QueryInterface(Ci.nsIWebNavigation);

	var URIhost = navigation.currentURI.asciiHost;
	var URIpath = navigation.currentURI.path;
	try{
	var refpath = navigation.referringURI.path;
	}catch(e){
		//referringURI may not exist in all cases
		refpath = "";
	}
	
	var prefs = CCGS("@mozilla.org/preferences-service;1",
				"nsIPrefService").getBranch("recap.");

	var temp_disabled = prefs.getBoolPref("temp_disable");

	if ((isPACERHost(URIhost)|| isUnsupportedPACERHost(URIhost))
	    && havePACERCookie() 
	    && !this.active) {
	    // Just logged into PACER
            if(temp_disabled == true){
	    		showAlert(ICON_DISABLED_32, 
	       			"RECAP deactivated.", "Your settings forced RECAP to stay deactivated.");
	    }
	    else if (isUnsupportedPACERHost(URIhost)){
	    		showAlert(ICON_DISABLED_32, 
	       			"RECAP not supported.", "RECAP does not work on Appellate Courts");
		    
	    }
	    else{
	    		showAlert(ICON_LOGGED_IN_32, 
	       		"RECAP activated.", "You are logged into PACER.");
	    }
	    this.active = true;

	} else if ((isPACERHost(URIhost)|| isUnsupportedPACERHost(URIhost))
		   && !havePACERCookie()
		   && this.active) {
	    // Just logged out of PACER
	    if(temp_disabled == false) { 
	         // Show alert only if we are not disabled
		 showAlert(ICON_LOGGED_OUT_32, 
	       		"RECAP deactivated.", "You are logged out of PACER. and that's d");
	    }

	    this.active = false;    
	} 

	this.updateAllWindowIcons();

	// Ensure that the page warrants modification
	if (temp_disabled ||
	    !isPACERHost(URIhost) ||
	    !havePACERCookie() ||
	    !this.isModifiable(URIpath)) {

	    return;
	}

	var court = getCourtFromHost(URIhost);	
	var document = navigation.document;
	//var showSubdocs = isDocPath(URIpath);
	var showSubdocs = true;

	var casenum = null;
	var preDocketPage = this.isPreDocketReportPage(URIpath)
        if (preDocketPage){
	    //Get the casenum from the current page URI
	    try {
		casenum = URIpath.match(/\?(\d+)$/i)[1];
	    } catch (e) {
		    log('could not find casenum! Query case failed')
	    
	    }
	}

	if (!preDocketPage && court && document) {
	    this.docCheckAndModify(document, court, showSubdocs);
	}
	else if (preDocketPage && casenum && court && document){
	    this.caseCheckAndModify(document, court, casenum);
	}

    },

    //Check our server to see if a docket page exists,
    //   and modify the page with link to docket page
    caseCheckAndModify: function(document, court, casenum){
        // TODO - DK: Refactor this out? The only thing we need to do is check pdf headers, i think
	// Don't add js libs they have already been loaded
	var loaded = document.getElementsByClassName("recapjs");
	if (!loaded.length) {
		// Write the necessary js libraries into the document
		this.loadjs(document);
	}
	if (casenum == undefined){
		return
	}
        //Casenum is defined, so this is a pre-docket show page
        //We will ask recap for a link to the docket page, if it exists
	var jsonout = { court: court, 
			showSubdocs: true,
		         getDocketURL: true,
			 urls: [],
	    	        casenum: casenum};

	var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	
	// Serialize the JSON object to a string
	var jsonouts = nativeJSON.encode(jsonout);

        // Send the AJAX POST request
	var req = CCIN("@mozilla.org/xmlextras/xmlhttprequest;1",
		       "nsIXMLHttpRequest");
	
	var params = "json=" + jsonouts;
	
	req.open("POST", QUERY_CASES_URL, true);

	var that = this;
	req.onreadystatechange = function() {
	    if (req.readyState == 4 && req.status == 200) {
		that.handleCaseResponse(req, document);
	    }
	};

	req.send(params);

			
    },


    // Check our server for cached copies of documents linked on the page,
    //   and modify the page with links to documents on our server
    docCheckAndModify: function(document, court, showSubdocs, casenum) {

	// Don't add js libs they have already been loaded
	var loaded = document.getElementsByClassName("recapjs");
	if (!loaded.length) {
		// Write the necessary js libraries into the document
		this.loadjs(document);
	}
	
	// Construct the JSON object parameter
	var jsonout = { showSubdocs: showSubdocs,
			court: court, 
			urls: [] };

	try {
	    var body = document.getElementsByTagName("body")[0];
	} catch(e) {
	    return;
	}
	
	var links = body.getElementsByTagName("a");
	// Save pointers to the HTML elements for each "a" tag, keyed by URL
	var elements = {};
	
	for (var i = 0; i < links.length; i++) {
	    var link = links[i];
	    
	    var docURL = this.getDocURL(link.href);
	    
	    if (docURL) {
		jsonout.urls.push(escape(docURL));
		try {
		    elements[docURL].push(link);
		} catch(e) {
		    elements[docURL] = [link];
		}
		
	    }
	}
	
	// if no linked docs, don't bother sending docCheck
	if (jsonout.urls.length == 0) {
	    return;
	}

	var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	
	// Serialize the JSON object to a string
	var jsonouts = nativeJSON.encode(jsonout);

        // Send the AJAX POST request
	var req = CCIN("@mozilla.org/xmlextras/xmlhttprequest;1",
		       "nsIXMLHttpRequest");
	
	var params = "json=" + jsonouts;
	
	req.open("POST", QUERY_URL, true);

	var that = this;
	req.onreadystatechange = function() {
	    if (req.readyState == 4 && req.status == 200) {
		that.handleResponse(req, document, elements);
	    }
	};

	req.send(params);

    },

    // Handle the AJAX response
    handleResponse: function(req, document, elements) { 
	
	var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	var jsonin = nativeJSON.decode(req.responseText);
	
	// a unique number for each dialog div
	var count = 0;
	
	for (var docURL in jsonin) {
	    count++;
	    
	    var filename = jsonin[docURL]["filename"];
	    var timestamp = jsonin[docURL]["timestamp"];
	    var urlElements = elements[docURL];

	    // If a document has subdocuments, we will create a slightly different modal box
            try{
	       var subDocuments = jsonin[docURL]["subDocuments"];
	    }
	    catch(e){
		    var subDocuments = false;
	    }
	    

	    if(!subDocuments){
	      // Create a dialogDiv for each RECAP document on the server
	      this.makeDialogDiv(document, filename,  timestamp, count);
	    }
	    else{
	      this.makeDialogDiv(document, filename,  timestamp, count, subDocuments);
	    }
	    
	    
	    //log("  File found: " + filename + " " + docURL);
	    
	    for (var i = 0; i < urlElements.length; i++) {
		
		element = urlElements[i];
		
		// Ensure that the element isn't already modified
		if (element.nextSibling) {
		    nextElement = element.nextSibling;
		    nextClass = nextElement.className;		
		    if (nextClass == "recapIcon") 
			continue;
		}
		
		// Insert our link to the right of the PACER link
		var iconLink = document.createElement("a");
		iconLink.setAttribute("class", "recapIcon");
		iconLink.setAttribute("href", filename);
		iconLink.setAttribute("onClick", "return false;");
		
		var iconImage = this.addImage(document, iconLink,
					      "recap-icon.png");
		iconImage.setAttribute("class", "recapIconImage");
		iconImage.setAttribute("alt", "[RECAP]");
		iconImage.setAttribute("onClick", 
				       "addModal(" + count + ")");
		iconImage.setAttribute("title",
				       "Available for free from RECAP.");
		
		element.parentNode.insertBefore(iconLink, 
						element.nextSibling);
	    }
	}
    },    

    handleCaseResponse: function(req, document) {
	
	var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	var jsonin = nativeJSON.decode(req.responseText);

	var docket_url = null;
	try{
	     docket_url = jsonin['docket_url'];
	}
	catch(e){ 
		return;
	}
	try{
	    timestamp = jsonin['timestamp'] 
	}
	catch(e){ 
		// continue on failure, timestamp is not crucial
	}

	if(docket_url!=null){
		
		var iconLink = document.createElement("a");
		iconLink.setAttribute("class", "recapIcon");
		iconLink.setAttribute("href", docket_url);
		iconLink.setAttribute("onClick", "return false;");

		var iconImage = this.addImage(document, iconLink,
					      "recap-icon.png");
		iconImage.setAttribute("class", "recapIconImage");
		iconImage.setAttribute("alt", "[RECAP]");
		iconImage.setAttribute("onClick", 
	        			       "addModal(" + 1 + ");");
		iconImage.setAttribute("title",
				       "Docket available for free via RECAP.");

		
	        this.makeCaseDialogDiv(document, docket_url,  timestamp);

		var textLink= document.createElement("a");
		textLink.setAttribute("href", docket_url);
		textLink.setAttribute("onClick", 
	        			       "addModal(" + 1 + "); return false;");
		textLink.innerHTML = " Docket available for free via RECAP (unofficial and potentially incomplete, last updated: " + timestamp+ " )";

		var reset_button = document.getElementsByName('reset')[0];
		reset_button.parentNode.parentNode.appendChild(iconLink);
		reset_button.parentNode.parentNode.appendChild(textLink);

		return;

	}

    
    },
    
    isPreDocketReportPage: function(current_path){
	var current_page_name = null;
	try {
	    current_page_name = current_path.match(/(\w+)\.pl/i)[0];
	} catch(e) {
		return false;
	}
        				   
	var modifiablePages = ["DktRpt.pl", "HistDocQry.pl"];
	
	var args = null;
	try {
	    args = current_path.match(/\?\d*$/i)[0];
	} catch(e) {}
	
	just_digits = (args && args.length > 0) ? true : false;


	// This may screw up when back/forward? 
	if (modifiablePages.indexOf(current_page_name) >= 0 && 
			args && just_digits ) {
		return true;
	}

	return false;
    },
    
    makeBasicDialogDiv: function(document, count){
	var outerdiv = document.createElement("div");
	outerdiv.setAttribute("id", "recapdialog" + count);
	outerdiv.setAttribute("class", "jqmWindow recapOuterDiv");

	// add X to close the dialog
	var closeLink = document.createElement("a");
	closeLink.setAttribute("href", "#");
	closeLink.setAttribute("class", "jqmClose");
	var closeIcon = this.addImage(document, closeLink, 
				      "close-x-button.png");
	closeIcon.setAttribute("alt", "[Close]");
	closeIcon.setAttribute("class", "recapCloseButton");
	closeLink.appendChild(closeIcon);
	outerdiv.appendChild(closeLink);

	return outerdiv;
    },
   
    // Make a dialog div and append it to the bottom of the document body
    makeDialogDiv: function(document, filename, timestamp, count, subDocuments) {

	if(subDocuments == undefined){
		subDocuments = false;
	}
        var outerdiv = this.makeBasicDialogDiv(document, count)
	
	var innerdiv = document.createElement("div");
	innerdiv.setAttribute("class", "recapInnerDiv");

	this.addP(document, innerdiv);
	this.addImage(document, innerdiv, "recap-logo.png");
	this.addBr(document, innerdiv);
	this.addText(document, innerdiv, 
		     "This document is available for free!");
	this.addP(document, innerdiv);
	this.addTextLink(document, innerdiv, "RECAP", 
		     "http://www.recapthelaw.org", "_blank");
	this.addText(document, innerdiv, 
		     " cached this document on " + timestamp + ".");
	this.addP(document, innerdiv);
	this.addBr(document, innerdiv);
	var a = this.addTextLink(document, innerdiv, "Download", filename, null);
	a.setAttribute("class", "recapDownloadButton");
	
	//If there are subDocuments, we want to display them here
	if (subDocuments){
	   var subDocDiv= document.createElement("div");
	   subDocDiv.setAttribute("class", "recapInnerSubDocDiv");

	   this.addP(document, innerdiv);
	   this.addText(document, innerdiv, 
			" RECAP also has some sub documents associated with this document!");

	   this.addBr(document, innerdiv);
	   for(var subDocNum in subDocuments){
		   sub_filename = subDocuments[subDocNum]["filename"]
		   sub_timestamp= subDocuments[subDocNum]["timestamp"]
	           this.addText(document, subDocDiv, 
		          "RECAP cached subdocument #" + subDocNum + " on " + sub_timestamp + " " )
	           var a = this.addTextLink(document, subDocDiv, "Download", sub_filename, null);	  
		   a.setAttribute("class", "recapDownloadButton");
	           this.addBr(document, subDocDiv);
	   }
	}

	this.addP(document, innerdiv);
	if (subDocuments){
	   innerdiv.appendChild(subDocDiv);
	}

	this.addDisclaimerDiv(document, innerdiv);
	outerdiv.appendChild(innerdiv);
	document.documentElement.appendChild(outerdiv);	
    },
    makeCaseDialogDiv: function(document, docket_url, timestamp){

        var outerdiv = this.makeBasicDialogDiv(document, 1)

	var innerdiv = document.createElement("div");
	innerdiv.setAttribute("class", "recapInnerDiv");

	this.addP(document, innerdiv);
	this.addImage(document, innerdiv, "recap-logo.png");
	this.addBr(document, innerdiv);
	this.addText(document, innerdiv, 
		     "This Docket is available for free!");
	this.addP(document, innerdiv);
	this.addTextLink(document, innerdiv, "RECAP", 
		     "http://www.recapthelaw.org", "_blank");
	this.addText(document, innerdiv, 
		     " cached this docket on " + timestamp + ".");
	this.addP(document, innerdiv);
	this.addBr(document, innerdiv);
	
	var a = this.addTextLink(document, innerdiv, "Download", docket_url, null);
	a.setAttribute("class", "recapDownloadButton");
	
	this.addP(document, innerdiv);
	this.addBr(document, innerdiv);
	
	this.addDisclaimerDiv(document, innerdiv);
	outerdiv.appendChild(innerdiv);
	document.documentElement.appendChild(outerdiv);	
    },

    addText: function(document, div, text) {
	var textNode = document.createTextNode(text);
	div.appendChild(textNode);
	return textNode;
    },

    addP: function(document, div) {
	var p = document.createElement("p");
	div.appendChild(p);
	return p;
    },

    addBr: function(document, div) {
	var br = document.createElement("br");
	div.appendChild(br);
	return br;
    },

    addTextLink: function(document, div, text, href, target) {
	var a = document.createElement("a");
	a.href = href;
	if (target) {
		a.target = target;
	}
	this.addText(document, a, text);
	div.appendChild(a);
	return a;
    },

    addImage: function(document, div, src) {
	var img = document.createElement("img");
	
	img.setAttribute("src", this.images[src]);
	div.appendChild(img);
	return img;
    },
    addDisclaimerDiv: function(document, div){
	
        var disclaimerDiv = document.createElement("div");
	disclaimerDiv.setAttribute("class","recapDisclaimer");
	this.addText(document, disclaimerDiv, "RECAP is not affiliated with the US Courts. The documents it makes available are voluntarily uploaded by PACER users.  RECAP cannot guarantee the authenticity of documents because the courts themselves have not implemented a document signing and authentication system.");

	div.appendChild(disclaimerDiv);
	return disclaimerDiv;
    },


    // Get the document URL path (e.g. '/doc1/1234567890')
    getDocURL: function(url) {
	var docURL = null;
	try { docURL = url.match(/\/doc1\/(\d*)/i)[0]; } catch (e) {}
	if (docURL) {
		return docURL;
	}
	
	try { docURL = url.match(/\/cgi-bin\/show_doc.*/i)[0]; } catch (e) {}
	if (docURL) {
		return docURL;
	}
	
	return null;
	
    },

    // Returns true if path matches ".../doc1/<docnum>"
    hasDocPath: function(path) {

	try {
	    var docMatch = path.match(/\/doc1\/(\d+)/i);
	    return docMatch ? true : false;
	} catch(e) {
	    return false;
	}	
    },

    // Check if the page worth modifying with our links
    isModifiable: function(path) {
	var modifiablePages = ["DktRpt.pl", "HistDocQry.pl"];

	// Parse out the Perl script name from the path
	var pageName = "";
	try {
	    pageName = path.match(/(\w*)\.pl/i)[0];
	} catch(e) {}

	return (modifiablePages.indexOf(pageName) >= 0 ||
		isDocPath(path)) ? true : false;
    },

    loadjs: function(document) {

	var jstext = this.localFileToString(RECAP_PATH + "jquery-1.3.2.js");
	jstext += this.localFileToString(RECAP_PATH + "jqModal.js");
	jstext += this.localFileToString(RECAP_PATH + "recapModal.js");
	
	var prefs = CCGS("@mozilla.org/preferences-service;1",
				"nsIPrefService").getBranch("recap.");
		
	if (prefs.getBoolPref("auto_check_pdf_headers") == true) {
		jstext += this.localFileToString(RECAP_PATH + "recapPDFHeaders.js");
	}

	var csstext = this.localFileToString(RECAP_SKIN_PATH + "jqModal.css");
	csstext += this.localFileToString(RECAP_SKIN_PATH + "recap.css");

	this.jscssLoadString(document, csstext, "css");
	this.jscssLoadString(document, jstext, "js");

    },

    localFileToBase64: function(localFile) {
	var binaryStream = CCIN("@mozilla.org/binaryinputstream;1",
				"nsIBinaryInputStream");

	var channel = this.ioService.newChannel(localFile, null, null);
	var input = channel.open();
	binaryStream.setInputStream(input);
	var bytes = binaryStream.readBytes(input.available());
	binaryStream.close();
	input.close();

	var base64 = btoa(bytes);

	return base64;
    },

    localFileToString: function(localFile) {

	var channel = this.ioService.newChannel(localFile, null, null);
	var input = channel.open();
	this.scriptableStream.init(input);
	var str = this.scriptableStream.read(input.available());
	this.scriptableStream.close();
	input.close();

	return str;
    },

    jscssLoadString: function(document, str, filetype) {

	if (filetype=="js") { //if filename is a external JavaScript file
	    var element = document.createElement("script");
	    element.setAttribute("type", "text/javascript");
	    element.setAttribute("class", "recapjs");
	    var strNode = document.createTextNode(str);
	    element.appendChild(strNode);
	}
	else if (filetype=="css") { //if filename is an external CSS file
	    var element = document.createElement("style");
	    element.setAttribute("type", "text/css");
	    var strNode = document.createTextNode(str);
	    element.appendChild(strNode);
	}

	if (typeof element != "undefined") {
	    document.getElementsByTagName("head")[0].appendChild(element);
	}
    },

    updateAllWindowIcons: function() {

	var winEnum = this.winMediator.getEnumerator("navigator:browser");

	while (winEnum.hasMoreElements()) {
	    var window = winEnum.getNext();

		try {
			window.updateStatusIcon();
		} catch(e) {
		}

	    
	}
    },
  

    // implementing nsIWebProgressListener, unnecessary functions.
    onProgressChange: function(webProgress, request, 
			       curSelfProgress, maxSelfProgress, 
			       curTotalProgress, maxTotalProgress) {},
    onSecurityChange: function(webProgress, request, state) {},
    onStatusChange: function(webProgress, request, status, message) {},

    QueryInterface: function(iid) {
	if (iid.equals(Ci.nsIWebProgressListener) ||
	    iid.equals(Ci.nsISupportsWeakReference) ||
	    iid.equals(Ci.nsISupports)) {
	    return this;
	}
	
	throw Components.results.NS_NOINTERFACE;
    },

    get _webProgressService() {
	return CCGS("@mozilla.org/docloaderservice;1", "nsIWebProgress");
    },
    
    _register: function() {
	//log("register ContentListener");
	// add listener, only listen for document loading start/stop events
	this._webProgressService
	    .addProgressListener(this, Ci.nsIWebProgress.NOTIFY_STATE_NETWORK);

    },

    unregister: function() {
	//log("unregister ContentListener");
	this._webProgressService.removeProgressListener(this);
    },
    
}

