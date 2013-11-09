// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// The RECAP IE Extension is free software: you can redistribute it 
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation, either version 3 of the 
// License, or (at your option) any later version.
//
// The RECAP IE Extension is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with the RECAP IE Extension.  If not, see: 
// http://www.gnu.org/licenses/
//
// ------------------
// RECAP-related functions.
//
// WARNING: Not yet debugged.
// WARNING: Functions with XHR calls have yet to be made asynchronous.

using System;
using System.IO;
using System.Web;
using System.Text;
using System.Text.RegularExpressions;
using System.Collections;
using System.Collections.Generic;
using SHDocVw;
using MSHTML;

namespace RECAP {
    public class RECAP {

        private const string SERVER_ROOT = "http://dev.recapextension.org/recap";

        private static Hashtable CaseMeta = new Hashtable();
        private static Hashtable DocMeta = new Hashtable();

        private WebBrowser browser;
        private HTMLDocument document;

        private string url;
        private string previous;
        private string court;

        public RECAP(WebBrowser browser) {
            this.browser = browser;
        }


        // Public methods

        public void ProcessDocument() {

            this.document = this.browser.Document;
            this.previous = this.url;
            this.url = this.browser.LocationURL.ToString();
            if (PACER.IsPacerUrl(this.url)) {
                this.court = PACER.GetCourtFromUrl(this.url);
            } else {
                this.court = null;
                return;
            }

            if (PACER.IsDocketQueryUrl(this.url)) {
                this.ProcessDocketQuery();
            }
            if (PACER.IsDocketDisplayUrl(this.url)) {
                this.ProcessDocketDisplay();
            }
            if (PACER.IsAttachmentMenuPage(this.url, this.document)) {
                this.ProcessAttachmentMenuPage();
            }
            if (PACER.IsSingleDocumentPage(this.url, this.document)) {
                this.ProcessSingleDocumentPage();
            }
            this.ProcessLinks();
        }


        // Private methods

        private void ShowUploadNotification(string message) {
            System.Windows.Forms.MessageBox.Show(message, "RECAP Upload");
        }

        private void ProcessDocketQuery() {
            GetAvailabilityForDocket(this.court, PACER.GetCaseNumberFromUrl(url), (responseData) => {
                CaseQueryResponse caseQueryResponse = (CaseQueryResponse) responseData;
                if (!String.IsNullOrEmpty(caseQueryResponse.docket_url)) {

                    // <a title="..." href="..."><img src="..."/> ... </a>
                    IHTMLElement a = this.document.createElement("a");
                    a.setAttribute("title", "Docket is available for free from RECAP.");
                    a.setAttribute("href", caseQueryResponse.docket_url);

                    IHTMLElement img = this.document.createElement("img");
                    img.setAttribute("src", "file://" + Path.Combine(typeof(RECAP).Assembly.Location, "icon-16.png"));

                    a.innerText = " Get this docket as of " + caseQueryResponse.timestamp + " for free from RECAP.";
                    ((HTMLAnchorElement) a).insertAdjacentElement("afterBegin", img);

                    // <br/>
                    IHTMLElement br = this.document.createElement("br");

                    // <small> ... </small>
                    IHTMLElement small = this.document.createElement("small");
                    small.innerText = "Note that archived dockets may be out of date.";

                    // <div class="recap-banner">
                    //   <a> ... </a>
                    //   <br/>
                    //   <small> ... </small>
                    // </div>
                    IHTMLElement div = this.document.createElement("div");
                    div.setAttribute("className", "recap-banner");
                    ((HTMLDivElement) div).insertAdjacentElement("beforeEnd", a);
                    ((HTMLDivElement) div).insertAdjacentElement("beforeEnd", br);
                    ((HTMLDivElement) div).insertAdjacentElement("beforeEnd", small);

                    // <form><div> ... </div></form>
                    foreach (IHTMLElement form in this.document.getElementsByTagName("form")) {
                        ((HTMLFormElement) form).insertAdjacentElement("beforeEnd", div);
                    }

                }
            });
        }

        private void ProcessDocketDisplay() {
            string casenum = PACER.GetCaseNumberFromUrl(this.previous);
            if (!String.IsNullOrEmpty(casenum)) {
                string filename = PACER.GetBaseNameFromUrl(this.url).Replace(".pl", ".html");
                UploadDocket(this.court, casenum, filename, "text/html", this.document.documentElement.innerHTML, (success) => {
                    if (success) this.ShowUploadNotification("Docket uploaded to the public archive.");
                });
            }
        }

