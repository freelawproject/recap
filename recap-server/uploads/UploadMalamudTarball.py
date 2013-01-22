
import os
import sys
import urllib
import urllib2
import httplib
import cPickle as pickle
import datetime
import time
import socket

import ParsePacer
import DocketXML
import InternetArchiveDirect as IADirect
from recap_config import config

SERVER_URL_BASE = "%s%s" % (config["SERVER_HOSTNAME"], config["SERVER_BASEDIR"])
if not SERVER_URL_BASE.endswith("/"):
    SERVER_URL_BASE += "/"
LOCK_URL = SERVER_URL_BASE + "lock?"
UNLOCK_URL = SERVER_URL_BASE + "unlock?"

AUTH_KEY = config["UPLOAD_AUTHKEY"]
MAX_RETRIES = 10

def lock(court, casenum):

    argstring = urllib.urlencode({"court": court, 
                                  "casenum": casenum,
                                  "key": AUTH_KEY})

    lockurl = LOCK_URL + argstring
    request = urllib2.Request(lockurl)
    try:
        response = IADirect.opener.open(request)
    except urllib2.HTTPError, e: # URL Error
        return False, unicode(e.code)
    except urllib2.URLError, e:
        return False, unicode(e.reason)
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, "urllib2 bug"
    except socket.timeout:
        return False, "socket timeout"

    resp_parts = response.read().split("<br>")

    got_lock = bool(int(resp_parts[0]))
    nonce_or_message = resp_parts[1]
    
    return got_lock, nonce_or_message

def unlock(court, casenum, modified=1, ignore_nonce=0):

    argstring = urllib.urlencode({"court": court, 
                                  "casenum": casenum,
                                  "key": AUTH_KEY,
                                  "modified": int(modified),
                                  "nononce": int(ignore_nonce)})

    unlockurl = UNLOCK_URL + argstring
    request = urllib2.Request(unlockurl)
    try:
        response = IADirect.opener.open(request)
    except urllib2.HTTPError, e: # URL Error
        return False, unicode(e.code)
    except urllib2.URLError, e:
        return False, unicode(e.reason)
    except socket.timeout:
        return False, "socket timeout"
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, "urllib2 bug"

    resp_parts = response.read().split("<br>")

    released_lock = bool(int(resp_parts[0]))
    if released_lock:
        message = ""
    else:
        message = resp_parts[1]

    return released_lock, message

def print_unlock_message(releasepair):
    released_lock, message = releasepair

    if released_lock:
        print "  released lock."
    else:
        print "  could not release lock: %s" % message        

def get_timestamp():
    timestamp = datetime.datetime.now()
    timestamp = timestamp.replace(microsecond=0)
    timestamp = timestamp.isoformat(" ")
    return timestamp

def add_to_retry(casenum):
    try:
        cases_to_retry[casenum] += 1
    except KeyError:
        cases_to_retry[casenum] = 1

def del_from_retry(casenum):
    try:
        del cases_to_retry[casenum]
    except KeyError:
        pass

def add_to_failed(casenum, message):
    cases_failed.append((casenum, message))

