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
// Content script to run when DOM finishes loading (run_at: "document_end").

var IMGDATAURI={
"grey-16.png":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAACXBIWXMAAAsTAAALEwEAmpwYAAADGGlDQ1BQaG90b3Nob3AgSUNDIHByb2ZpbGUAAHjaY2BgnuDo4uTKJMDAUFBUUuQe5BgZERmlwH6egY2BmYGBgYGBITG5uMAxIMCHgYGBIS8/L5UBFTAyMHy7xsDIwMDAcFnX0cXJlYE0wJpcUFTCwMBwgIGBwSgltTiZgYHhCwMDQ3p5SUEJAwNjDAMDg0hSdkEJAwNjAQMDg0h2SJAzAwNjCwMDE09JakUJAwMDg3N+QWVRZnpGiYKhpaWlgmNKflKqQnBlcUlqbrGCZ15yflFBflFiSWoKAwMD1A4GBgYGXpf8EgX3xMw8BSMDVQYqg4jIKAUICxE+CDEESC4tKoMHJQODAIMCgwGDA0MAQyJDPcMChqMMbxjFGV0YSxlXMN5jEmMKYprAdIFZmDmSeSHzGxZLlg6WW6x6rK2s99gs2aaxfWMPZ9/NocTRxfGFM5HzApcj1xZuTe4FPFI8U3mFeCfxCfNN45fhXyygI7BD0FXwilCq0A/hXhEVkb2i4aJfxCaJG4lfkaiQlJM8JpUvLS19QqZMVl32llyfvIv8H4WtioVKekpvldeqFKiaqP5UO6jepRGqqaT5QeuA9iSdVF0rPUG9V/pHDBYY1hrFGNuayJsym740u2C+02KJ5QSrOutcmzjbQDtXe2sHY0cdJzVnJRcFV3k3BXdlD3VPXS8Tbxsfd99gvwT//ID6wIlBS4N3hVwMfRnOFCEXaRUVEV0RMzN2T9yDBLZE3aSw5IaUNak30zkyLDIzs+ZmX8xlz7PPryjYVPiuWLskq3RV2ZsK/cqSql01jLVedVPrHzbqNdU0n22VaytsP9op3VXUfbpXta+x/+5Em0mzJ/+dGj/t8AyNmf2zvs9JmHt6vvmCpYtEFrcu+bYsc/m9lSGrTq9xWbtvveWGbZtMNm/ZarJt+w6rnft3u+45uy9s/4ODOYd+Hmk/Jn58xUnrU+fOJJ/9dX7SRe1LR68kXv13fc5Nm1t379TfU75/4mHeY7En+59lvhB5efB1/lv5dxc+NH0y/fzq64Lv4T8Ffp360/rP8f9/AA0ADzT6lvFdAAAAIGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAE2SURBVHjaZNA/a1RREIfhZ885V1eU5CIoiBBTC4qFxUJAiJV1mvSCQrr9BpLKSt1voKC29trY2FgIdoKVpomwJFlDLLJ7zz0W97qCzsAUM+/85s/gXr32KI2zsPTYR6aTvd149/FwXGskSVK54JpGcNY5V0enw8FOObLuja+4Y83UW7dsOSPiWGhF+7bBhis2jHz2VI0iCANJUoMgaWxi5kBRFClIktgDUVLprGgVoUvGpULlB2oXFVn7r8J5vLbugZ/y/8AXQy/wxFSWNVohqJbADTfBK5VsYSEL3dzUL5bdx3snGs1f4I8CxW01nkvm5h1QSY77cjGzg28+iE7l7lGrXvazg2zFNt75JGLw8Nn1cWXW96841JhbdaRx2fdJvPRxPjRq+7N+WchaJxZah5O93d8DAEwiaNIZh8qpAAAAAElFTkSuQmCC",
"grey-32.png":"data:image/png;base64,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",
"icon-16.png":"data:image/png;base64,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",
"icon-32.png":"data:image/png;base64,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",
"warning-16.png":"data:image/png;base64,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",
"warning-32.png":"data:image/png;base64,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"
};
//TODO: Add notifier support
//var notifier = importInstance(Notifier);
//var toolbar_button = importInstance(ToolbarButton);
//var pacer = importInstance(Pacer);
//var recap = importInstance(Recap);
var pacer = Pacer();
var recap = Recap();

var url = window.location.href;
var court = PACER.getCourtFromUrl(url);

// Update the toolbar button with knowledge of whether the user is logged in.
// TODO: add notifier support
// toolbar_button.updateCookieStatus(court, document.cookie, null);

