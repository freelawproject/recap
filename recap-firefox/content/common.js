
var ICON_LOGGED_IN = "chrome://recap/skin/recap-icon.png";
var ICON_LOGGED_IN_32 = "chrome://recap/skin/recap-icon-32.png";
var ICON_LOGGED_OUT = "chrome://recap/skin/recap-icon-grey.png";
var ICON_LOGGED_OUT_32 = "chrome://recap/skin/recap-icon-grey-32.png";

// List of all PACER/ECF domains
var PACER_DOMAINS = ["ecf.almd.uscourts.gov", "ecf.alnd.uscourts.gov", "ecf.alsd.uscourts.gov", "ecf.akd.uscourts.gov", "ecf.azd.uscourts.gov", "ecf.ared.uscourts.gov", "ecf.arwd.uscourts.gov", "ecf.cacd.uscourts.gov", "ecf.caed.uscourts.gov", "ecf.cand.uscourts.gov", "ecf.casd.uscourts.gov", "ecf.cod.uscourts.gov", "ecf.ctd.uscourts.gov", "ecf.ded.uscourts.gov", "ecf.dcd.uscourts.gov", "ecf.flmd.uscourts.gov", "ecf.flnd.uscourts.gov", "ecf.flsd.uscourts.gov", "ecf.gamd.uscourts.gov", "ecf.gand.uscourts.gov", "ecf.gasd.uscourts.gov", "ecf.gud.uscourts.gov", "ecf.hid.uscourts.gov", "ecf.idd.uscourts.gov", "ecf.ilcd.uscourts.gov", "ecf.ilnd.uscourts.gov", "ecf.ilsd.uscourts.gov", "ecf.innd.uscourts.gov", "ecf.insd.uscourts.gov", "ecf.iand.uscourts.gov", "ecf.iasd.uscourts.gov", "ecf.ksd.uscourts.gov", "ecf.kyed.uscourts.gov", "ecf.kywd.uscourts.gov", "ecf.laed.uscourts.gov", "ecf.lamd.uscourts.gov", "ecf.lawd.uscourts.gov", "ecf.med.uscourts.gov", "ecf.mdd.uscourts.gov", "ecf.mad.uscourts.gov", "ecf.mied.uscourts.gov", "ecf.miwd.uscourts.gov", "ecf.mnd.uscourts.gov", "ecf.msnd.uscourts.gov", "ecf.mssd.uscourts.gov", "ecf.moed.uscourts.gov", "ecf.mowd.uscourts.gov", "ecf.mtd.uscourts.gov", "ecf.ned.uscourts.gov", "ecf.nvd.uscourts.gov", "ecf.nhd.uscourts.gov", "ecf.njd.uscourts.gov", "ecf.nmd.uscourts.gov", "ecf.nyed.uscourts.gov", "ecf.nynd.uscourts.gov", "ecf.nysd.uscourts.gov", "ecf.nywd.uscourts.gov", "ecf.nced.uscourts.gov", "ecf.ncmd.uscourts.gov", "ecf.ncwd.uscourts.gov", "ecf.ndd.uscourts.gov", "ecf.nmid.uscourts.gov", "ecf.ohnd.uscourts.gov", "ecf.ohsd.uscourts.gov", "ecf.oked.uscourts.gov", "ecf.oknd.uscourts.gov", "ecf.okwd.uscourts.gov", "ecf.ord.uscourts.gov", "ecf.paed.uscourts.gov", "ecf.pamd.uscourts.gov", "ecf.pawd.uscourts.gov", "ecf.prd.uscourts.gov", "ecf.rid.uscourts.gov", "ecf.scd.uscourts.gov", "ecf.sdd.uscourts.gov", "ecf.tned.uscourts.gov", "ecf.tnmd.uscourts.gov", "ecf.tnwd.uscourts.gov", "ecf.txed.uscourts.gov", "ecf.txnd.uscourts.gov", "ecf.txsd.uscourts.gov", "ecf.txwd.uscourts.gov", "ecf.cofc.uscourts.gov", "ecf.utd.uscourts.gov", "ecf.vtd.uscourts.gov", "ecf.vid.uscourts.gov", "ecf.vaed.uscourts.gov", "ecf.vawd.uscourts.gov", "ecf.waed.uscourts.gov", "ecf.wawd.uscourts.gov", "ecf.wvnd.uscourts.gov", "ecf.wvsd.uscourts.gov", "ecf.wied.uscourts.gov", "ecf.wiwd.uscourts.gov", "pacer.wiwd.uscourts.gov", "ecf.wyd.uscourts.gov", "monocle.princeton.edu"];

function isPDF(mimetype) {
    return (mimetype == "application/pdf") ? true: false;
}

function isHTML(mimetype) {
    return (mimetype.indexOf("text/html") >= 0) ? true: false;
}

// Returns true if path matches "/doc1/<docnum>"
function isDocPath(path) {

    try {
	var docMatch = path.match(/^\/doc1\/(\d+)$/i);
	return docMatch ? true : false;
    } catch(e) {
	return false;
    }	
}

// Checks whether hostname is a PACER domain
function isPACERHost(hostname) {
    return (PACER_DOMAINS.indexOf(hostname) >= 0) ? true : false;
}

// Get court name from hostname
function getCourtFromHost(hostname) {
    var court = null;
    try {
	court = hostname.match(/(\w*)\.uscourts.gov/i)[1];
    } catch(e) {}

    return court;
}

// Checks whether we have a PACER cookie
function havePACERCookie(URI, request) {
    var cservice = CCGS("@mozilla.org/cookieService;1",
			"nsICookieService");
    
    var cookieString = cservice.getCookieString(URI, request);
    
    if (!cookieString || !cookieString.match("PacerUser")) {
	//log("No PACER cookie found.");
	return false;
    } else if (cookieString.match("KEY")) {
	// We should never get here, but let's be paranoid
	log("CM/ECF cookie found.");
	return false;
    } else {
	//log("PACER cookie found.");
	return true;
    }
}

// The XUL element in the status bar for Recap
var statusXUL = null;