def process_case(casenum):
    
    # Setup: Grab the lock.
    got_lock, nonce_or_message = lock(court, casenum)

    if got_lock:
        print "got the lock: %s" % (nonce_or_message)
        nonce = nonce_or_message
    else:
        print "could not get lock: %s" % (nonce_or_message)
        add_to_retry(casenum)
        return False

    casedir = "%s/%s" % (dirarg, casenum)

    # Step 1: Parse the docket.html file.
    try:
        docketpath = "%s/docket.html" % casedir
        docketfile = open(docketpath)
        docketbits = docketfile.read()
        docketfile.close()
    except IOError:
        reason = "could not open local docket"
        print "***Skipping %s.%s: %s... " % (court, casenum, reason),
        print_unlock_message(unlock(court, casenum, False))
        del_from_retry(casenum)
        add_to_failed(casenum, reason)
        return False
    else:
        docket = ParsePacer.parse_histdocqry(docketbits, court, casenum)

    if not docket:
        reason = "could not parse local docket"
        print "***Skipping %s.%s: %s... " % (court, casenum, reason),
        print_unlock_message(unlock(court, casenum, False))
        del_from_retry(casenum)
        add_to_failed(casenum, reason)
        return False

    # Step 1a: Try to fetch the the existing IA docket.
    ia_docket = None
    ia_docket_orig_string = ""
    ia_casemeta_orig_hash = ""

    ia_docketstring, fetcherror = IADirect.get_docket_string(court, casenum)

    if ia_docketstring:

        # Got the existing docket-- parse it.
        ia_docket, parseerror = DocketXML.parse_xml_string(ia_docketstring)
        if not ia_docket:
            reason = "could not parse IA docket: %s" % (parseerror)
            print "***Skipping %s.%s: %s... " % (court, casenum, reason),
            print_unlock_message(unlock(court, casenum, False))
            del_from_retry(casenum)
            add_to_failed(casenum, reason)
            return False
        else:
            # Save the original docket hashes
            ia_docket_orig_string = ia_docketstring
            ia_casemeta_orig_hash = hash(pickle.dumps(ia_docket.casemeta))

    elif fetcherror is IADirect.FETCH_NO_FILE:
        # Bucket exists but no docket-- ok.
        pass

    elif fetcherror is IADirect.FETCH_NO_BUCKET:
        # Bucket doesn't exist-- either make_bucket failed or not yet ready.

        if casenum not in bucket_made:
            # If make_bucket failed, try make_bucket again.
            print "  make bucket...",
            make_bucket(casenum)

    elif fetcherror is IADirect.FETCH_TIMEOUT:
        # Couldn't contact IA, skip.
        print "***Skipping %s.%s: IA is down... " % (court, casenum),
        print_unlock_message(unlock(court, casenum, False))
        add_to_retry(casenum)
        return False

    elif not ia_docketstring:
        # Unknown fetch error, skip.
        print "***Skipping %s.%s: unknown docket fetch error: %s..." % \
            (court, casenum, fetcherror),
        print_unlock_message(unlock(court, casenum, False))
        add_to_retry(casenum)
        return False

    # Step 1b: If necessary, merge the two dockets.
    if ia_docket:
        ia_docket.merge_docket(docket)
    else:
        ia_docket = docket

    casedir_ls = os.listdir(casedir)

    index_ls = []
    pdf_ls = []
    for casedocname in casedir_ls:
        if casedocname.endswith("index.html"):
            index_ls.append(casedocname)
        elif casedocname.endswith(".pdf"):
            pdf_ls.append(casedocname)
        
    # Step 2: Parse each index file
    for indexname in index_ls:
                
        try:
            indexpath = "%s/%s" % (casedir, indexname)
            indexfile = open(indexpath)
            indexbits = indexfile.read()
            indexfile.close()
        except IOError:
            print "***Could not open file '%s'" % indexpath
            continue

        docnum = indexname.strip("-index.html")
        index_docket = ParsePacer.parse_doc1(indexbits, court, 
                                             casenum, docnum)
        # Merge this docket into the IA docket
        ia_docket.merge_docket(index_docket)

    # Set initial flag for retrying this case.
    need_to_retry = 0

    # Step 3: Wait for the bucket to be ready
    bucketready = False
    for checkcount in xrange(20):
        bucketready, code = IADirect.check_bucket_ready(court, casenum)
        if bucketready:
            break
        else:
            # Wait 5 seconds and try again.
            time.sleep(5)

    if not bucketready:
        print "***Skipping %s.%s: bucket is not ready... " \
            % (court, casenum),
        print_unlock_message(unlock(court, casenum, False))
        add_to_retry(casenum)
        return False
        
    # Step 4: Upload each pdf file.
    doccount = 0
    for pdfname in pdf_ls:
        doccount += 1

        print "  uploading document %d/%d..." % (doccount, len(pdf_ls)),

        try:
            pdfpath = "%s/%s" % (casedir, pdfname)
            pdffile = open(pdfpath)
            pdfbits = pdffile.read()
            pdffile.close()
        except IOError:
            print "***Could not open file '%s'" % pdfpath
            continue

        pdfname = pdfname.strip(".pdf")
        split = pdfname.split("-")
        try:
            docnum = unicode(int(split[0]))
        except ValueError:
            # Not an integer.
            print "***Docnum not an integer '%s'" % pdfpath
            continue

        try:
            # converting v3->v4 subdocnums
            subdocnum = unicode(int(split[1]) - 1)   
        except IndexError:
            subdocnum = "0"                

        doc_docket = DocketXML.make_docket_for_pdf(pdfbits, court, 
                                                   casenum, docnum, 
                                                   subdocnum)
        doc_meta = doc_docket.get_document_metadict(docnum, subdocnum)

        # Only upload the PDF if the hash doesn't match the one in IA.
        ia_pdfhash = ia_docket.get_document_sha1(docnum, subdocnum)
        pdfhash = doc_docket.get_document_sha1(docnum, subdocnum)

        if ia_pdfhash != pdfhash:
            pdfstatus, pdferror = \
                IADirect.put_pdf(pdfbits, court, casenum,
                                 docnum, subdocnum, doc_meta)

            if not pdfstatus:
                # PUT failed, mark document as unavailable
                doc_docket.set_document_available(docnum, subdocnum, "0")
                print " fail: %s" % pdferror
                need_to_retry = True
                continue
            else:
                print "done."

            # Add this document's metadata into the ia_docket
            ia_docket.merge_docket(doc_docket)
            
        else:
            print "same."


    # Step 5: Push the docket to IA, if things have changed.
    print "  docket upload...",

    docket_modified = 0
    ignore_nonce = 0
    ia_docket_merged_string = ia_docket.to_xml()

    if ia_docket_orig_string != ia_docket_merged_string:

        # Assign the docket the new nonce from the lock
        ia_docket.nonce = nonce
            
        ia_casemeta_merged_hash = hash(pickle.dumps(ia_docket.casemeta))
        casemeta_diff = ia_casemeta_orig_hash != ia_casemeta_merged_hash

        putstatus, puterror = \
            IADirect.put_docket(ia_docket, court, casenum,
                                casemeta_diff=casemeta_diff)

        if putstatus:
            docket_modified = 1
            print "done."
        else:
            need_to_retry = 1
            print "fail: %s" % puterror
    else:
        ignore_nonce = 1
        print "same."
        
    if ignore_nonce:
        print_unlock_message(unlock(court, casenum, ignore_nonce=1))
    else:
        print_unlock_message(unlock(court, casenum, modified=docket_modified))

    if need_to_retry:
        add_to_retry(casenum)
        return False
    else:
        return True

