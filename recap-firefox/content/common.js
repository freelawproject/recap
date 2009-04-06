log("loaded common.js");

var ICON_LOGGED_IN = "chrome://recap/skin/recap-icon.png";
var ICON_LOGGED_IN_32 = "chrome://recap/skin/recap-icon-32.png";
var ICON_LOGGED_OUT = "chrome://recap/skin/recap-icon-grey.png";
var ICON_LOGGED_OUT_32 = "chrome://recap/skin/recap-icon-grey-32.png";

//var SERVER_URL = "http://recapextension.appspot.com/"
//var SERVER_URL = "http://localhost:9999/"
var SERVER_URL = "http://monocle.princeton.edu/recap/";

// List of all PACER/ECF domains
var PACER_DOMAINS = ["ecf.almd.uscourts.gov", "ecf.alnd.uscourts.gov", "ecf.alsd.uscourts.gov", "ecf.akd.uscourts.gov", "ecf.azd.uscourts.gov", "ecf.ared.uscourts.gov", "ecf.arwd.uscourts.gov", "ecf.cacd.uscourts.gov", "ecf.caed.uscourts.gov", "ecf.cand.uscourts.gov", "ecf.casd.uscourts.gov", "ecf.cod.uscourts.gov", "ecf.ctd.uscourts.gov", "ecf.ded.uscourts.gov", "ecf.dcd.uscourts.gov", "ecf.flmd.uscourts.gov", "ecf.flnd.uscourts.gov", "ecf.flsd.uscourts.gov", "ecf.gamd.uscourts.gov", "ecf.gand.uscourts.gov", "ecf.gasd.uscourts.gov", "ecf.gud.uscourts.gov", "ecf.hid.uscourts.gov", "ecf.idd.uscourts.gov", "ecf.ilcd.uscourts.gov", "ecf.ilnd.uscourts.gov", "ecf.ilsd.uscourts.gov", "ecf.innd.uscourts.gov", "ecf.insd.uscourts.gov", "ecf.iand.uscourts.gov", "ecf.iasd.uscourts.gov", "ecf.ksd.uscourts.gov", "ecf.kyed.uscourts.gov", "ecf.kywd.uscourts.gov", "ecf.laed.uscourts.gov", "ecf.lamd.uscourts.gov", "ecf.lawd.uscourts.gov", "ecf.med.uscourts.gov", "ecf.mdd.uscourts.gov", "ecf.mad.uscourts.gov", "ecf.mied.uscourts.gov", "ecf.miwd.uscourts.gov", "ecf.mnd.uscourts.gov", "ecf.msnd.uscourts.gov", "ecf.mssd.uscourts.gov", "ecf.moed.uscourts.gov", "ecf.mowd.uscourts.gov", "ecf.mtd.uscourts.gov", "ecf.ned.uscourts.gov", "ecf.nvd.uscourts.gov", "ecf.nhd.uscourts.gov", "ecf.njd.uscourts.gov", "ecf.nmd.uscourts.gov", "ecf.nyed.uscourts.gov", "ecf.nynd.uscourts.gov", "ecf.nysd.uscourts.gov", "ecf.nywd.uscourts.gov", "ecf.nced.uscourts.gov", "ecf.ncmd.uscourts.gov", "ecf.ncwd.uscourts.gov", "ecf.ndd.uscourts.gov", "ecf.nmid.uscourts.gov", "ecf.ohnd.uscourts.gov", "ecf.ohsd.uscourts.gov", "ecf.oked.uscourts.gov", "ecf.oknd.uscourts.gov", "ecf.okwd.uscourts.gov", "ecf.ord.uscourts.gov", "ecf.paed.uscourts.gov", "ecf.pamd.uscourts.gov", "ecf.pawd.uscourts.gov", "ecf.prd.uscourts.gov", "ecf.rid.uscourts.gov", "ecf.scd.uscourts.gov", "ecf.sdd.uscourts.gov", "ecf.tned.uscourts.gov", "ecf.tnmd.uscourts.gov", "ecf.tnwd.uscourts.gov", "ecf.txed.uscourts.gov", "ecf.txnd.uscourts.gov", "ecf.txsd.uscourts.gov", "ecf.txwd.uscourts.gov", "ecf.cofc.uscourts.gov", "ecf.utd.uscourts.gov", "ecf.vtd.uscourts.gov", "ecf.vid.uscourts.gov", "ecf.vaed.uscourts.gov", "ecf.vawd.uscourts.gov", "ecf.waed.uscourts.gov", "ecf.wawd.uscourts.gov", "ecf.wvnd.uscourts.gov", "ecf.wvsd.uscourts.gov", "ecf.wied.uscourts.gov", "ecf.wiwd.uscourts.gov", "pacer.wiwd.uscourts.gov", "ecf.wyd.uscourts.gov"];

