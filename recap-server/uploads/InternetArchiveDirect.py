
import urllib2
import httplib
import socket
import logging

import InternetArchiveCommon as IACommon

FETCH_NO_BUCKET = -1
FETCH_NO_FILE = -2
FETCH_URLERROR = -3
FETCH_TIMEOUT = -4
FETCH_UNKNOWN = -5

NO_BUCKET_HTML_MESSAGE="The item you have requested has a problem with one or more of the\n\
metadata files that describe it, which prevents us from displaying this\n\
page"

_redirect_handler = urllib2.HTTPRedirectHandler()
opener = urllib2.build_opener(_redirect_handler)

def is_xml(mimetype):
    return mimetype == "application/xml" or mimetype == "text/xml"

def is_html(mimetype):
    return mimetype.find("text/html") >= 0

def get_docket_string(court, casenum):
    docketurl = IACommon.get_docketxml_url(court, casenum)    

    request = urllib2.Request(docketurl)

    try:
        response = opener.open(request)
    except urllib2.HTTPError, e: # HTTP Error
        if e.code == 404:
            bits = e.read()
            # IA returns different 404 pages if the bucket exists or not
            # This might be a brittle way to check the difference, but don't think there's a better way
            if(bits.find(NO_BUCKET_HTML_MESSAGE) > 0):
                return None, FETCH_NO_BUCKET
            # Otherwise, assume the bucket exists
            return None, FETCH_NO_FILE
        else:
            logging.info("get_docket_string: unknown fetch code %d" % e.code)
            return None, FETCH_UNKNOWN
    except urllib2.URLError, e: # URL Error, IA down.
        return None, FETCH_URLERROR
    except socket.timeout:
        return None, FETCH_TIMEOUT
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return None, FETCH_UNKNOWN
    else:
        mimetype = response.info().getheader("Content-Type")
        if is_xml(mimetype):
            bits = response.read()
            if not bits:
                # Zero length
                return None, FETCH_NO_BUCKET
            else:
                return bits, ""
        #elif is_html(mimetype):
        #    return None, FETCH_NO_BUCKET
        return None, FETCH_NO_BUCKET

def check_bucket_ready(court, casenum):
    bucketurl = IACommon.get_bucketcheck_url(court, casenum)
    
    request = urllib2.Request(bucketurl)

    try:
        response = opener.open(request)
    except urllib2.HTTPError, e: # HTTP Error
        # No bucket exists, probably a 404 code.
        return False, int(e.code)
    except urllib2.URLError, e: # URL Error, IA down.
        return False, FETCH_URLERROR
    except socket.timeout:
        return False, FETCH_TIMEOUT
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, FETCH_UNKNOWN
    else:
        return True, 200

def make_new_bucket(court, casenum):
    
    request = IACommon.make_bucket_request(court, casenum, makenew=1)
    return _dispatch_direct_put(request)

def put_docket(docket, court, casenum, casemeta_diff=1):

    docketbits = docket.to_xml()
    
    request = IACommon.make_docketxml_request(docketbits, court, casenum, 
                                              docket.casemeta)

    put_result, put_msg = _dispatch_direct_put(request)

    if put_result:
        cleanup_docket_put(court, casenum, docket, metadiff=casemeta_diff)
    
    return put_result, put_msg

def put_casemeta(court, casenum, metadict={}):
    request = IACommon.make_casemeta_request(court, casenum, metadict)
    return _dispatch_direct_put(request)


def put_pdf(filebits, court, casenum, docnum, subdocnum, metadict={}):
    """ PUT the file into a new Internet Archive bucket. """
    request = IACommon.make_pdf_request(filebits, court, casenum, 
                                        docnum, subdocnum, metadict)

    return _dispatch_direct_put(request)

def put_dockethtml(court, casenum, docket):
    dockethtml = docket.to_html()
    request = IACommon.make_dockethtml_request(dockethtml, court, casenum,
                                               docket.casemeta)
    return _dispatch_direct_put(request)

def cleanup_docket_put(court, casenum, docket, metadiff=1):
    
    # Best-effort casemeta update
    if metadiff:
        put_casemeta(court, casenum, docket.casemeta)
    # Best-effort docket HTML update
    putstatus, putmsg = put_dockethtml(court, casenum, docket)    
    return putmsg

def _dispatch_direct_put(request, tries_so_far=0):

    try:
        response = opener.open(request)
    except urllib2.HTTPError, e:
        if e.code == 201: # 201 Created: Success!
            return True, "IA 201 created."
        elif e.code == 409: # 409 Conflict (if bucket name already exists)
            return False, "IA 409 conflict."
        else: # HTTP Error
            if tries_so_far < 3:
                return _dispatch_direct_put(request, tries_so_far+1)
            else:
                return False, "IA HTTP error %d." % e.code
    except urllib2.URLError, e: # URL Error
        return False, "IA URL error %s." % e.reason
    except socket.timeout:
        return False, "IA timed out."
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, FETCH_UNKNOWN
    else: # 200 Error, should be 201 Created
        if response.code == 200:
           return True, "IA 200 created."
        else:
           return False, "IA %d error." % response.code