// If this is a docket query page, ask RECAP whether it has the docket page.
if (PACER.isDocketQueryUrl(url)) {
  forge.logging.debug("IsDocketQuery succeeded");
  recap.getAvailabilityForDocket(
    court, PACER.getCaseNumberFromUrl(url), function (result) {
    if (result && result.docket_url) {
      // Insert a RECAP download link at the bottom of the form.
      forge.logging.debug("Insert a RECAP download link at the bottom of the form.");
      $('<div class="recap-banner"/>').append(
        $('<a/>', {
          title: 'Docket is available for free from RECAP.',
          href: result.docket_url
        }).append(
          $('<img/>', {src: IMGDATAURI['icon-16.png']})
        ).append(
          ' Get this docket as of ' + result.timestamp + ' for free from RECAP.'
        )
      ).append(
        $('<br><small>Note that archived dockets may be out of date.</small>')
      ).appendTo($('form'));
    }
  });
}
/* TODO: Uncomment this and add support
if (!(history.state && history.state.uploaded)) {
  // If this is a docket page, upload it to RECAP.
  if (PACER.isDocketDisplayUrl(url)) {
    var casenum = PACER.getCaseNumberFromUrl(document.referrer);
    if (casenum) {
      var filename = PACER.getBaseNameFromUrl(url).replace('.pl', '.html');
      recap.uploadDocket(court, casenum, filename, 'text/html',
                         document.documentElement.innerHTML, function (ok) {
        if (ok) {
          history.replaceState({uploaded: 1});
          //TODO: add notifier support
          //notifier.showUpload('Docket uploaded to the public archive.', null);
        }
      });
    }
  }
  
  // If this is a document's menu of attachments, upload it to RECAP.
  if (PACER.isAttachmentMenuPage(url, document)) {
    recap.uploadAttachmentMenu(
      court, window.location.pathname, 'text/html',
      document.documentElement.innerHTML, function (ok) {
      if (ok) {
        history.replaceState({uploaded: 1});
        //TODO: add notifier support
        //notifier.showUpload('Menu page uploaded to the public archive.', null);
      }
    });
  }
}*/

// If this page offers a single document, ask RECAP whether it has the document.
if (PACER.isSingleDocumentPage(url, document)) {
  recap.getAvailabilityForDocuments([url], function (result) {
    if (result && result[url]) {
      // Insert a RECAP download link at the bottom of the form.
      $('<div class="recap-banner"/>').append(
        $('<a/>', {
          title: 'Document is available for free from RECAP.',
          href: result[url].filename
        }).append(
          $('<img/>', {src: IMGDATAURI['icon-16.png']})
        ).append(
          ' Get this document for free from RECAP.'
        )
      ).appendTo($('form'));
    }
  });
}

/*TODO: Uncomment this and add support
// If this page offers a single document, intercept navigation to the document
// view page.  The "View Document" button calls the goDLS() function, which
// creates a <form> element and calls submit() on it, so we hook into submit().
if (PACER.isSingleDocumentPage(url, document)) {
  // Monkey-patch the <form> prototype so that its submit() method sends a
  // message to this content script instead of submitting the form.  To do this
  // in the page context instead of this script's, we inject a <script> element.
  var script = document.createElement('script');
  script.innerText =
      'document.createElement("form").__proto__.submit = function () {' +
      '  this.id = "form" + new Date().getTime();' +
      '  window.postMessage({id: this.id}, "*");' +
      '};';
  document.body.appendChild(script);
  // TODO this will probably not work because postMessage might be off in IE

  // When we receive the message from the above submit method, submit the form
  // via XHR so we can get the document before the browser does.
  addEvent(window,'message', function (event) {
    // Save a copy of the page source, altered so that the "View Document"
    // button goes forward in the history instead of resubmitting the form.
    var originalSubmit = document.forms[0].getAttribute('onsubmit');
    document.forms[0].setAttribute('onsubmit', 'history.forward(); return !1;');
    var previousPageHtml = document.documentElement.innerHTML;
    document.forms[0].setAttribute('onsubmit', originalSubmit);
    var docid = PACER.getDocumentIdFromUrl(window.location.href);
    var path = window.location.pathname;
    
    // Now do the form request to get to the view page.  Some PACER sites will
    // return an HTML page containing an <iframe> that loads the PDF document;
    // others just return the PDF document.  As we don't know whether we'll get
    // HTML (text) or PDF (binary), we ask for an ArrayBuffer and convert later.
    $('body').css('cursor', 'wait');
    var form = document.getElementById(event.data.id);
    var data = new FormData(form);
    httpRequest(form.action, data, 'arraybuffer', function (type, ab) {
      var blob = new Blob([new Uint8Array(ab)], {type: type});
      // If we got a PDF, we wrap it in a simple HTML page.  This lets us treat
      // both cases uniformly: either way we have an HTML page with an <iframe>
      // in it, which is handled by showPdfPage (defined below).
      if (type === 'application/pdf') {
        showPdfPage('<style>body { margin: 0; } iframe { border: none; }' +
                    '</style><iframe src="' + URL.createObjectURL(blob) +
                    '" width="100%" height="100%"></iframe>');
      } else {
        var reader = new FileReader();
        reader.onload = function() { showPdfPage(reader.result); };
        reader.readAsText(blob);  // convert blob to HTML text
      }

      // Given the HTML for a page with an <iframe> in it, downloads the PDF
      // document in the iframe, displays it in the browser, and also uploads
      // the PDF document to RECAP.
      function showPdfPage(html) {
        // Find the <iframe> URL in the HTML string.
        var match = html.match(/([^]*?)<iframe[^>]*src="(.*?)"([^]*)/);
        if (!match) {
          document.documentElement.innerHTML = html;
          return;
        }

        // Show the page with a blank <iframe> while waiting for the download.
        document.documentElement.innerHTML =
          match[1] + '<iframe src="about:blank"' + match[3];

        // Download the file from the <iframe> URL.
        httpRequest(match[2], null, 'arraybuffer', function (type, ab) {
          // Make the Back button redisplay the previous page.
          window.onpopstate = function(event) {
            if (event.state.content) {
              document.documentElement.innerHTML = event.state.content;
            }
          };
          history.replaceState({content: previousPageHtml});

          // Display the page with the downloaded file in the <iframe>.
          var blob = new Blob([new Uint8Array(ab)], {type: type});
          var blobUrl = URL.createObjectURL(blob);
          recap.getDocumentMetadata(
            docid, function (caseid, officialcasenum, docnum, subdocnum) {
            var filename1 = 'gov.uscourts.' + court + '.' + caseid +
              '.' + docnum + '.' + (subdocnum || '0') + '.pdf';
            var filename2 = PACER.COURT_ABBREVS[court] + '_' +
              (officialcasenum || caseid) +
              '_' + docnum + '_' + (subdocnum || '0') + '.pdf';
            var downloadLink = '<div id="recap-download" class="initial">' +
              '<a href="' + blobUrl + '" download="' + filename1 + '">' +
              'Save as ' + filename1 + '</a>' +
              '<a href="' + blobUrl + '" download="' + filename2 + '">' +
              'Save as ' + filename2 + '</a></div>';
            html = match[1] + downloadLink + '<iframe onload="' +
              'setTimeout(function() {' +
              "  document.getElementById('recap-download').className = '';" +
              '}, 7500)" src="' + blobUrl + '"' + match[3];
            document.documentElement.innerHTML = html;
            history.pushState({content: html});
          });
  
          // Upload the file to RECAP.  We can't pass an ArrayBuffer directly
          // to the background page, so we have to convert to a regular array.
          var name = path.match(/[^\/]+$/)[0] + '.pdf';
          var bytes = arrayBufferToArray(ab);
          recap.uploadDocument(court, path, name, type, bytes, function (ok) {
            if (ok) {
              //TODO: add notifier support
              //notifier.showUpload('PDF uploaded to the public archive.', null);
            }
          });
        });
      };
    });
  }, false);
} */

