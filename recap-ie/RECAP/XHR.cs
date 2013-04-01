// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// ------------------
// Convenience class for sending asynchronous HTTP requests.
//
// Usage:
//
//     string url = "http://www.bing.com/";
//     string postData = null;
//     string responseType = "text";
//     XHR.Callback callback = (type, responseData) => {
//         Console.Write(responseData);
//     };
//     (new XHR(url, postData, responseType, callback)).Send();
//
// Parameters:
//
// * url -- (string)
//
// * postData -- (string or null)
//
//   If `postData` not null, the request will be sent as a POST request 
//   instead of a GET request, with `postData` included in the POST request.
//
// * responseType -- (string)
//
//   If `responseType` is "text" or "json", the response data will be passed
//   to the callback function as a string. Otherwise, the response data will
//   be passed to the callback function as a byte array (i.e., byte[]).
//
// * callback -- (XHR.Callback)
//
//   `callback` is a function that takes two arguments: (1) the response `type`
//   as a string; (2) the `responseData` as a string or byte array. The
//   callback function will be called upon a successful ("200 OK") request.

using System;
using System.IO;
using System.Net;
using System.Text;

namespace RECAP {
    public class XHR {

        private HttpWebRequest request;
        private HttpWebResponse response;
        private HttpWebCallback callback;

        public delegate void Callback(string type, object responseData);
        private delegate void HttpWebCallback(IAsyncResult result);

        public XHR(string url, object postData, string responseType, Callback customCallback) {

            // Prepare request
            this.request = (HttpWebRequest) WebRequest.Create(url);
            if (postData.GetType() == typeof(FormData)) {
                // POST request (multipart/form-data)
                request.Method = "POST";
                request.ContentType = "multipart/form-data";
                // POST data as UTF8 bytes
                Stream postStream = request.GetRequestStream();
                ((FormData) postData).Write(postStream);
                postStream.Close();
            } else if (!String.IsNullOrEmpty((string) postData)) {
                // POST request (application/x-www-form-urlencoded)
                request.Method = "POST";
                request.ContentType = "application/x-www-form-urlencoded";
                // POST data as UTF8 bytes
                Stream postStream = request.GetRequestStream();
                byte[] postBytes = Encoding.UTF8.GetBytes((string) postData);
                postStream.Write(postBytes, 0, postBytes.Length);
                postStream.Close();
            } else {
                // GET response
                request.Method = "GET";
            }

            // Prepare callback
            this.callback = (result) => {
                this.response = (HttpWebResponse) this.request.EndGetResponse(result);
                if (this.response.StatusCode == HttpStatusCode.OK) {
                    // Get response data
                    Stream responseStream = this.response.GetResponseStream();
                    byte[] responseBytes = new byte[responseStream.Length];
                    responseStream.Read(responseBytes, 0, (int) responseStream.Length);
                    // Execute callback
                    if (responseType == "text") {
                        string responseData = Encoding.UTF8.GetString(responseBytes);
                        customCallback(this.response.ContentType, responseData);
                    } else if (responseType == "json") {
                        try {
                            object responseData = JSON.Parse(Encoding.UTF8.GetString(responseBytes));
                            customCallback(this.response.ContentType, responseData);
                        } catch {
                            string responseData = Encoding.UTF8.GetString(responseBytes);
                            customCallback(this.response.ContentType, responseData);
                        }
                    } else {
                        byte[] responseData = responseBytes;
                        customCallback(this.response.ContentType, responseData);
                    }
                }
            };

        }

        public void Send() {
            this.request.BeginGetResponse(new AsyncCallback(this.callback), null);
        }

    }
}