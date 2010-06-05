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

var ICON_LOGGED_IN = "chrome://recap/skin/recap-icon.png";
var ICON_LOGGED_IN_32 = "chrome://recap/skin/recap-icon-32.png";
var ICON_LOGGED_OUT = "chrome://recap/skin/recap-icon-grey.png";
var ICON_LOGGED_OUT_32 = "chrome://recap/skin/recap-icon-grey-32.png";
var ICON_DISABLED = "chrome://recap/skin/recap-icon-disabled.png";
var ICON_DISABLED_32 = "chrome://recap/skin/recap-icon-disabled-32.png";

var SERVER_URL = "http://recapextension.org/recap/";

var UPLOAD_URL = SERVER_URL + "upload/";
var QUERY_URL = SERVER_URL + "query/";
var QUERY_CASES_URL = SERVER_URL + "query_cases/";
var ADDDOCMETA_URL = SERVER_URL + "adddocmeta/";

// List of all PACER/ECF domains
var PACER_DOMAINS = ["ecf.almd.uscourts.gov", "ecf.alnd.uscourts.gov", "ecf.alsd.uscourts.gov", "ecf.akd.uscourts.gov", "ecf.azd.uscourts.gov", "ecf.ared.uscourts.gov", "ecf.arwd.uscourts.gov", "ecf.cacd.uscourts.gov", "ecf.caed.uscourts.gov", "ecf.cand.uscourts.gov", "ecf.casd.uscourts.gov", "ecf.cod.uscourts.gov", "ecf.ctd.uscourts.gov", "ecf.ded.uscourts.gov", "ecf.dcd.uscourts.gov", "ecf.flmd.uscourts.gov", "ecf.flnd.uscourts.gov", "ecf.flsd.uscourts.gov", "ecf.gamd.uscourts.gov", "ecf.gand.uscourts.gov", "ecf.gasd.uscourts.gov", "ecf.gud.uscourts.gov", "ecf.hid.uscourts.gov", "ecf.idd.uscourts.gov", "ecf.ilcd.uscourts.gov", "ecf.ilnd.uscourts.gov", "ecf.ilsd.uscourts.gov", "ecf.innd.uscourts.gov", "ecf.insd.uscourts.gov", "ecf.iand.uscourts.gov", "ecf.iasd.uscourts.gov", "ecf.ksd.uscourts.gov", "ecf.kyed.uscourts.gov", "ecf.kywd.uscourts.gov", "ecf.laed.uscourts.gov", "ecf.lamd.uscourts.gov", "ecf.lawd.uscourts.gov", "ecf.med.uscourts.gov", "ecf.mdd.uscourts.gov", "ecf.mad.uscourts.gov", "ecf.mied.uscourts.gov", "ecf.miwd.uscourts.gov", "ecf.mnd.uscourts.gov", "ecf.msnd.uscourts.gov", "ecf.mssd.uscourts.gov", "ecf.moed.uscourts.gov", "ecf.mowd.uscourts.gov", "ecf.mtd.uscourts.gov", "ecf.ned.uscourts.gov", "ecf.nvd.uscourts.gov", "ecf.nhd.uscourts.gov", "ecf.njd.uscourts.gov", "ecf.nmd.uscourts.gov", "ecf.nyed.uscourts.gov", "ecf.nynd.uscourts.gov", "ecf.nysd.uscourts.gov", "ecf.nywd.uscourts.gov", "ecf.nced.uscourts.gov", "ecf.ncmd.uscourts.gov", "ecf.ncwd.uscourts.gov", "ecf.ndd.uscourts.gov", "ecf.nmid.uscourts.gov", "ecf.ohnd.uscourts.gov", "ecf.ohsd.uscourts.gov", "ecf.oked.uscourts.gov", "ecf.oknd.uscourts.gov", "ecf.okwd.uscourts.gov", "ecf.ord.uscourts.gov", "ecf.paed.uscourts.gov", "ecf.pamd.uscourts.gov", "ecf.pawd.uscourts.gov", "ecf.prd.uscourts.gov", "ecf.rid.uscourts.gov", "ecf.scd.uscourts.gov", "ecf.sdd.uscourts.gov", "ecf.tned.uscourts.gov", "ecf.tnmd.uscourts.gov", "ecf.tnwd.uscourts.gov", "ecf.txed.uscourts.gov", "ecf.txnd.uscourts.gov", "ecf.txsd.uscourts.gov", "ecf.txwd.uscourts.gov", "ecf.cofc.uscourts.gov", "ecf.utd.uscourts.gov", "ecf.vtd.uscourts.gov", "ecf.vid.uscourts.gov", "ecf.vaed.uscourts.gov", "ecf.vawd.uscourts.gov", "ecf.waed.uscourts.gov", "ecf.wawd.uscourts.gov", "ecf.wvnd.uscourts.gov", "ecf.wvsd.uscourts.gov", "ecf.wied.uscourts.gov", "ecf.wiwd.uscourts.gov", "pacer.wiwd.uscourts.gov", "ecf.wyd.uscourts.gov", "ecf.cit.uscourts.gov", "ecf.akb.uscourts.gov", "ecf.almb.uscourts.gov", "ecf.alnb.uscourts.gov", "ecf.alsb.uscourts.gov", "ecf.areb.uscourts.gov", "ecf.arwb.uscourts.gov", "ecf.azb.uscourts.gov", "ecf.cacb.uscourts.gov", "ecf.caeb.uscourts.gov", "ecf.canb.uscourts.gov", "ecf.casb.uscourts.gov", "ecf.cob.uscourts.gov", "ecf.ctb.uscourts.gov", "ecf.dcb.uscourts.gov", "ecf.deb.uscourts.gov", "ecf.flmb.uscourts.gov", "ecf.flnb.uscourts.gov", "ecf.flsb.uscourts.gov", "ecf.gamb.uscourts.gov", "ecf.ganb.uscourts.gov", "ecf.gasb.uscourts.gov", "ecf.gub.uscourts.gov", "ecf.hib.uscourts.gov", "ecf.ianb.uscourts.gov", "ecf.iasb.uscourts.gov", "ecf.idb.uscourts.gov", "ecf.ilcb.uscourts.gov", "ecf.ilnb.uscourts.gov", "ecf.ilsb.uscourts.gov", "ecf.innb.uscourts.gov", "ecf.insb.uscourts.gov", "ecf.ksb.uscourts.gov", "ecf.kyeb.uscourts.gov", "ecf.kywb.uscourts.gov", "ecf.laeb.uscourts.gov", "ecf.lamb.uscourts.gov", "ecf.lawb.uscourts.gov", "ecf.mab.uscourts.gov", "ecf.mdb.uscourts.gov", "ecf.meb.uscourts.gov", "ecf.mieb.uscourts.gov", "ecf.miwb.uscourts.gov", "ecf.mnb.uscourts.gov", "ecf.moeb.uscourts.gov", "ecf.mowb.uscourts.gov", "ecf.msnb.uscourts.gov", "ecf.mssb.uscourts.gov", "ecf.mtb.uscourts.gov", "ecf.nceb.uscourts.gov", "ecf.ncmb.uscourts.gov", "ecf.ncwb.uscourts.gov", "ecf.ndb.uscourts.gov", "ecf.neb.uscourts.gov", "ecf.nhb.uscourts.gov", "ecf.njb.uscourts.gov", "ecf.nmb.uscourts.gov", "ecf.nvb.uscourts.gov", "ecf.nyeb.uscourts.gov", "ecf.nynb.uscourts.gov", "ecf.nysb.uscourts.gov", "ecf.nywb.uscourts.gov", "ecf.ohnb.uscourts.gov", "ecf.ohsb.uscourts.gov", "ecf.okeb.uscourts.gov", "ecf.oknb.uscourts.gov", "ecf.okwb.uscourts.gov", "ecf.orb.uscourts.gov", "ecf.paeb.uscourts.gov", "ecf.pamb.uscourts.gov", "ecf.pawb.uscourts.gov", "ecf.prb.uscourts.gov", "ecf.rib.uscourts.gov", "ecf.scb.uscourts.gov", "ecf.sdb.uscourts.gov", "ecf.tneb.uscourts.gov", "ecf.tnmb.uscourts.gov", "ecf.tnwb.uscourts.gov", "ecf.txeb.uscourts.gov", "ecf.txnb.uscourts.gov", "ecf.txsb.uscourts.gov", "ecf.txwb.uscourts.gov", "ecf.utb.uscourts.gov", "ecf.vaeb.uscourts.gov", "ecf.vawb.uscourts.gov", "ecf.vib.uscourts.gov", "ecf.vtb.uscourts.gov", "ecf.waeb.uscourts.gov", "ecf.wawb.uscourts.gov", "ecf.wieb.uscourts.gov", "ecf.wiwb.uscourts.gov", "ecf.wvnb.uscourts.gov", "ecf.wvsb.uscourts.gov", "ecf.wyb.uscourts.gov", "ecf.nysb-mega.uscourts.gov"];

