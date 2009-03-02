
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

function DownloadListener(filemeta) {
    // metadata for the expected file, which has the following properties:
    //    filemeta.name ('1234567890.pdf')
    //    filemeta.path ('/doc1/')
    //    filemeta.court ('cacd')
    //    filemeta.mimeType ('application/pdf')

    this.filemeta = filemeta;
}

DownloadListener.prototype = {

    // Arbitrary multipart form separator
    boundary: "-------recap-multipart-boundary-" + (new Date().getTime()),

    // Appends the prefix for the multipart input form
    appendPrefixStream: function() {

	var prefixStream = CCIN("@mozilla.org/io/string-input-stream;1",
				"nsIStringInputStream");

	var formData = [];
	formData.push("--" + this.boundary);
	formData.push("Content-Disposition: form-data; name=\"data\"; " +
			"filename=\"" + this.filemeta.name + "\"");
	formData.push("Content-Type: " + this.filemeta.mimeType);
	formData.push("");
	formData.push("");
	formString = formData.join("\r\n");
	
	prefixStream.setData(formString, formString.length);

	this.multiplexStream.appendStream(prefixStream);
    },

    // Appends the suffix for the multipart input form
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
	
	req.open("POST", 
		 "http://monocle.princeton.edu/recap/doupload/", 
		 true);
	
	req.setRequestHeader("Content-Type", 
			     "multipart/form-data; boundary=" + 
			     this.boundary);
	req.setRequestHeader("Content-Length", 
			     this.multiplexStream.available());
	
	log("Court: " + this.filemeta.court + 
	    "; Path: " + this.filemeta.path +
	    "; Name: " + this.filemeta.name +
	    "; MimeType: " + this.filemeta.mimeType +
	    "; StreamBytes: " + this.multiplexStream.available());
	
	req.onreadystatechange = function() {
	    if (req.readyState == 4) {
		log(req.responseText);
	    }
	};
	
	req.send(this.multiplexStream);
	 
    },
    
    originalListener: null,
    
    // The buffer stream
    multiplexStream: CCIN("@mozilla.org/io/multiplex-input-stream;1",
			  "nsIMultiplexInputStream"),
    
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

	// add the form prefix data before any content arrives
	this.appendPrefixStream();
	
        this.originalListener.onStartRequest(request, context);
    },

    // Called when the HTTP request is ending
    onStopRequest: function(request, context, statusCode)
    {

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
