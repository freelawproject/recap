// This file is part of RECAP for Chrome.
// Copyright 2013 Ka-Ping Yee <ping@zesty.ca>
//
// RECAP for Chrome is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option)
// any later version.  RECAP for Chrome is distributed in the hope that it will
// be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
// Public License for more details.
// 
// You should have received a copy of the GNU General Public License along with
// RECAP for Chrome.  If not, see: http://www.gnu.org/licenses/

// -------------------------------------------------------------------------
// Browser-specific utilities for use in background pages and content scripts.


// In Chrome, content scripts can only communicate with background pages using
// message passing (see http://developer.chrome.com/extensions/messaging.html).
// Sometimes the content script needs to call into a background page in order
// to persist data from page to page or to use certain permissions, so for
// convenience we wrap the message-passing machinery using a pair of functions,
// exportInstance() and importInstance().  Here's how to use them:
//
// 1. Write a service by defining a no-argument constructor function.  The
//    name of the function identifies the service.  The function should return
//    an object whose methods all take a callback (cb) as the last argument and
//    call the callback with the return value (rv).  All arguments and return
//    values must be JSON-serializable.  The caller's tab is provided as cb.tab.
//
// 2. Include the service in both the background page and the content script
//    (i.e. in manifest.json, the service's JS file should appear in both the
//    background: {scripts: [...]} and content_scripts: {js: [...]} lists).
//
// 3. In the background page, call exportInstance on the constructor).  This
//    creates a instance that will serve requests from the content script.
//    Only one singleton instance can be exported.
//
// 4. In the content script, call importInstance on the same constructor to get
//    an object.  Then call methods on the object, always passing a callback
//    function or null as the last argument.
//
// Here's an example.
//
// Service definition:
//   function Counter() {
//     var count = 0;
//     return {inc: function (amount, cb) { cb(count += amount); }};
//   }
//
// In the background page:
//   exportInstance(Counter);
//
// In the content script:
//   var counter = importInstance(Counter);
//   counter.inc(6, function (rv) { alert('count is ' + rv); });


//TODO: Pretty sure this is not needed at all for Forge. This is legacy from
//the Chrome extension code and keeping it here till we have a test plan to
//confirm this is not needed. -- devd

// Makes a singleton instance in a background page callable from a content
// script, using Chrome's message system.  See above for details.
function exportInstance(Constructor) {
  var name = Constructor.name, // function name identifies the service
      instance = new Constructor(),
      pack;
  forge.message.listen(function(msg,cb){
    if (msg.name === name) {
      pack = function () { cb(Array.prototype.slice.apply(arguments)); };
      //pack.tab = sender.tab;
      //instance[msg.verb].apply(instance, request.args.concat([pack]));
      return true;  // allow cb to be called after listener returns
    }
  });
}

// Gets an object that can be used in a content script to invoke methods on an
// instance exported from the background page.  See above for details.  
function importInstance(constructor) {
  var name = constructor.name;
  var sender = {};
  var verb;
  for (verb in new constructor()) {
    (function (verb) {
      sender[verb] = function () {
        var args = Array.prototype.slice.call(arguments, 0, -1);
        var cb = arguments[arguments.length - 1] || function () {};
        if (typeof cb !== 'function') {
          throw 'Service invocation error: last argument is not a callback';
        }
        var unpack = function (results) { cb.apply(null, results); };
        forge.message.broadcast("instance",
          {name: name, verb: verb, args: args}, unpack, function(content){forge.logging.debug(content);});
      };
    })(verb);
  }
  return sender;
}

// Makes an XHR to the given URL, calling a callback with the returned content
// type and response (interpreted according to responseType).  See XHR2 spec
// for details on responseType and response.  Uses GET if postData is null or
// POST otherwise.  postData can be any type accepted by XMLHttpRequest.send().
function httpRequest(url, postData, responseType, callback) {
  forge.request.ajax({
    'type': postData === null ? 'GET' : 'POST',
  'url': url,
  'data': postData,
  'dataType': responseType,
  'success': function(data) {
    forge.logging.debug(data);
    if (callback) {
      callback(responseType, data);
    }
  },
  'error': function(error) {
    forge.logging.debug("ERRORRRRR in httpRequest");
    forge.logging.debug([url,postData,responseType,callback]);
    forge.logging.debug(error);
  }
  });
}
/*function httpRequest(url, postData, responseType, callback) {
  var type = null;
  var result = null;
  var xhr = new XMLHttpRequest();
  // WebKit doesn't support responseType 'json' yet, but probably will soon.
  xhr.responseType = responseType === 'json' ? 'text' : responseType;
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        type = xhr.getResponseHeader('Content-Type');
        result = xhr.response;
        if (responseType === 'json') {
          try {
            result = JSON.parse(result);
          } catch (e) { }
        }
      }
      callback && callback(type, result);
    }
  };
  xhr.open(postData === null ? 'GET' : 'POST', url);
  xhr.send(postData);
}*/

// Converts an ArrayBuffer to a regular array of unsigned bytes.  Array.apply()
// causes a "maximum call stack size exceeded" error for buffers of only 300k,
// so we need this ridiculous circumlocution of breaking the data into chunks.
function arrayBufferToArray(ab) {
  var chunks = [];
  var i;
  for (i = 0; i < ab.byteLength; i += 100000) {
    var slice = new Uint8Array(ab, i, Math.min(100000, ab.byteLength - i));
    chunks.push(Array.apply(null, slice));  // convert each chunk separately
  }
  return [].concat.apply([], chunks);  // concatenate all the chunks together
}

/* John Resig's addEventListener Hack */
function addEvent( obj, type, fn ) {
  if ( obj.attachEvent ) {
    obj['e'+type+fn] = fn;
    obj[type+fn] = function(){obj['e'+type+fn]( window.event );}
    obj.attachEvent( 'on'+type, obj[type+fn] );
  } else
    obj.addEventListener( type, fn, false );
}
function removeEvent( obj, type, fn ) {
  if ( obj.detachEvent ) {
    obj.detachEvent( 'on'+type, obj[type+fn] );
    obj[type+fn] = null;
  } else
    obj.removeEventListener( type, fn, false );
}