// PACER court id to West-style court cite
var PACER_TO_WEST_COURT = {"akd":"D.Alaska", "almd":"M.D.Ala.", "alnd":"N.D.Ala.", "alsd":"S.D.Ala.", "ared":"E.D.Ark.", "arwd":"W.D.Ark.", "azd":"D.Ariz.", "cacd":"C.D.Cal.", "caed":"E.D.Cal.", "cand":"N.D.Cal.", "casd":"S.D.Cal.", "cod":"D.Colo.", "ctd":"D.Conn.", "dcd":"D.D.C.", "ded":"D.Del.", "flmd":"M.D.Fla.", "flnd":"N.D.Fla.", "flsd":"S.D.Fla.", "gamd":"M.D.Ga.", "gand":"N.D.Ga.", "gasd":"S.D.Ga.", "gud":"D.Guam", "hid":"D.Hawaii", "iand":"N.D.Iowa", "iasd":"S.D.Iowa", "idd":"D.Idaho", "ilcd":"C.D.Ill.", "ilnd":"N.D.Ill.", "ilsd":"S.D.Ill.", "innd":"N.D.Ind.", "insd":"S.D.Ind.", "ksd":"D.Kan.", "kyed":"E.D.Ky.", "kywd":"W.D.Ky.", "laed":"W.D.La.", "lamd":"M.D.La.", "lawd":"W.D.La.", "mad":"D.Mass.", "mdd":"D.Md.", "med":"D.Me.", "mied":"E.D.Mich.", "miwd":"W.D.Mich.", "mnd":"D.Minn.", "moed":"W.D.Mo.", "mowd":"W.D.Mo.", "msnd":"N.D.Miss", "mssd":"S.D.Miss.", "mtd":"D.Mont.", "nced":"E.D.N.C.", "ncmd":"M.D.N.C.", "ncwd":"W.D.N.C.", "ndd":"D.N.D.", "ned":"D.Neb.", "nhd":"D.N.H.", "njd":"D.N.J.", "nmd":"D.N.M.", "nmid":"N.MarianaIslands", "nvd":"D.Nev.", "nyed":"E.D.N.Y.", "nynd":"N.D.N.Y.", "nysd":"S.D.N.Y.", "nywd":"W.D.N.Y.", "ohnd":"N.D.Ohio", "ohsd":"S.D.Ohio", "oked":"E.D.Okla.", "oknd":"N.D.Okla.", "okwd":"W.D.Okla.", "ord":"D.Or.", "paed":"E.D.Pa.", "pamd":"M.D.Pa.", "pawd":"W.D.Pa.", "prd":"D.P.R.", "rid":"D.R.I.", "scd":"D.S.C.", "sdd":"D.S.D.", "tned":"E.D.Tenn.", "tnmd":"M.D.Tenn.", "tnwd":"W.D.Tenn.", "txed":"E.D.Tex.", "txnd":"N.D.Tex.", "txsd":"S.D.Tex.", "txwd":"W.D.Tex.", "utd":"D.Utah", "vaed":"E.D.Va.", "vawd":"W.D.Va.", "vid":"D.VirginIslands", "vtd":"D.Vt.", "waed":"E.D.Wash.", "wawd":"W.D.Wash.", "wied":"E.D.Wis.", "wiwd":"W.D.Wis", "wvnd":"N.D.W.Va.", "wvsd":"S.D.W.Va.", "wyd":"E.D.Wis.","cit":"CIT","akb":"Bankr.D.Alaska","almb":"Bankr.M.D.Ala.","alnb":"Bankr.N.D.Ala.","alsb":"Bankr.S.D.Ala.","areb":"Bankr.E.D.Ark.","arwb":"Bankr.W.D.Ark.","azb":"Bankr.D.Ariz.","cacb":"Bankr.C.D.Cal.","caeb":"Bankr.E.D.Cal.","canb":"Bankr.N.D.Cal.","casb":"Bankr.S.D.Cal.","cob":"Bankr.D.Colo.","ctb":"Bankr.D.Conn.","dcb":"Bankr.D.D.C.","deb":"Bankr.D.Del.","flmb":"Bankr.M.D.Fla.","flnb":"Bankr.N.D.Fla.","flsb":"Bankr.S.D.Fla.","gamb":"Bankr.M.D.Ga.","ganb":"Bankr.N.D.Ga.","gasb":"Bankr.S.D.Ga.","gub":"Bankr.D.Guam","hib":"Bankr.D.Hawaii","ianb":"Bankr.N.D.Iowa","iasb":"Bankr.S.D.Iowa","idb":"Bankr.D.Idaho","ilcb":"Bankr.C.D.Ill.","ilnb":"Bankr.N.D.Ill.","ilsb":"Bankr.S.D.Ill.","innb":"Bankr.N.D.Ind.","insb":"Bankr.S.D.Ind.","ksb":"Bankr.D.Kan.","kyeb":"Bankr.E.D.Ky.","kywb":"Bankr.W.D.Ky.","laeb":"Bankr.W.D.La.","lamb":"Bankr.M.D.La.","lawb":"Bankr.W.D.La.","mab":"Bankr.D.Mass.","mdb":"Bankr.D.Md.","meb":"Bankr.D.Me.","mieb":"Bankr.E.D.Mich.","miwb":"Bankr.W.D.Mich.","mnb":"Bankr.D.Minn.","moeb":"Bankr.W.D.Mo.","mowb":"Bankr.W.D.Mo.","msnb":"Bankr.N.D.Miss","mssb":"Bankr.S.D.Miss.","mtb":"Bankr.D.Mont.","nceb":"Bankr.E.D.N.C.","ncmb":"Bankr.M.D.N.C.","ncwb":"Bankr.W.D.N.C.","ndb":"Bankr.D.N.D.","neb":"Bankr.D.Neb.","nhb":"Bankr.D.N.H.","njb":"Bankr.D.N.J.","nmb":"Bankr.D.N.M.","nvb":"Bankr.D.Nev.","nyeb":"Bankr.E.D.N.Y.","nynb":"Bankr.N.D.N.Y.","nysb":"Bankr.S.D.N.Y.","nywb":"Bankr.W.D.N.Y.","ohnb":"Bankr.N.D.Ohio","ohsb":"Bankr.S.D.Ohio","okeb":"Bankr.E.D.Okla.","oknb":"Bankr.N.D.Okla.","okwb":"Bankr.W.D.Okla.","orb":"Bankr.D.Or.","paeb":"Bankr.E.D.Pa.","pamb":"Bankr.M.D.Pa.","pawb":"Bankr.W.D.Pa.","prb":"Bankr.D.P.R.","rib":"Bankr.D.R.I.","scb":"Bankr.D.S.C.","sdb":"Bankr.D.S.D.","tneb":"Bankr.E.D.Tenn.","tnmb":"Bankr.M.D.Tenn.","tnwb":"Bankr.W.D.Tenn.","txeb":"Bankr.E.D.Tex.","txnb":"Bankr.N.D.Tex.","txsb":"Bankr.S.D.Tex.","txwb":"Bankr.W.D.Tex.","utb":"Bankr.D.Utah","vaeb":"Bankr.E.D.Va.","vawb":"Bankr.W.D.Va.","vib":"Bankr.D.VirginIslands","vtb":"Bankr.D.Vt.","waeb":"Bankr.E.D.Wash.","wawb":"Bankr.W.D.Wash.","wieb":"Bankr.E.D.Wis.","wiwb":"Bankr.W.D.Wis","wvnb":"Bankr.N.D.W.Va.","wvsb":"Bankr.S.D.W.Va.","wyb":"Bankr.E.D.Wis.","nysb-mega":"Bankr.S.D.N.Y."};

