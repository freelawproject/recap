
/** DocLinkListener: 
 *    implements nsIStreamListener 
 *
 *    Listens for HTTP data and pipes some data from the stream to a
 *      server using an AJAX GET request, then forwards the stream on to the
 *      original listener.
 *
 *    This should be registered as a listener to an nsITraceableChannel
 *      (only available for Firefox 3.0.4 or later).
 *
*/

function DocLinkListener(court, URIpath) {
    
    this.responsetext = "";
    this.court = court;
    this.URIpath = URIpath;
    
}

DocLinkListener.prototype = {

    // Posts the file to the server directly using the data stream
    postFile: function() {

	var req = CCIN("@mozilla.org/xmlextras/xmlhttprequest;1",
		       "nsIXMLHttpRequest");
	
	var args;
	
	try {
		args = this.URIpath.split("?")[1];
		casenum = this.getQueryVariable("caseid",args);
		de_seq_num = this.getQueryVariable("de_seq_num",args);
		dm_id = this.getQueryVariable("dm_id",args);
		docnum = this.getQueryVariable("doc_num",args);
		docid = this.responsetext.match(/\d*$/);
	} catch (e) {
		log("didn't all necessary args to build addocmeta query: " + this.responsetext + this.URIpath);
		return;
	}
	
	req.open("GET", 
		 SERVER_URL + "adddocmeta/?docid=" + docid + "&casenum=" + casenum + "&de_seq_num=" + de_seq_num + "&dm_id=" + dm_id + "&docnum=" + docnum + "&court=" + this.court, 
		 true);
		

	
	var that = this;
	req.onreadystatechange = function() {
	    if (req.readyState == 4 && req.status == 200) {
	    	var message;
			message = req.responseText;
			log("did adddocmeta for docid " + docid + "  response: " + message);
	    }	    
	};	
	
	req.send("");
	 
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
        if (data) {
	        this.responsetext = this.responsetext + data;
		}
		
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
        this.originalListener.onStartRequest(request, context);
    },

    // Called when the HTTP request is ending
    onStopRequest: function(request, context, statusCode)
    {
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
    },
    
    getQueryVariable: function(variable,querytext) {
		var vars = querytext.split("K");
		for (var i=0;i<vars.length;i++) {
			var pair = vars[i].split("V");
			if (pair[0] == variable) {
				return pair[1];
			}
		} 
	}
};