        private void ProcessAttachmentMenuPage() {
            string filename = this.browser.LocationURL;
            UploadAttachmentMenu(this.court, filename, "text/html", this.document.documentElement.innerHTML, (success) => {
                if (success) this.ShowUploadNotification("Menu page uploaded to the public archive.");
            });
        }

        private void ProcessSingleDocumentPage() {

            string[] urls = { this.url };
            GetAvailabilityForDocuments(urls, (responseData) => {
                Hashtable queryResponse = (Hashtable) responseData;
                if (queryResponse.Contains(this.url) && ((Hashtable) queryResponse[this.url]).Contains("filename")) {

                    // <a title="..." href="..."><img src="..."/> ... </a>
                    IHTMLElement a = this.document.createElement("a");
                    a.setAttribute("title", "Document is available for free from RECAP.");
                    a.setAttribute("href", (string) ((Hashtable) queryResponse[this.url])["filename"]);

                    IHTMLElement img = this.document.createElement("img");
                    img.setAttribute("src", "file://" + Path.Combine(typeof(RECAP).Assembly.Location, "icon-16.png"));

                    a.innerText = " Get this document for free from RECAP.";
                    ((HTMLAnchorElement) a).insertAdjacentElement("afterBegin", img);

                    // <div class="recap-banner">
                    //   <a> ... </a>
                    // </div>
                    IHTMLElement div = this.document.createElement("div");
                    div.setAttribute("className", "recap-banner");
                    ((HTMLDivElement) div).insertAdjacentElement("beforeEnd", a);

                    // <form><div> ... </div></form>
                    foreach (IHTMLElement form in this.document.getElementsByTagName("form")) {
                        ((HTMLFormElement) form).insertAdjacentElement("beforeEnd", div);
                    }

                }
            });

            foreach (IHTMLElement form in this.document.getElementsByTagName("form")) {
                ((IHTMLFormElement) form).onsubmit += new HTMLFormElementEvents2_onsubmitEventHandler(this.SingleDocumentHandler);
            }

        }

        private void ProcessLinks() {
            IHTMLElementCollection links = this.document.getElementsByTagName("a");
            List<string> urls = new List<string>();
            foreach (IHTMLElement link in links) {
                string url = link.getAttribute("href");
                if (PACER.IsDocumentUrl(url)) {
                    urls.Add(url);
                }
                link.onmouseover += new HTMLDocumentEvents2_onmouseoverEventHandler(this.LinkMouseOverHandler);
            }
            if (urls.Count > 0) {
                GetAvailabilityForDocuments(urls.ToArray(), (responseData) => {
                    Hashtable queryResponse = (Hashtable) responseData;
                    foreach (IHTMLElement link in links) {
                        string url = link.getAttribute("href");
                        if (queryResponse.Contains(url) && ((Hashtable) queryResponse[url]).Contains("filename")) {

                            // <a class="..." title="..." href="..."><img src="..."/></a>
                            IHTMLElement a = this.document.createElement("a");
                            a.setAttribute("className", "recap-inline");
                            a.setAttribute("title", "Available for free from RECAP.");
                            a.setAttribute("href", (string) ((Hashtable) queryResponse[url])["filename"]);

                            IHTMLElement img = this.document.createElement("img");
                            img.setAttribute("src", "file://" + Path.Combine(typeof(RECAP).Assembly.Location, "icon-16.png"));

                            ((HTMLAnchorElement) a).insertAdjacentElement("beforeEnd", img);

                            // Insert new <a> ... </a> before existing <a> ... </a>
                            ((HTMLAnchorElement) link).insertAdjacentElement("afterEnd", a);

                        }
                    }
                });
            }
        }


        // Callback methods

        private void LinkMouseOverHandler(IHTMLEventObj e) {
            IHTMLElement a = e.srcElement;
            string url = a.getAttribute("href");
            if (PACER.IsConvertibleDocumentUrl(url)) {
                PACER.ConvertDocumentUrl(url, (newurl, docid, caseid, deseqnum, dmid, docnum) => {
                    UploadMetadata(this.court, docid, caseid, deseqnum, dmid, docnum, null);
                });
            }
        }