var UNSUPPORTED_PACER_DOMAINS = ["ecf.ca1.uscourts.gov", "ecf.ca2.uscourts.gov", "pacer.ca2.uscourts.gov", "ecf.ca3.uscourts.gov", "ecf.ca4.uscourts.gov", "ecf.ca5.uscourts.gov", "ecf.ca6.uscourts.gov", "ecf.ca7.uscourts.gov", "ecf.ca8.uscourts.gov", "ecf.ca9.uscourts.gov", "ecf.ca10.uscourts.gov", "ecf.ca11.uscourts.gov","pacer.ca11.uscourts.gov", "ecf.cadc.uscourts.gov","ecf.cafc.uscourts.gov","pacer.cafc.uscourts.gov", "pacer.login.uscourts.gov"];
function isPDF(mimetype) {
    if (typeof mimetype == 'undefined') {
	return false;
    }
    return (mimetype == "application/pdf") ? true: false;
}

function isHTML(mimetype) {
    if (typeof mimetype == 'undefined' || mimetype == null) {
	return false;
    }
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

// RECAP currently only works on District and Bankruptcy courts
function isUnsupportedPACERHost(hostname) {
    return (UNSUPPORTED_PACER_DOMAINS.indexOf(hostname) >= 0) ? true : false;
}

// Get court name from hostname
function getCourtFromHost(hostname) {
    var court = null;
    try {
	court = hostname.match(/([^\.]*)\.uscourts.gov/i)[1];
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
	if (cookie instanceof Components.interfaces.nsICookie){
	    if (cookie.host.match("uscourts.gov")) {
			if (cookie.name.match("KEY")) {
			    return false;
			}
		if (cookie.name.match("PacerUser")) {
		    if(cookie.value.indexOf("unvalidated") >=0){
			    return false;
		    }
		    else{
		            foundPacerUser = true;
		    }
		}
	    }
	}
    }

    if (foundPacerUser == true) {
	return true;
    } else {
	return false;
    }

}

// Helper function to get interfaces
function CCGS(contractID, interfaceName) {
	
	if (interfaceName != "nsIConsoleService") {
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
    var prefs = CCGS("@mozilla.org/preferences-service;1",
		     "nsIPrefService").getBranch("recap.");
    
    if (prefs.getBoolPref("display_notifications") == false) {
	return;
    }
    
    try {
	alertsService = CCGS("@mozilla.org/alerts-service;1",
				     "nsIAlertsService");
	alertsService.showAlertNotification(icon, headline, message);
					    
    } catch (e) {
	log("couldn't start up alert service " +
	    "are we on OSX without Growl installed?)");
    }
}

function updateStatusIcon() {
    //log("current domain is PACER domain? " + isPACERHost(gBrowser.selectedBrowser.contentDocument.domain));
    //
    var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"]
                   .getService(Components.interfaces.nsIWindowMediator);
    var browserWindow = wm.getMostRecentWindow("navigator:browser");

    var statusIcon = browserWindow.document.getElementById("recap-panel-image");
    var hostname = browserWindow.gBrowser.selectedBrowser.contentDocument.domain;
    
    var prefs = CCGS("@mozilla.org/preferences-service;1",
		     "nsIPrefService").getBranch("recap.");
  
    if(prefs.getBoolPref("temp_disable") == true) {
            //make a red icon and put it here!
	    statusIcon.src= ICON_DISABLED;
	    statusIcon.tooltipText = "RECAP is temporarily deactivated. Click to activate.";
	    return;
    }

    if (isPACERHost(hostname) && 
	havePACERCookie()) {
	    statusIcon.tooltipText = "You are logged into PACER.";
	    statusIcon.src = ICON_LOGGED_IN;
    }
    else if (isUnsupportedPACERHost(hostname) && 
	havePACERCookie()) {
	    statusIcon.tooltipText = "RECAP does not work on Appellate Courts";
	    statusIcon.src = ICON_DISABLED;

    } else {
	statusIcon.src= ICON_LOGGED_OUT;
	statusIcon.tooltipText = "You are logged out of PACER.";
    }
}
function handlePrefDisable(){
        var prefs = CCGS("@mozilla.org/preferences-service;1",
		     "nsIPrefService").getBranch("recap.");
  
        var curr_disable = prefs.getBoolPref("temp_disable");
    	
	updateStatusIcon();
        
	if(curr_disable == true){
		showAlert(ICON_DISABLED_32, 
    			"RECAP deactivated.", "RECAP will stay deactivated even when logged into PACER.");
	}
	else{
    		var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"]
                   	.getService(Components.interfaces.nsIWindowMediator);
    		var browserWindow = wm.getMostRecentWindow("navigator:browser");
		var URIhost = browserWindow.gBrowser.selectedBrowser.contentDocument.domain;
		
		if(isPACERHost(URIhost) && havePACERCookie()){
			
			showAlert(ICON_LOGGED_IN_32, 
    			    "RECAP activated.", "You are logged into PACER.");
		
		}
		else{
			showAlert(ICON_LOGGED_OUT_32, 
    				"RECAP activated.", "RECAP will be activated when logged into PACER.");

		}

	}

	return true;
}