// PACER court id to West-style court cite
var PACER_TO_WEST_COURT = {"akd":"D.Alaska", "almd":"M.D.Ala.", "alnd":"N.D.Ala.", "alsd":"S.D.Ala.", "ared":"E.D.Ark.", "arwd":"W.D.Ark.", "azd":"D.Ariz.", "cacd":"C.D.Cal.", "caed":"E.D.Cal.", "cand":"N.D.Cal.", "casd":"S.D.Cal.", "cod":"D.Colo.", "ctd":"D.Conn.", "dcd":"D.D.C.", "ded":"D.Del.", "flmd":"M.D.Fla.", "flnd":"N.D.Fla.", "flsd":"S.D.Fla.", "gamd":"M.D.Ga.", "gand":"N.D.Ga.", "gasd":"S.D.Ga.", "gud":"D.Guam", "hid":"D.Hawaii", "iand":"N.D.Iowa", "iasd":"S.D.Iowa", "idd":"D.Idaho", "ilcd":"C.D.Ill.", "ilnd":"N.D.Ill.", "ilsd":"S.D.Ill.", "innd":"N.D.Ind.", "insd":"S.D.Ind.", "ksd":"D.Kan.", "kyed":"E.D.Ky.", "kywd":"W.D.Ky.", "laed":"W.D.La.", "lamd":"M.D.La.", "lawd":"W.D.La.", "mad":"D.Mass.", "mdd":"D.Md.", "med":"D.Me.", "mied":"E.D.Mich.", "miwd":"W.D.Mich.", "mnd":"D.Minn.", "moed":"W.D.Mo.", "mowd":"W.D.Mo.", "msnd":"N.D.Miss", "mssd":"S.D.Miss.", "mtd":"D.Mont.", "nced":"E.D.N.C.", "ncmd":"M.D.N.C.", "ncwd":"W.D.N.C.", "ndd":"D.N.D.", "ned":"D.Neb.", "nhd":"D.N.H.", "njd":"D.N.J.", "nmd":"D.N.M.", "nmid":"N.MarianaIslands", "nvd":"D.Nev.", "nyed":"E.D.N.Y.", "nynd":"N.D.N.Y.", "nysd":"S.D.N.Y.", "nywd":"W.D.N.Y.", "ohnd":"N.D.Ohio", "ohsd":"S.D.Ohio", "oked":"E.D.Okla.", "oknd":"N.D.Okla.", "okwd":"W.D.Okla.", "ord":"D.Or.", "paed":"E.D.Pa.", "pamd":"M.D.Pa.", "pawd":"W.D.Pa.", "prd":"D.P.R.", "rid":"D.R.I.", "scd":"D.S.C.", "sdd":"D.S.D.", "tned":"E.D.Tenn.", "tnmd":"M.D.Tenn.", "tnwd":"W.D.Tenn.", "txed":"E.D.Tex.", "txnd":"N.D.Tex.", "txsd":"S.D.Tex.", "txwd":"W.D.Tex.", "utd":"D.Utah", "vaed":"E.D.Va.", "vawd":"W.D.Va.", "vid":"D.VIrginIslands", "vtd":"D.Vt.", "waed":"E.D.Wash.", "wawd":"W.D.Wash.", "wied":"E.D.Wis.", "wiwd":"W.D.Wis", "wvnd":"N.D.W.Va.", "wvsd":"S.D.W.Va.", "wyd":"E.D.Wis."};

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
function havePACERCookie() {

    var cookieMan = CCGS("@mozilla.org/cookiemanager;1",
			 "nsICookieManager");

    var foundPacerUser = false;
    
    var cookieEnum = cookieMan.enumerator;
    while (cookieEnum.hasMoreElements()) {
	var cookie = cookieEnum.getNext();
	//log(cookie.name);
	if (cookie instanceof Components.interfaces.nsICookie){
	    if (cookie.host.match("uscourts.gov")) {
			if (cookie.name.match("KEY")) {
			    return false;
			}
		if (cookie.name.match("PacerUser")) {
		    foundPacerUser = true;
		    //log("PacerUser" + cookie.value);
		}
		
	    }
	}
    }

    if (foundPacerUser == true) {
	//log("havePACERCookie returning true");
	return true;
    } else {
	//log("havePACERCookie returning false");
	return false;
    }

}

// Helper function to get interfaces
function CCGS(contractID, interfaceName) {
	
	if (interfaceName != "nsIConsoleService") {
	    //log("CCGS called with: " + contractID + " " + interfaceName);
	}
    return Cc[contractID].getService(Ci[interfaceName]);
}


// Helper function to log to both stdout and Error Console
function log(text) {
    var msg = "Recap: " + text + "\n";
    
    dump(msg);
    
    var consoleService = CCGS("@mozilla.org/consoleservice;1",
			      "nsIConsoleService");
    consoleService.logStringMessage(msg);
}

function showAlert(icon, headline, message) {
		try {
			alertsService.showAlertNotification(icon, 
	       headline, message);
		} catch (e) {
			log("couldn't start up alert service (are we on OSX without Growl installed?)");
		}

}
