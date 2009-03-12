
function ContentListener() {
    this._register();
}

ContentListener.prototype = {

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

	// Ensure that the page is from a PACER host and warrants modification
	if (!isPACERHost(URIhost) || !this.isModifiable(URIpath)) {
	    return;
	}

	var court = getCourtFromHost(URIhost);	
	var document = navigation.document;	
	var showSubdocs = this.hasDocPath(URIpath);

	if (court && document) {
	    this.docCheckAndModify(document, court, showSubdocs);
	}
    },

    // Check our server for cached copies of documents linked on the page,
    //   and modify the page with links to documents on our server
    docCheckAndModify: function(document, court, showSubdocs) {

	var loaded = document.getElementsByClassName("recaploaded");
	if (loaded.length) {
	    return;
	}
	
	this.loadjs(document);
	
	// Construct the JSON object parameter
	var jsonout = { showSubdocs: showSubdocs,
			court: court, 
			urls: [] };
	
	var links = document.getElementsByTagName("a");
	// Save pointers to the HTML elements for each "a" tag, keyed by URL
	var elements = {};
	
	for (var i = 0; i < links.length; i++) {
	    var link = links[i];
	    var docURL = this.getDocURL(link.href);
	    
	    if (docURL) {
		jsonout.urls.push(docURL);
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
	
	req.open("POST", 
		 "http://monocle.princeton.edu/recap/document/",
		 true);

	var that = this;
	req.onreadystatechange = function() {
	    that.handleResponse(req, document, elements);
	};

	req.send(params);

    },

    handleResponse: function(req, document, elements) { 
	
	if (req.readyState == 4 && req.status == 200) {

	    var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	    var jsonin = nativeJSON.decode(req.responseText);
	    
	    var count = 0;

	    for (var docURL in jsonin) {
		count++;

		var filename = jsonin[docURL]["filename"];
		var timestamp = jsonin[docURL]["timestamp"];
		var urlElements = elements[docURL];

		// create the dialogdiv
		var dialogDiv = document.createElement("div");
		dialogDiv.setAttribute("id", "recapdialog" + count);
		dialogDiv.setAttribute("class", "jqmWindow");
		
		var dialogText = "This is a RECAP document.  " +
		    "We cached this copy on " + timestamp;
		var dialogTextNode = document.createTextNode(dialogText);
		
		var dialogLinkElement = document.createElement("a");
		dialogLinkElement.href = filename;
		var dialogLinkText = document.createTextNode("[Download]");
		dialogLinkElement.appendChild(dialogLinkText);
		
		dialogDiv.appendChild(dialogTextNode);
		dialogDiv.appendChild(dialogLinkElement);
		document.documentElement.appendChild(dialogDiv);
		
		log("  File found: " + filename + " " + docURL);
		// Ensure that the element isn't already modified
		
		for (var i = 0; i < urlElements.length; i++) {
		    
		    element = urlElements[i];
		    
		    if (element.previousSibling) {
			previousElement = element.previousSibling;
			previousClass = previousElement.className;
			
			if (previousClass == "recaptrigger") 
			    continue;
		    }
		    
		    // Insert our link to the left of the PACER link
		    var newLink = document.createElement("a");
		    newLink.href = "#";
		    newLink.setAttribute("style", "margin: 0 10px 0 0;");
		    newLink.setAttribute("class", "recaptrigger");
		    newLink.setAttribute("onClick", "addModal(" + count + ");");
		    var newText = document.createTextNode("[RECAP]");
		    // TK: tooltip with timestamp?
		    newLink.appendChild(newText);
		    element.parentNode.insertBefore(newLink, element);
		}
	    }
	}
    },    
    

    // Get the document URL path (e.g. '/doc1/1234567890')
    getDocURL: function(url) {
	var docURL = null;
	try {
	    docURL = url.match(/\/doc1\/(\d*)/i)[0];
	} catch(e) {
	    return null;
	}
	
	return docURL;
    },

    // Returns true if path matches ".../doc1/<docnum>"
    hasDocPath: function(path) {

	try {
	    var docMatch = path.match(/\/doc1\/(\d+)$/i);
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
		this.hasDocPath(path)) ? true : false;
    },

    // implementing nsIWebProgressListener, unnecessary functions.
    onLocationChange: function(webProgress, request, location) {},
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
	return Cc["@mozilla.org/docloaderservice;1"]
	         .getService(Ci.nsIWebProgress);
    },
    
    _register: function() {
	log("register ContentListener");
	// add listener, only listen for document loading start/stop events
	this._webProgressService
	    .addProgressListener(this, Ci.nsIWebProgress.NOTIFY_STATE_NETWORK);
    },

    unregister: function() {
	log("unregister ContentListener");
	this._webProgressService.removeProgressListener(this);
    },
    
    loadjs: function(document) {

	var jstext = this.localFileToString(RECAP_PATH + "jquery-1.3.2.js");
	jstext += this.localFileToString(RECAP_PATH + "jqModal.js");
	jstext += this.localFileToString(RECAP_PATH + "recapModal.js");

	var csstext = this.localFileToString(RECAP_PATH + "jqModal.css");

	this.jscssLoadString(document, csstext, "css");
	this.jscssLoadString(document, jstext, "js");

    },

    localFileToString: function(localFile) {
	var ioService = Cc["@mozilla.org/network/io-service;1"]
                         .getService(Ci.nsIIOService);
	var scriptableStream = Cc["@mozilla.org/scriptableinputstream;1"]
                         .getService(Ci.nsIScriptableInputStream);

	var channel = ioService.newChannel(localFile, null, null);
	var input=channel.open();
	scriptableStream.init(input);
	var str = scriptableStream.read(input.available());
	scriptableStream.close();
	input.close();

	return str;
    },

    jscssLoadString: function(document, str, filetype) {

	if (filetype=="js") { //if filename is a external JavaScript file
	    var element = document.createElement("script");
	    element.setAttribute("type", "text/javascript");
	    element.setAttribute("class", "recaploaded");
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
	    log("jscssLoadString: " + filetype);
	}
    },

}