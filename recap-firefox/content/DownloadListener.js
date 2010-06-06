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

/** DownloadListener: 
 *    implements nsIStreamListener 
 *
 *    Listens for HTTP data and pipes the stream directly to a server using
 *      an AJAX POST input form request, then forwards the stream on to the
 *      original listener.
 *
 *    This should be registered as a listener to an nsITraceableChannel
 *      (only available for Firefox 3.0.4 or later).
 *
*/

function DownloadListener(filemeta, metacache) {
    // metadata for a PDF file, should have the following properties:
    //    filemeta.mimetype ('application/pdf')
    //    filemeta.court ('cacd')
    //    filemeta.name ('1234567890.pdf')
    //    filemeta.url ('/doc1/1234567890')

    
    // metadata for an .pl HTML file, should have the following properties:
    //    filemeta.mimetype
    //    filemeta.court
    //    filemeta.name
    //    filemeta.casenum


    // metadata for a /doc1/ HTML file, should have the following properties:
    //    filemeta.mimetype
    //    filemeta.court
    //    filemeta.name

    this.filemeta = filemeta;
    
    // cache of document and case metadata from Recap namespace
    this.metacache = metacache;
}

DownloadListener.prototype = {

    // Arbitrary multipart POST separator
    boundary: "-------recap-multipart-boundary-" + (new Date().getTime()),

    // Appends the prefix to the multipart POST
    appendPrefixStream: function() {

	var prefixStream = CCIN("@mozilla.org/io/string-input-stream;1",
				"nsIStringInputStream");

	var formData = [];
	formData.push("--" + this.boundary);
	formData.push("Content-Disposition: form-data; name=\"data\"; " +
			"filename=\"" + this.filemeta.name + "\"");
	formData.push("Content-Type: " + this.filemeta.mimetype);
	formData.push("");
	formData.push("");
	formString = formData.join("\r\n");
	
	prefixStream.setData(formString, formString.length);

	this.multiplexStream.appendStream(prefixStream);
    },

    // Appends the file metadeta to the multipart POST
    appendFilemetaStream: function() {
	
	var filemetaStream = CCIN("@mozilla.org/io/string-input-stream;1",
				  "nsIStringInputStream");

	var formData = [];
	formData.push("");

	for (fieldname in this.filemeta) {
	    if (fieldname == "name") continue;

	    formData.push("--" + this.boundary);
	    formData.push("Content-Disposition: form-data; name=\"" 
			  + fieldname + "\"");
	    formData.push("");
	    formData.push(this.filemeta[fieldname]);
	}

	formString = formData.join("\r\n");
	
	filemetaStream.setData(formString, formString.length);

	this.multiplexStream.appendStream(filemetaStream);
    },

    // Appends the suffix to the multipart POST
    appendSuffixStream: function() {

	var suffixStream = CCIN("@mozilla.org/io/string-input-stream;1",
				"nsIStringInputStream");

	var formData = [];
	formData.push("");
	formData.push("--" +  this.boundary + "--");
	formData.push("");
	formString = formData.join("\r\n");
	
	suffixStream.setData(formString, formString.length);

	this.multiplexStream.appendStream(suffixStream);
    },

    // Posts the file to the server directly using the data stream
    postFile: function() {

	var req = CCIN("@mozilla.org/xmlextras/xmlhttprequest;1",
		       "nsIXMLHttpRequest");
	
	req.open("POST", UPLOAD_URL, true);
	
	req.setRequestHeader("Content-Type", 
			     "multipart/form-data; boundary=" + 
			     this.boundary);
	req.setRequestHeader("Content-Length", 
			     this.multiplexStream.available());
	
	log("Posting file: " + this.filemeta.name);
	
	var that = this;
	req.onreadystatechange = function() {
	    
	    if (req.readyState == 4 && req.status == 200) {
		var message;
		message = that.handleResponse(req) || req.responseText;
	    }
	    
	};
	
	req.send(this.multiplexStream);
	 
    },

    handleResponse: function(req) {
    	
	// handle json object and update metadata cache
	var nativeJSON = CCIN("@mozilla.org/dom/json;1", "nsIJSON");
	try {
	    var jsonin = nativeJSON.decode(req.responseText);
	} catch (e) {
	    return "JSON decoding failed. (req.responseText: " + req.responseText + ")";
	}
	
	if (jsonin && typeof(jsonin.error) == "undefined") {
	    
	    if (isPDF(this.filemeta.mimetype)) {
		// PDF upload notification
		
		showAlert(ICON_LOGGED_IN_32, 
			  "Recap File Upload", 
			  "PDF uploaded to the public archive.");
		
	    } else if (isHTML(this.filemeta.mimetype)) {
		
		showAlert(ICON_LOGGED_IN_32, 
			  "Recap File Upload", 
			  "Docket uploaded to the public archive.");  
		

		updateMetaCache(this.metacache,jsonin.documents, jsonin.cases);

		return jsonin.message;
	    }
	}
	return jsonin;
	
    },
    
    originalListener: null,
    
    // The buffer stream
    multiplexStream : null, 
    
    // Called when data is arriving on the HTTP channel
    onDataAvailable: function(request, context, inputStream, offset, count) {
        var binaryInputStream = CCIN("@mozilla.org/binaryinputstream;1",
				     "nsIBinaryInputStream");
        var storageStream = CCIN("@mozilla.org/storagestream;1", 
				 "nsIStorageStream");
        var binaryOutputStream = CCIN("@mozilla.org/binaryoutputstream;1",
				      "nsIBinaryOutputStream");

        binaryInputStream.setInputStream(inputStream);
        storageStream.init(4096, count, null);
        binaryOutputStream.setOutputStream(storageStream.getOutputStream(0));

        // Copy received data as they come
        var data = binaryInputStream.readBytes(count);

	// Store data in the storageStream
        binaryOutputStream.writeBytes(data, count);
	binaryOutputStream.close();
	
	// Add this data chunk to the buffer stream
	this.multiplexStream.appendStream(storageStream.newInputStream(0));

	// Forward the data to the original listener
        this.originalListener.onDataAvailable(request, 
					      context,
					      storageStream.newInputStream(0), 
					      offset, 
					      count);
    },
    
    // Called when the HTTP request is beginning
    onStartRequest: function(request, context) {
	//initialize this here so that it is not shared by other instances of DownloadListener
        this.multiplexStream = CCIN("@mozilla.org/io/multiplex-input-stream;1",
			  "nsIMultiplexInputStream");

	// add the form prefix data before any content arrives
	this.appendPrefixStream();
	
        this.originalListener.onStartRequest(request, context);
    },

    // Called when the HTTP request is ending
    onStopRequest: function(request, context, statusCode)
    {

	// add other file metadata to the stream
	this.appendFilemetaStream();
	// add the form suffix data after all the content arrives
	this.appendSuffixStream();
	// POST the file to the server
	this.postFile();

        this.originalListener.onStopRequest(request, context, statusCode);
    },
    
    QueryInterface: function (aIID) {
        if (aIID.equals(Ci.nsIStreamListener) ||
            aIID.equals(Ci.nsISupports)) {
            return this;
        }
        throw Components.results.NS_NOINTERFACE;
    }
};