        private bool SingleDocumentHandler(IHTMLEventObj e) {

            IHTMLElement form = e.srcElement;
            string docid = PACER.GetDocumentIdFromUrl(this.browser.LocationURL);
            string urlpath = this.browser.LocationURL;

            FormData data = new FormData();
            foreach (IHTMLElement input in ((HTMLFormElement) form).getElementsByTagName("input")) {
                if (input.getAttribute("type") == "text") {
                    data.Append(input.getAttribute("name"), input.innerText);
                }
            }

            (new XHR(form.getAttribute("action"), data, "arraybuffer", (XHR.Callback) ((type, responseData) => {
                byte[] responseBytes = (byte[]) responseData;
                if (type == "application/pdf") {
                    string filepath = SaveTemporaryPdf(responseBytes);
                    string html = "<body><iframe src=\"file://" + filepath + "\"></iframe></body>";
                    this.ShowPdfPage(docid, urlpath, filepath, html);
                } else {
                    string html = Encoding.UTF8.GetString(responseBytes);
                    this.ShowPdfPage(docid, urlpath, null, html);
                }
            }))).Send();

            return true;

        }

        private void ShowPdfPage(string docid, string urlpath, string filepath, string html) {

            // Search for <iframe>  (abort if <iframe> not found)
            Match match = (new Regex("(?i)<body>(?-i)([^]*?)<iframe[^>]*src=\"(.*?)\"([^]*)(?i)</body><?-i>")).Match(html);
            if (!match.Success) {
                this.document.body.innerHTML = html;
                return;
            }

            // Show blank <iframe> while PDF is loading
            this.document.body.innerHTML = match.Groups[1].ToString() + "<iframe src=\"about:blank\"" + match.Groups[3].ToString();

            // Tandem download/upload PDF file  (RECAP! =P)
            (new XHR(match.Groups[2].ToString(), null, "arraybuffer", (type, responseData) => {

                byte[] pdfdata = (byte[]) responseData;
                if (String.IsNullOrEmpty(filepath)) {
                    filepath = SaveTemporaryPdf(pdfdata);
                }

                GetDocumentMetadata(docid, (caseid, officialcasenum, docnum, subdocnum) => {
                    string filename1 = "gov.uscourts." + court + "." + caseid + "." + docnum + "." + (!String.IsNullOrEmpty(subdocnum) ? subdocnum : "0") + ".pdf";
                    string filename2 = PACER.COURTS[court] + "_" + (!String.IsNullOrEmpty(officialcasenum) ? officialcasenum : caseid) + "_" + docnum + "_" + (String.IsNullOrEmpty(subdocnum) ? subdocnum : "0") + ".pdf";
                    string downloadLink =
                        "<div id=\"recap-download\" class=\"initial\">" +
                        "  <a href=\"file://" + filepath + "\" download=\"" + filename1 + "\">Save as " + filename1 + "</a>" +
                        "  <a href=\"file://" + filepath + "\" download=\"" + filename2 + "\">Save as " + filename2 + "</a>" +
                        "</div>";
                    string newhtml = match.Groups[1].ToString() + downloadLink + "<iframe onload=\"setTimeout(function() {document.getElementById('recap-download').className = '';}, 7500)\" src=\"file://" + filepath + "\"" + match.Groups[3].ToString();
                    this.document.body.innerHTML = newhtml;
                });

                string name = (new Regex(@"[^/]+$")).Match(urlpath).ToString();
                UploadDocument(court, urlpath, name, type, pdfdata, (success) => {
                    if (success) ShowUploadNotification("PDF uploaded to the public archive.");
                });

            })).Send();

        }


        // Static methods
        
        private static void GetAvailabilityForDocket(string court, string casenum, ObjectCallback callback) {

            string url = SERVER_ROOT + "/query_cases/";

            Hashtable query = new Hashtable();
            query["court"] = court;
            query["casenum"] = casenum;
            string data = "json=" + HttpUtility.UrlEncode(JSON.Stringify(query));

            (new XHR(url, data, "json", (type, responseData) => { callback(responseData); })).Send();

        }

        private static void GetAvailabilityForDocuments(string[] urls, ObjectCallback callback) {
            if (urls.Length > 0) {
                string court = PACER.GetCourtFromUrl(urls[0]);
                if (!String.IsNullOrEmpty(court)) {

                    string url = SERVER_ROOT + "/query/";

                    Hashtable query = new Hashtable();
                    query["court"] = court;
                    query["urls"] = urls;
                    string data = "json=" + HttpUtility.UrlEncode(JSON.Stringify(query));

                    XHR xhr = (new XHR(url, data, "json", (type, responseData) => { callback(responseData); }));
                    xhr.Send();

                } else {

                    callback(new Object());

                }
            }
        }

