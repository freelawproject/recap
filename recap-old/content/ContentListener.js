
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

	if (court && document) {
	    this.docCheckAndModify(court, document);
	}
    },

    // Check our server for cached copies of documents linked on the page,
    //   and modify the page with links to documents on our server
    docCheckAndModify: function(court, document) {

	// Construct the JSON object parameter
	var jsonout = { "court": court, 
			"urls": [] };
	var links = document.getElementsByTagName("a");
	// Save pointers to the HTML elements for each "a" tag, keyed by URL
	var elements = {};

	for (var i = 0; i < links.length; i++) {
	    var link = links[i];
	    var docURL = this.getDocURL(link.href);
	    
	    if (docURL) {
		jsonout.urls.push(docURL);
		elements[docURL] = link;
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

	req.onreadystatechange = function() {
	    
	    if (req.readyState == 4) {
		var jsonin = nativeJSON.decode(req.responseText);

		for (var docURL in jsonin) {
		    var filename = jsonin[docURL]["filename"];
		    var timestamp = jsonin[docURL]["timestamp"];
		    var element = elements[docURL];
		    
		    log("  File found: " + filename);
		    // Ensure that the element isn't already modified
		    if (element.previousSibling) {
			previousElement = element.previousSibling;
			previousClass = previousElement.className;

			if (previousClass == "recap") 
			    continue;
		    }

		    // Insert our link to the left of the PACER link
		    var newLink = document.createElement("a");
		    newLink.href = "http://monocle.princeton.edu/recap_docs/" 
			+ filename; 
		    newLink.setAttribute("style", "margin: 0 10px 0 0;");
		    newLink.setAttribute("class", "recap");
		    var newText = document.createTextNode("[RECAP " + 
							  timestamp + "]");
		    newLink.appendChild(newText);
		    element.parentNode.insertBefore(newLink, element);
		}
	    }
	};
	
	req.send(params);
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

    // Check if the page worth modifying with our links
    isModifiable: function(path) {
	var PACERpages = ["qrySummary.pl", "DktRpt.pl", "HistDocQry.pl"];
	
	var plName = null;
	try {
	    plName = path.match(/(\w*)\.pl/i)[0];
	} catch(e) {
	    return false;
	}

	return (PACERpages.indexOf(plName) >= 0) ? true : false;
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
    }

}