// Scan the document for all the links and collect the URLs we care about.
var links = document.body.getElementsByTagName('a');
var urls = [];
for (var i = 0; i < links.length; i++) {
  if (PACER.isDocumentUrl(links[i].href)) {
    urls.push(links[i].href);
  }
  addEvent(links[i],'mouseover', function () {
    if (PACER.isConvertibleDocumentUrl(this.href)) {
      pacer.convertDocumentUrl(
        this.href,
        function (url, docid, caseid, de_seq_num, dm_id, docnum) {
          recap.uploadMetadata(
            court, docid, caseid, de_seq_num, dm_id, docnum, null);
        }
      );
    }
  });
}

// Pop up a dialog offering the link to the free cached copy of the document,
// or just go directly to the free document if popups are turned off.
function handleClick(url, uploadDate) {
  prefs.get('options', function (items) {
    if (!items.options.recap_link_popups) {
      window.location = url;
      return;
    }
    $('<div id="recap-shade"/>').appendTo($('body'));
    $('<div class="recap-popup"/>').append(
      $('<a/>', {
        'class': 'recap-close-link',
        href: '#',
        onclick: 'var d = document; d.body.removeChild(this.parentNode); ' +
          'd.body.removeChild(d.getElementById("recap-shade")); return false'
      }).append(
        '\u00d7'
      )
    ).append(
      $('<a/>', {
        href: url,
        onclick: 'var d = document; d.body.removeChild(this.parentNode); ' +
          'd.body.removeChild(d.getElementById("recap-shade"))'
      }).append(
        ' Get this document as of ' + uploadDate + ' for free from RECAP.'
      )
    ).append(
      $('<br><br><small>Note that archived documents may be out of date. ' +
        'RECAP is not affiliated with the U.S. Courts. The documents ' +
        'it makes available are voluntarily uploaded by PACER users. ' +
        'RECAP cannot guarantee the authenticity of documents because the ' +
        'courts themselves provide no document authentication system.</small>')
    ).appendTo($('body'));
  },function(content){forge.logging.debug(content);});
  return false;
}

if (urls.length) {
  // Ask the server whether any of these documents are available from RECAP.
  recap.getAvailabilityForDocuments(urls, function (result) {
    // When we get a reply, update all links that have documents available.
    for (var i = 0; i < links.length; i++) {
      (function (info) {
        if (info) {
          // Insert a RECAP button just after the original link.
          $('<a/>', {
            'class': 'recap-inline',
            title: 'Available for free from RECAP.',
            href: info.filename
          }).click(function () {
            return handleClick(info.filename, info.timestamp);
          }).append(
            $('<img/>').attr({src: IMGDATAURI['icon-16.png']})
          ).insertAfter(links[i]);
        }
      })(result[links[i].href]);
    }
  });
}

