
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

    // List of all PACER/ECF domains
    PACER_DOMAINS: ["www.supremecourtus.gov", "pacer.uspci.uscourts.gov", "ecf.ca1.uscourts.gov", "pacer.bap1.uscourts.gov", "pacer.ca2.uscourts.gov", "ecf.ca3.uscourts.gov", "ecf.ca4.uscourts.gov", "pacer.ca5.uscourts.gov", "ecf.ca5.uscourts.gov", "ecf.ca6.uscourts.gov", "ecf.ca7.uscourts.gov", "pacer.ca7.uscourts.gov", "ecf.ca8.uscourts.gov", "ecf.ca9.uscourts.gov", "ecf.ca9.uscourts.gov", "ecf.ca10.uscourts.gov", "ecf.ca10.uscourts.gov", "pacer.ca11.uscourts.gov", "ecf.cadc.uscourts.gov", "pacer.cafc.uscourts.gov", "ecf.almd.uscourts.gov", "ecf.alnd.uscourts.gov", "ecf.alsd.uscourts.gov", "ecf.akd.uscourts.gov", "ecf.azd.uscourts.gov", "ecf.ared.uscourts.gov", "ecf.arwd.uscourts.gov", "ecf.cacd.uscourts.gov", "ecf.caed.uscourts.gov", "ecf.cand.uscourts.gov", "ecf.casd.uscourts.gov", "ecf.cod.uscourts.gov", "ecf.ctd.uscourts.gov", "ecf.ded.uscourts.gov", "ecf.dcd.uscourts.gov", "ecf.flmd.uscourts.gov", "ecf.flnd.uscourts.gov", "ecf.flsd.uscourts.gov", "ecf.gamd.uscourts.gov", "ecf.gand.uscourts.gov", "ecf.gasd.uscourts.gov", "ecf.gud.uscourts.gov", "ecf.hid.uscourts.gov", "ecf.idd.uscourts.gov", "ecf.ilcd.uscourts.gov", "ecf.ilnd.uscourts.gov", "ecf.ilsd.uscourts.gov", "ecf.innd.uscourts.gov", "ecf.insd.uscourts.gov", "ecf.iand.uscourts.gov", "ecf.iasd.uscourts.gov", "ecf.ksd.uscourts.gov", "ecf.kyed.uscourts.gov", "ecf.kywd.uscourts.gov", "ecf.laed.uscourts.gov", "ecf.lamd.uscourts.gov", "ecf.lawd.uscourts.gov", "ecf.med.uscourts.gov", "ecf.mdd.uscourts.gov", "ecf.mad.uscourts.gov", "ecf.mied.uscourts.gov", "ecf.miwd.uscourts.gov", "ecf.mnd.uscourts.gov", "ecf.msnd.uscourts.gov", "ecf.mssd.uscourts.gov", "ecf.moed.uscourts.gov", "ecf.mowd.uscourts.gov", "ecf.mtd.uscourts.gov", "ecf.ned.uscourts.gov", "ecf.nvd.uscourts.gov", "ecf.nhd.uscourts.gov", "ecf.njd.uscourts.gov", "ecf.nmd.uscourts.gov", "ecf.nyed.uscourts.gov", "ecf.nynd.uscourts.gov", "ecf.nysd.uscourts.gov", "ecf.nywd.uscourts.gov", "ecf.nced.uscourts.gov", "ecf.ncmd.uscourts.gov", "ecf.ncwd.uscourts.gov", "ecf.ndd.uscourts.gov", "ecf.nmid.uscourts.gov", "ecf.ohnd.uscourts.gov", "ecf.ohsd.uscourts.gov", "ecf.oked.uscourts.gov", "ecf.oknd.uscourts.gov", "ecf.okwd.uscourts.gov", "ecf.ord.uscourts.gov", "ecf.paed.uscourts.gov", "ecf.pamd.uscourts.gov", "ecf.pawd.uscourts.gov", "ecf.prd.uscourts.gov", "ecf.rid.uscourts.gov", "ecf.scd.uscourts.gov", "ecf.sdd.uscourts.gov", "ecf.tned.uscourts.gov", "ecf.tnmd.uscourts.gov", "ecf.tnwd.uscourts.gov", "ecf.txed.uscourts.gov", "ecf.txnd.uscourts.gov", "ecf.txsd.uscourts.gov", "ecf.txwd.uscourts.gov", "ecf.cofc.uscourts.gov", "ecf.utd.uscourts.gov", "ecf.vtd.uscourts.gov", "ecf.vid.uscourts.gov", "ecf.vaed.uscourts.gov", "ecf.vawd.uscourts.gov", "ecf.waed.uscourts.gov", "ecf.wawd.uscourts.gov", "ecf.wvnd.uscourts.gov", "ecf.wvsd.uscourts.gov", "ecf.wied.uscourts.gov", "ecf.wiwd.uscourts.gov", "pacer.wiwd.uscourts.gov", "ecf.wyd.uscourts.gov", "ecf.almb.uscourts.gov", "ecf.alnb.uscourts.gov", "ecf.alsb.uscourts.gov", "ecf.akb.uscourts.gov", "ecf.azb.uscourts.gov", "ecf.areb.uscourts.gov", "ecf.arwb.uscourts.gov", "pacerla.cacb.uscourts.gov", "ecf.cacb.uscourts.gov", "ecf.caeb.uscourts.gov", "ecf.canb.uscourts.gov", "ecf.casb.uscourts.gov", "ecf.cob.uscourts.gov", "ecf.ctb.uscourts.gov", "ecf.deb.uscourts.gov", "ecf.dcb.uscourts.gov", "ecf.flmb.uscourts.gov", "ecf.flnb.uscourts.gov", "ecf.flsb.uscourts.gov", "ecf.gamb.uscourts.gov", "ecf.ganb.uscourts.gov", "ecf.gasb.uscourts.gov", "ecf.gub.uscourts.gov", "ecf.hib.uscourts.gov", "ecf.idb.uscourts.gov", "ecf.ilcb.uscourts.gov", "pacer.ilcb.uscourts.gov", "ecf.ilnb.uscourts.gov", "ecf.ilsb.uscourts.gov", "ecf.innb.uscourts.gov", "ecf.insb.uscourts.gov", "ecf.ianb.uscourts.gov", "ecf.iasb.uscourts.gov", "ecf.ksb.uscourts.gov", "ecf.kyeb.uscourts.gov", "ecf.kywb.uscourts.gov", "ecf.laeb.uscourts.gov", "ecf.lamb.uscourts.gov", "ecf.lawb.uscourts.gov", "ecf.meb.uscourts.gov", "ecf.mdb.uscourts.gov", "ecf.mab.uscourts.gov", "ecf.mieb.uscourts.gov", "ecf.miwb.uscourts.gov", "ecf.mnb.uscourts.gov", "ecf.msnb.uscourts.gov", "ecf.mssb.uscourts.gov", "ecf.moeb.uscourts.gov", "ecf.mowb.uscourts.gov", "ecf.mtb.uscourts.gov", "ecf.neb.uscourts.gov", "ecf.nvb.uscourts.gov", "ecf.nhb.uscourts.gov", "ecf.njb.uscourts.gov", "ecf.nmb.uscourts.gov", "ecf.nyeb.uscourts.gov", "ecf.nynb.uscourts.gov", "ecf.nysb.uscourts.gov", "ecf-closed.nysb.uscourts.gov", "ecf.nywb.uscourts.gov", "ecf.nceb.uscourts.gov", "ecf.ncmb.uscourts.gov", "ecf.ncwb.uscourts.gov", "ecf.ndb.uscourts.gov", "ecf.ohnb.uscourts.gov", "ecf.ohsb.uscourts.gov", "ecf.okeb.uscourts.gov", "ecf.oknb.uscourts.gov", "ecf.okwb.uscourts.gov", "ecf.orb.uscourts.gov", "ecf.paeb.uscourts.gov", "ecf.pamb.uscourts.gov", "ecf.pawb.uscourts.gov", "ecf.prb.uscourts.gov", "ecf.rib.uscourts.gov", "ecf.scb.uscourts.gov", "ecf.sdb.uscourts.gov", "ecf.tneb.uscourts.gov", "ecf.tnmb.uscourts.gov", "ecf.tnwb.uscourts.gov", "pacer.tnwb.uscourts.gov", "ecf.txeb.uscourts.gov", "ecf.txnb.uscourts.gov", "ecf.txsb.uscourts.gov", "ecf.txwb.uscourts.gov", "ecf.utb.uscourts.gov", "ecf.vtb.uscourts.gov", "ecf.vib.uscourts.gov", "ecf.vaeb.uscourts.gov", "ecf.vawb.uscourts.gov", "ecf.waeb.uscourts.gov", "ecf.wawb.uscourts.gov", "ecf.wvnb.uscourts.gov", "ecf.wvsb.uscourts.gov", "ecf.wieb.uscourts.gov", "ecf.wiwb.uscourts.gov", "ecf.wyb.uscourts.gov", "tails.princeton.edu"],

    // Checks whether hostname is a PACER domain
    isPACERHost: function(hostname) {
	return (this.PACER_DOMAINS.indexOf(hostname) >= 0) ? true : false;
    },

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
    setContentDispositionHeader: function(channel, filename) {

	if (filename != null) {

	    var cdVal = "inline; filename=\"" + filename + "\"";	

	    log("Setting Content-Disposition to: " + cdVal);
	    channel.setResponseHeader("Content-Disposition", cdVal, false);
	}

    },
    
    // Gets the file metadata from the referrer URI
    getFilemeta: function(channel) {

	var referrer = channel.referrer;

	try {
	    var refhost = referrer.asciiHost;
	    var refpath = referrer.path;	   
	    log("Referrer: " + refhost + refpath);
	} catch(e) {
	    log("Referrer: " + e);
	    return {court: null, path: null, name: null};
	}

	// get court name from hostname
	var court = refhost.match(/(\w*)\.uscourts.gov/i)[1];

	var pathSplit = refpath.split("/");

	// filename will be the last segment of the path, append ".pdf"
	var filename = pathSplit.pop() + ".pdf";
	
	pathSplit.push("");
	var filepath = pathSplit.join("/");
	
	log("Court: " + court + "; Path: " + filepath + "; Name: " + filename);
	
	return {court: court, path: filepath, name: filename};
	
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
    getMimeType: function(channel) {
        try {
	    return channel.getResponseHeader("Content-Type");
	} catch(e) {
	    return null;
	}
    },

    // Called on every HTTP response
    observe: function(subject, topic, data) {
        if (topic != "http-on-examine-response")
            return;

	var channel = subject.QueryInterface(Ci.nsIHttpChannel);
	var URIscheme = channel.URI.scheme;
	var URIhost = channel.URI.asciiHost;
	var URIpath = channel.URI.path;

	// Ignore everything on non-PACER domains
	if (!this.isPACERHost(URIhost)) {
	    return;
	}

	this.logHeaders(channel);

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

	var mimeType = this.getMimeType(channel);	

	// Upload the content to the server if the file is a PDF
	if (this.isPDF(mimeType)) {

	    var filemeta = this.getFilemeta(channel);
	    filemeta.mimeType = mimeType;

	    // Set Content-Disposition header to be save-friendly
	    this.setContentDispositionHeader(channel, filemeta.name);

	    var dlistener = new DownloadListener(filemeta);
	    subject.QueryInterface(Ci.nsITraceableChannel);
	    dlistener.originalListener = subject.setNewListener(dlistener);

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