def make_bucket(casenum):

    makestatus, makeerror = IADirect.make_new_bucket(court, casenum)

    if not makestatus:
        try:
            makeerror.index("409")
            print " exists."
            bucket_made.add(casenum)
        except ValueError:
            # Not a 409 error, some failure.
            print " fail."
    else:
        print " done."
        bucket_made.add(casenum)

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <directory>\n" % sys.argv[0])
        sys.exit(1)

    # Script setup.
    dirarg = os.path.abspath(sys.argv[1])
    dirarg_split = dirarg.strip("/").split("/")

    court = dirarg_split.pop()
    basedir = dirarg_split.pop()

    outfile = open("%s.out" % basedir, "w")
    errfile = open("%s.err" % basedir, "w")
    sys.stdout = outfile
    sys.stderr = errfile

    # Some global structures.
    casecount = 0
    cases_to_retry = {}
    cases_failed = []
    bucket_made = set()

    casenum_ls = os.listdir(dirarg)

    for casenum in casenum_ls:

        timestamp = get_timestamp()
        casecount += 1

        print "[%s] Make bucket %d/%d %s.%s..." % (timestamp,
                                                   casecount, len(casenum_ls),
                                                   court, casenum),
        make_bucket(casenum)

    casecount = 0
    for casenum in casenum_ls:

        timestamp = get_timestamp()
        casecount += 1

        print "[%s] Processing %d/%d %s.%s..." % (timestamp,
                                                  casecount, len(casenum_ls),
                                                  court, casenum),
        process_case(casenum)

    while len(cases_to_retry):

        retry_list = cases_to_retry.keys()

        for casenum in retry_list:
            
            num_retries = cases_to_retry[casenum]
            
            if num_retries > MAX_RETRIES:
                reason = "*** reached max retries ***"
                add_to_failed(casenum, reason)
                del_from_retry(casenum)

            else:

                timestamp = get_timestamp()

                print "[%s] Retry attempt %d/%d for %s.%s..." % \
                    (timestamp, num_retries, MAX_RETRIES, 
                     court, casenum),

                if process_case(casenum):
                    del_from_retry(casenum)
                                                                
    print "The following cases failed permanantly:"
    for (casenum, reason) in cases_failed:
        print "  * %s.%s: %s" % (court, casenum, reason)
