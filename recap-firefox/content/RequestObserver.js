
/** RequestObserver:
 *    implements nsIObserver
 *
 *    Receives notifications for all http-on-examine-response events.
 *    Upon notification, if this is a PACER document:
 *      - Modifies the HTTP response headers to be cache-friendly
 *      - If necessary, modifies the default filename to be save-friendly
 *      - If "uploadworthy", uploads the file to a server
 *
 */

function RequestObserver() {
    this._register();
}

RequestObserver.prototype = {


    // Logs interesting HTTP response headers to the Error Console
    logHeaders: function(channel) {
	var headers = ["Age", "Cache-Control", "ETag", "Pragma", 
		       "Vary", "Last-Modified", "Expires", "Date", 
		       "Content-Disposition", "Content-Type"];

	var output = "Headers for " + channel.URI.asciiSpec + "\n  ";
	for (var i = 0; i < headers.length; i++) {
	    var hvalue = "";
	    try {
		hvalue = channel.getResponseHeader(headers[i]);
	    } catch(e) {
		hvalue = "<<none>>";
	    }

	    output += "'" + headers[i] + "': " + "'" + hvalue + "'; ";
	}

	log(output);
    },

    // Removes 'no-cache' from the Pragma response header if it exists
    getPragmaValue: function(channel) {
	try {
	    var hpragma = channel.getResponseHeader("Pragma");
	} catch(e) {
	    return "";
	}
	
	return hpragma.replace(/no-cache/g, "");
    },

    // Sets a better filename in the Content-Disposition header
    setContentDispositionHeader: function(channel, filename, court) {

	if (filename != null && court != null) {

	    var cdVal = "inline; filename=\"" + court + 
	                 "-" + filename + "\"";	

	    log("Setting Content-Disposition to: " + cdVal);
	    channel.setResponseHeader("Content-Disposition", cdVal, false);
	}

    },

    // Gets the PDF metadata from the referrer URI
    getPDFmeta: function(channel, mimetype) {

	var referrer = channel.referrer;

	try {
	    var refhost = referrer.asciiHost;
	    var refpath = referrer.path;	   
	} catch(e) {
	    return {mimetype: mimetype, court: null, 
		    url: null, name: null};
	}

	var court = getCourtFromHost(refhost);
	
	var pathSplit = refpath.split("/");

	// filename will be the last segment of the path, append file suffix
	var filename = pathSplit.pop() + this.fileSuffixFromMime(mimetype);

	return {mimetype: mimetype, court: court, 
		url: refpath, name: filename};
    },

    tryHTMLmeta: function(channel, path, mimetype) {

	if (mimetype.indexOf("text/html") >= 0) {

	    var downloadablePages = ["HistDocQry.pl", "DktRpt.pl"];
	    
	    var referrer = channel.referrer;
	    try {
		var refhost = referrer.asciiHost;
		var refpath = referrer.path;	   
	    } catch(e) {
		return false;
	    }

	    var pageName = this.pathMatch(path);
	    var refPageName = this.pathMatch(refpath);
	    
	    // If this is an interesting HTML document, return metadata
	    if (pageName && refPageName &&
		pageName == refPageName &&
		downloadablePages.indexOf(pageName) >= 0) {

		var casenum = null;
		try {
		    casenum = refpath.match(/\?(\d+)$/i)[1];
		} catch (e) {}

		var name = pageName.replace(".pl", ".html");

		var court = getCourtFromHost(refhost);

		log("HTMLmeta: " + mimetype + " " + casenum + " " + name
		    + " " + court);

		return {mimetype: mimetype, casenum: casenum, 
			name: name, court: court};
	    }
	}
	return false;
    },

    
    fileSuffixFromMime: function(mimetype) {
	if (mimetype == "application/pdf") {
	    return ".pdf";
	} else {
	    return null;
	}
    },

    // Returns a boolean, whether the file is a PDF
    isPDF: function(mimetype) {
	if (mimetype == "application/pdf") {
	    return true;
	} else {
	    return false;
	}
    },

    // Returns the specified Content-type from the HTTP response header
    getMimetype: function(channel) {
        try {
	    return channel.getResponseHeader("Content-Type");
	} catch(e) {
	    return null;
	}
    },

    ignorePage: function(path) {
	var ignorePages = ["login.pl", "iquery.pl", "BillingRpt.pl"];
	
	var pageName = this.pathMatch(path);

	return (pageName && ignorePages.indexOf(pageName) >= 0) ? true : false;
    },

    pathMatch: function(path) {
	var pageName = null;
	try {
	    pageName = path.match(/(\w+)\.pl/i)[0];
	} catch(e) {}

	return pageName;
    },

    // Called on every HTTP response
    observe: function(subject, topic, data) {
        if (topic != "http-on-examine-response")
            return;

	var channel = subject.QueryInterface(Ci.nsIHttpChannel);
	var URIscheme = channel.URI.scheme;
	var URIhost = channel.URI.asciiHost;
	var URIpath = channel.URI.path;

	// Ignore everything on non-PACER domains and some PACER pages
	if (!isPACERHost(URIhost) || this.ignorePage(URIpath)) {
	    //log("Ignored: " + URIhost + " " + URIpath)
	    return;
	}

	//this.logHeaders(channel);

	var pragmaVal = this.getPragmaValue(channel);
	// expiration arbitrarily set to one day
	var oneday = (new Date()).getTime() + 24*60*60*1000;
	var expiresVal = (new Date(oneday)).toUTCString();
	var dateVal = (new Date()).toUTCString();

	// Set HTTP response headers to be cache-friendly
	channel.setResponseHeader("Age", "", false);
	channel.setResponseHeader("Cache-Control", "", false);
	channel.setResponseHeader("ETag", "", false);
	channel.setResponseHeader("Pragma", pragmaVal, false);
	channel.setResponseHeader("Vary", "", false);
	channel.setResponseHeader("Last-Modified", "", false);
	channel.setResponseHeader("Expires", expiresVal, false);
	channel.setResponseHeader("Date", dateVal, false);

	var mimetype = this.getMimetype(channel);	

	// Upload content to the server if the file is a PDF
	if (this.isPDF(mimetype)) {

	    var PDFmeta = this.getPDFmeta(channel, mimetype);

	    // Set Content-Disposition header to be save-friendly
	    this.setContentDispositionHeader(channel, 
					     PDFmeta.name, 
					     PDFmeta.court);

	    var dlistener = new DownloadListener(PDFmeta);
	    subject.QueryInterface(Ci.nsITraceableChannel);
	    dlistener.originalListener = subject.setNewListener(dlistener);

	} else {
	    // Upload content to the server if the file is interesting HTML
	    
	    var HTMLmeta = this.tryHTMLmeta(channel, URIpath, mimetype);

	    if (HTMLmeta) {	    	    
		var dlistener = new DownloadListener(HTMLmeta);
		subject.QueryInterface(Ci.nsITraceableChannel);
		dlistener.originalListener = subject.setNewListener(dlistener);
	    }
	}
    },

    get _observerService() {
        return Cc["@mozilla.org/observer-service;1"]
	         .getService(Ci.nsIObserverService);
    },
    
    _register: function() {
        log("register RequestObserver");
        this._observerService.addObserver(this, 
					  "http-on-examine-response", 
					  false);
    },
    
    unregister: function() {
        log("unregister RequestObserver");
        this._observerService.removeObserver(this, 
					     "http-on-examine-response");
    }
};