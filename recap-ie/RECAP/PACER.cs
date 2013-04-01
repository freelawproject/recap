// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// ------------------
// PACER-related functions.

using System.Web;
using System.Collections;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Text.RegularExpressions;
using MSHTML;

namespace RECAP {
    public static class PACER {

        public static bool IsPacerUrl(string url) {
            return (new Regex(@"(ecf|ecf-train|pacer).*.uscourts.gov/")).IsMatch(url);
        }
        public static bool IsDocumentUrl(string url) {
            return (new Regex(@"(/doc1/\d+|/cgi-bin/show_doc)")).IsMatch(url) && (PACER.GetCourtFromUrl(url) != null);
        }
        public static bool IsConvertibleDocumentUrl(string url) {
            return (new Regex(@"/cgi-bin/show_docs")).IsMatch(url) && (PACER.GetCourtFromUrl(url) != null);
        }
        public static bool IsDocketQueryUrl(string url) {
            return (new Regex(@"/(DktRpt|HistDocQry)\.pl\?\d+$")).IsMatch(url);
        }
        public static bool IsDocketDisplayUrl(string url) {
            return (new Regex(@"/(DktRpt|HistDocQry)\.pl\?\w+-[\w-]+$")).IsMatch(url);
        }
        public static bool IsAttachmentMenuPage(string url, HTMLDocument document) {
            IHTMLElementCollection inputs = document.getElementsByTagName("input");
            return (new Regex(@"/doc1/\d+")).IsMatch(url) && (inputs.length > 0) && (inputs.item(inputs.length - 1).getAttribute("value") == "Download All");
        }
        public static bool IsSingleDocumentPage(string url, HTMLDocument document) {
            IHTMLElementCollection inputs = document.getElementsByTagName("input");
            return (new Regex(@"/doc1/\d+")).IsMatch(url) && (inputs.length > 0) && (inputs.item(inputs.length - 1).getAttribute("value") == "View Document");
        }
        public static string GetCourtFromUrl(string url) {
            Match match = (new Regex(@"^\w+://(ecf|ecf-train|pacer)\.(\w+)\.uscourts\.gov/")).Match(url);
            return match.Success ? match.Groups[2].ToString() : null;
        }
        public static string GetCaseNumberFromUrl(string url) {
            Match match = (new Regex(@"\?(\d+)$")).Match(url);
            return match.Success ? match.Groups[1].ToString() : null;
        }
        public static string GetBaseNameFromUrl(string url) {
            Match match = (new Regex(@".*/(.+?)\?.*")).Match(url);
            return match.Success ? match.Groups[1].ToString() : null;
        }
        public static string GetDocumentIdFromUrl(string url) {
            Match match = (new Regex(@"/doc1/(\d+)$")).Match(url);
            return match.Success ? match.Groups[1].ToString() : null;
        }


        public static void ConvertDocumentUrl(string url, ConvertDocumentUrlCallback callback) {

            string schemeHost = (new Regex(@"^\w+://[^/]+")).Match(url).ToString();
            string query = (new Regex(@"\?.*")).Match(url).ToString();
            string queryurl = schemeHost + "/cgi-bin/document_link.pl?document" + query.Replace('?', 'K').Replace('&', 'K').Replace('=', 'V');

            NameValueCollection data = HttpUtility.ParseQueryString(query);

            (new XHR(queryurl, null, "text", (type, responseData) => {
                string newurl = (string) responseData;
                callback(newurl, PACER.GetDocumentIdFromUrl(newurl), data["caseid"], data["de_seq_num"], data["dm_id"], data["doc_num"]);
            })).Send();

        }

        public delegate void ConvertDocumentUrlCallback(string newurl, string docid, string caseid, string deseqnum, string dmid, string docnum);