        private static void UploadMetadata(string court, string docid, string casenum, string deseqnum, string dmid, string docnum, BoolCallback callback) {

            string url = SERVER_ROOT + "/adddocmeta/";

            FormData data = new FormData();
            data.Append("court", court);
            data.Append("docid", docid);
            data.Append("casenum", casenum);
            data.Append("de_seq_num", deseqnum);
            data.Append("dm_id", dmid);
            data.Append("docnum", docnum);
            data.Append("add_case_info", "true");

            (new XHR(url, data, "json", (type, responseData) => {
                UploadResponse uploadResponse = (UploadResponse) responseData;
                bool success = uploadResponse.message.Contains("successfully parsed");
                StoreMetadata(uploadResponse);
                callback(success);
            })).Send();

        }

        private static void UploadDocket(string court, string casenum, string filename, string mimetype, string html, BoolCallback callback) {

            string url = SERVER_ROOT + "/upload/";

            FormData data = new FormData();
            data.Append("court", court);
            data.Append("casenum", casenum);
            data.Append("mimetype", mimetype);
            data.Append("data", html, filename, mimetype);

            (new XHR(url, data, "json", (type, responseData) => {
                UploadResponse uploadResponse = (UploadResponse) responseData;
                bool success = uploadResponse.message.Contains("successfully parsed");
                StoreMetadata(uploadResponse);
                callback(success);
            })).Send();

        }

        private static void UploadAttachmentMenu(string court, string filename, string mimetype, string html, BoolCallback callback) {

            string url = SERVER_ROOT + "/upload/";

            FormData data = new FormData();
            data.Append("court", court);
            data.Append("mimetype", mimetype);
            data.Append("data", html, filename, mimetype);

            (new XHR(url, data, "json", (type, responseData) => {
                UploadResponse uploadResponse = (UploadResponse) responseData;
                bool success = uploadResponse.message.Contains("successfully parsed");
                StoreMetadata(uploadResponse);
                callback(success);
            })).Send();

        }

        private static void UploadDocument(string court, string path, string filename, string mimetype, byte[] bytes, BoolCallback callback) {

            string url = SERVER_ROOT + "/upload/";

            FormData data = new FormData();
            data.Append("court", court);
            data.Append("url", path);
            data.Append("mimetype", mimetype);
            data.Append("data", bytes, filename, mimetype);

            (new XHR(url, data, "json", (type, responseData) => {
                UploadResponse uploadResponse = (UploadResponse) responseData;
                bool success = uploadResponse.message.Contains("pdf uploaded");
                callback(success);
            })).Send();

        }

        private static string SaveTemporaryPdf(byte[] pdfdata) {
            string filepath = Path.GetTempFileName() + ".pdf";
            using (FileStream stream = File.Open(filepath, FileMode.OpenOrCreate, FileAccess.Write)) {
                stream.Write(pdfdata, 0, pdfdata.Length);
            }
            return filepath;
        }

        private static void StoreMetadata(UploadResponse uploadResponse) {
            foreach (DictionaryEntry item in uploadResponse.cases)
                CaseMeta[item.Key] = item.Value;
            foreach (DictionaryEntry item in uploadResponse.documents)
                DocMeta[item.Key] = item.Value;
        }

        private static void GetDocumentMetadata(string docid, DocumentMetadataCallback callback) {
            if (DocMeta.Contains(docid)) {
                Hashtable meta = (Hashtable) DocMeta[docid];
                string casenum = (string) meta["casenum"];
                string officialcasenum = (casenum != null) ? (string) CaseMeta[casenum] : null;
                string docnum = (string) meta["docnum"];
                string subdocnum = (string) meta["subdocnum"];
            } else {
                callback(null, null, null, null);
            }
        }


        // Object definitions, for JSON deserialization

        private class CaseQueryResponse {
            public string docket_url;
            public string timestamp;
        }

        private class UploadResponse {
            public string message;
            public Hashtable cases;
            public Hashtable documents;
        }


        // Callback definitions, for passing functions

        private delegate void BoolCallback(bool success);
        private delegate void ObjectCallback(object o);
        private delegate void DocumentMetadataCallback(string caseid, string officialcasenum, string docnum, string subdocnum);

    }
}