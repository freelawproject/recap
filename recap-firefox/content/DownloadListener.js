function DownloadListener(URIhost, filename, mimeType) {
    this.URIhost = URIhost;
    this.filename = filename;
    this.mimeType = mimeType;
}

DownloadListener.prototype = {

    boundary: "-------recap-multipart-boundary-" + (new Date().getTime()),

    appendPrefixStream: function() {

	var prefixStream = CCIN("@mozilla.org/io/string-input-stream;1",
				"nsIStringInputStream");

	var formData = [];
	formData.push("--" + this.boundary);
	formData.push("Content-Disposition: form-data; name=\"data\"; " +
			"filename=\"" + this.filename + "\"");
	formData.push("Content-Type: " + this.mimeType);
	formData.push("");
	formData.push("");
	formString = formData.join("\r\n");
	
	prefixStream.setData(formString, formString.length);

	this.multiplexStream.appendStream(prefixStream);
    },

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

    postFile: function() {

	var req = CCIN("@mozilla.org/xmlextras/xmlhttprequest;1",
			"nsIXMLHttpRequest");

	req.open("POST", "http://tails.princeton.edu/recapsite/doupload/", true);
	 
	req.setRequestHeader("Content-Type", 
			     "multipart/form-data; boundary=" + 
			     this.boundary);
	req.setRequestHeader("Content-Length", 
			     this.multiplexStream.available());
	
	log(this.URIhost + " " + this.filename + " " + 
	    this.mimeType + " " + this.multiplexStream.available() + " " + 
	    this.multiplexStream.count);
	
	req.onreadystatechange = function() {
	    //log(req.readyState);
	    if (req.readyState == 4) {
		log(req.responseText);
	    }
	};
	
	req.send(this.multiplexStream);
	 
    },
    
    originalListener: null,
    
    multiplexStream: CCIN("@mozilla.org/io/multiplex-input-stream;1",
			  "nsIMultiplexInputStream"),
    
    receivedData: [],    
    
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

        // Copy received data as they come.
        var data = binaryInputStream.readBytes(count);

	// this.receivedData.push(data);
	//log("got some data");
	
	// Store data in the storageStream
        binaryOutputStream.writeBytes(data, count);
	binaryOutputStream.close();
	
	this.multiplexStream.appendStream(storageStream.newInputStream(0));

        this.originalListener.onDataAvailable(request, 
					      context,
					      storageStream.newInputStream(0), 
					      offset, 
					      count);
    },
    
    onStartRequest: function(request, context) {
	// this.receivedData = [];
	this.multiplexStream = CCIN("@mozilla.org/io/multiplex-input-stream;1",
				    "nsIMultiplexInputStream");
	this.appendPrefixStream();
	
        this.originalListener.onStartRequest(request, context);
    },

    onStopRequest: function(request, context, statusCode)
    {
        // Get entire response
        //var responseSource = this.receivedData.join();

	this.appendSuffixStream();
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