        public static Hashtable COURTS = new Hashtable() {
            {"akb", "Bankr.D.Alaska"},
            {"akd", "D.Alaska"},
            {"almb", "Bankr.M.D.Ala."},
            {"almd", "M.D.Ala."},
            {"alnb", "Bankr.N.D.Ala."},
            {"alnd", "N.D.Ala."},
            {"alsb", "Bankr.S.D.Ala."},
            {"alsd", "S.D.Ala."},
            {"areb", "Bankr.E.D.Ark."},
            {"ared", "E.D.Ark."},
            {"arwb", "Bankr.W.D.Ark."},
            {"arwd", "W.D.Ark."},
            {"azb", "Bankr.D.Ariz."},
            {"azd", "D.Ariz."},
            {"cacb", "Bankr.C.D.Cal."},
            {"cacd", "C.D.Cal."},
            {"caeb", "Bankr.E.D.Cal."},
            {"caed", "E.D.Cal."},
            {"canb", "Bankr.N.D.Cal."},
            {"cand", "N.D.Cal."},
            {"casb", "Bankr.S.D.Cal."},
            {"casd", "S.D.Cal."},
            {"cit", "CIT"},
            {"cob", "Bankr.D.Colo."},
            {"cod", "D.Colo."},
            {"cofc", "Fed.Cl."},
            {"ctb", "Bankr.D.Conn."},
            {"ctd", "D.Conn."},
            {"dcb", "Bankr.D.D.C."},
            {"dcd", "D.D.C."},
            {"deb", "Bankr.D.Del."},
            {"ded", "D.Del."},
            {"flmb", "Bankr.M.D.Fla."},
            {"flmd", "M.D.Fla."},
            {"flnb", "Bankr.N.D.Fla."},
            {"flnd", "N.D.Fla."},
            {"flsb", "Bankr.S.D.Fla."},
            {"flsd", "S.D.Fla."},
            {"gamb", "Bankr.M.D.Ga."},
            {"gamd", "M.D.Ga."},
            {"ganb", "Bankr.N.D.Ga."},
            {"gand", "N.D.Ga."},
            {"gasb", "Bankr.S.D.Ga."},
            {"gasd", "S.D.Ga."},
            {"gub", "Bankr.D.Guam"},
            {"gud", "D.Guam"},
            {"hib", "Bankr.D.Hawaii"},
            {"hid", "D.Hawaii"},
            {"ianb", "Bankr.N.D.Iowa"},
            {"iand", "N.D.Iowa"},
            {"iasb", "Bankr.S.D.Iowa"},
            {"iasd", "S.D.Iowa"},
            {"idb", "Bankr.D.Idaho"},
            {"idd", "D.Idaho"},
            {"ilcb", "Bankr.C.D.Ill."},
            {"ilcd", "C.D.Ill."},
            {"ilnb", "Bankr.N.D.Ill."},
            {"ilnd", "N.D.Ill."},
            {"ilsb", "Bankr.S.D.Ill."},
            {"ilsd", "S.D.Ill."},
            {"innb", "Bankr.N.D.Ind."},
            {"innd", "N.D.Ind."},
            {"insb", "Bankr.S.D.Ind."},
            {"insd", "S.D.Ind."},
            {"ksb", "Bankr.D.Kan."},
            {"ksd", "D.Kan."},
            {"kyeb", "Bankr.E.D.Ky."},
            {"kyed", "E.D.Ky."},
            {"kywb", "Bankr.W.D.Ky."},
            {"kywd", "W.D.Ky."},
            {"laeb", "Bankr.E.D.La."},
            {"laed", "E.D.La."},
            {"lamb", "Bankr.M.D.La."},
            {"lamd", "M.D.La."},
            {"lawb", "Bankr.W.D.La."},
            {"lawd", "W.D.La."},
            {"mab", "Bankr.D.Mass."},
            {"mad", "D.Mass."},
            {"mdb", "Bankr.D.Md."},
            {"mdd", "D.Md."},
            {"meb", "Bankr.D.Me."},
            {"med", "D.Me."},
            {"mieb", "Bankr.E.D.Mich."},
            {"mied", "E.D.Mich."},
            {"miwb", "Bankr.W.D.Mich."},
            {"miwd", "W.D.Mich."},
            {"mnb", "Bankr.D.Minn."},
            {"mnd", "D.Minn."},
            {"moeb", "Bankr.E.D.Mo."},
            {"moed", "E.D.Mo."},
            {"mowb", "Bankr.W.D.Mo."},
            {"mowd", "W.D.Mo."},
            {"msnb", "Bankr.N.D.Miss"},
            {"msnd", "N.D.Miss"},
            {"mssb", "Bankr.S.D.Miss."},
            {"mssd", "S.D.Miss."},
            {"mtb", "Bankr.D.Mont."},
            {"mtd", "D.Mont."},
            {"nceb", "Bankr.E.D.N.C."},
            {"nced", "E.D.N.C."},
            {"ncmb", "Bankr.M.D.N.C."},
            {"ncmd", "M.D.N.C."},
            {"ncwb", "Bankr.W.D.N.C."},
            {"ncwd", "W.D.N.C."},
            {"ndb", "Bankr.D.N.D."},
            {"ndd", "D.N.D."},
            {"neb", "Bankr.D.Neb."},
            {"ned", "D.Neb."},
            {"nhb", "Bankr.D.N.H."},
            {"nhd", "D.N.H."},
            {"njb", "Bankr.D.N.J."},
            {"njd", "D.N.J."},
            {"nmb", "Bankr.D.N.M."},
            {"nmd", "D.N.M."},
            {"nmid", "N.MarianaIslands"},
            {"nvb", "Bankr.D.Nev."},
            {"nvd", "D.Nev."},
            {"nyeb", "Bankr.E.D.N.Y."},
            {"nyed", "E.D.N.Y."},
            {"nynb", "Bankr.N.D.N.Y."},
            {"nynd", "N.D.N.Y."},
            {"nysb", "Bankr.S.D.N.Y."},
            {"nysb-mega", "Bankr.S.D.N.Y."},
            {"nysd", "S.D.N.Y."},
            {"nywb", "Bankr.W.D.N.Y."},
            {"nywd", "W.D.N.Y."},
            {"ohnb", "Bankr.N.D.Ohio"},
            {"ohnd", "N.D.Ohio"},
            {"ohsb", "Bankr.S.D.Ohio"},
            {"ohsd", "S.D.Ohio"},
            {"okeb", "Bankr.E.D.Okla."},
            {"oked", "E.D.Okla."},
            {"oknb", "Bankr.N.D.Okla."},
            {"oknd", "N.D.Okla."},
            {"okwb", "Bankr.W.D.Okla."},
            {"okwd", "W.D.Okla."},
            {"orb", "Bankr.D.Or."},
            {"ord", "D.Or."},
            {"paeb", "Bankr.E.D.Pa."},
            {"paed", "E.D.Pa."},
            {"pamb", "Bankr.M.D.Pa."},
            {"pamd", "M.D.Pa."},
            {"pawb", "Bankr.W.D.Pa."},
            {"pawd", "W.D.Pa."},
            {"prb", "Bankr.D.P.R."},
            {"prd", "D.P.R."},
            {"rib", "Bankr.D.R.I."},
            {"rid", "D.R.I."},
            {"scb", "Bankr.D.S.C."},
            {"scd", "D.S.C."},
            {"sdb", "Bankr.D.S.D."},
            {"sdd", "D.S.D."},
            {"tneb", "Bankr.E.D.Tenn."},
            {"tned", "E.D.Tenn."},
            {"tnmb", "Bankr.M.D.Tenn."},
            {"tnmd", "M.D.Tenn."},
            {"tnwb", "Bankr.W.D.Tenn."},
            {"tnwd", "W.D.Tenn."},
            {"txeb", "Bankr.E.D.Tex."},
            {"txed", "E.D.Tex."},
            {"txnb", "Bankr.N.D.Tex."},
            {"txnd", "N.D.Tex."},
            {"txsb", "Bankr.S.D.Tex."},
            {"txsd", "S.D.Tex."},
            {"txwb", "Bankr.W.D.Tex."},
            {"txwd", "W.D.Tex."},
            {"utb", "Bankr.D.Utah"},
            {"utd", "D.Utah"},
            {"vaeb", "Bankr.E.D.Va."},
            {"vaed", "E.D.Va."},
            {"vawb", "Bankr.W.D.Va."},
            {"vawd", "W.D.Va."},
            {"vib", "Bankr.D.VirginIslands"},
            {"vid", "D.VirginIslands"},
            {"vtb", "Bankr.D.Vt."},
            {"vtd", "D.Vt."},
            {"waeb", "Bankr.E.D.Wash."},
            {"waed", "E.D.Wash."},
            {"wawb", "Bankr.W.D.Wash."},
            {"wawd", "W.D.Wash."},
            {"wieb", "Bankr.E.D.Wis."},
            {"wied", "E.D.Wis."},
            {"wiwb", "Bankr.W.D.Wis"},
            {"wiwd", "W.D.Wis"},
            {"wvnb", "Bankr.N.D.W.Va."},
            {"wvnd", "N.D.W.Va."},
            {"wvsb", "Bankr.S.D.W.Va."},
            {"wvsd", "S.D.W.Va."},
            {"wyb", "Bankr.D.Wyo."},
            {"wyd", "D.Wyo."}
        };

    }
}