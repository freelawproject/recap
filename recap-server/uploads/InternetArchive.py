
import os
import socket
import urllib2
import httplib
import logging
import datetime
import re
import cPickle as pickle
import cStringIO as StringIO
import sys

import signal
import traceback
import pdb

from MySQLdb import IntegrityError, OperationalError

from pyPdf import PdfFileReader
from pyPdf.utils import PdfReadError

from settings import ROOT_PATH
from uploads.models import Document, PickledPut, BucketLock, Uploader
import DocketXML
import UploadHandler
import BucketLockManager
import InternetArchiveDirect as IADirect
import InternetArchiveCommon as IACommon
import DocumentManager
from django.conf import settings as config

MAX_CONCURRENT_PROCESSES = 1

BASE_PICKLE_JAR = ROOT_PATH + "/picklejar"
LOCK_TIMEOUT = 86400 #seconds
AUTH_KEY = config.UPLOAD_AUTHKEY

BLACKLIST_DICT = {}

def put_file(filebits, court, casenum, docnum, subdocnum, metadict={}):
    """ PUT the file into a new Internet Archive bucket. """

    request = IACommon.make_pdf_request(filebits, court, casenum,
                                        docnum, subdocnum, metadict)

    # If this file is already scheduled, drop this. # TK: what we want?
    filename = IACommon.get_pdfname(court, casenum, docnum, subdocnum)

    query = PickledPut.objects.filter(filename=filename)
    if query:
        logging.info("put_file: same file already pickled. %s" % filename)
        return "IA PUT failed: the same file is already in the pickle bucket."

    # Add a PickledPut DB entry to schedule the PUT, not yet ready
    ppentry = PickledPut(filename=filename)

    # Fix a race case?
    try:
        ppentry.save()
    except IntegrityError:

        logging.info("put_file: same file already pickled. %s" % filename)
        return "IA PUT failed: the same file is already in the pickle bucket."


    # Pickle the request object into the jar
    pickle_success, message = pickle_object(request, filename)

    if pickle_success:
        # PickledPut now ready for processing.
        ppentry.ready = 1
        ppentry.save()
        logging.info("put_file: ready. %s" % filename)
    else:
        # Could not pickle object, so remove from DB
        logging.warning("put_file: could not pickle PDF. %s" % filename)
        ppentry.delete()

    return message

def put_docket(docket, court, casenum, ppentry,
               newbucket=0, casemeta_diff=1):

    # Put the docket to IA
    docketbits = docket.to_xml()

    request = IACommon.make_docketxml_request(docketbits, court, casenum,
                                              docket.casemeta, newbucket)

    put_result, put_msg = _dispatch_put(request, ppentry)

    if put_result:
        html_put_msg = IADirect.cleanup_docket_put(court, casenum, docket,
                                                   metadiff=casemeta_diff)
        print "  gov.uscourts.%s.%s.docket.html upload: %s" % (court,
                                                               unicode(casenum),
                                                               html_put_msg)
        DocumentManager.update_local_db(docket)

    return put_result, put_msg


def pickle_object(obj, filename, directory = BASE_PICKLE_JAR):

    # Open pickle file for writing
    try:
        f = open("%s/_%s" % (directory, filename), "w")
    except IOError:
        return False, "Pickle failed: could not open file."

    # Dump the object into the file.
    try:
        pickle.dump(obj, f)
    except pickle.PicklingError:
        return False, "Pickle failed: could not pickle object."

    f.close()

    return True, "Pickling succeeded."


def unpickle_object(filename, directory = BASE_PICKLE_JAR):

    try:
        f = open("%s/_%s" % (directory, filename))
    except IOError:
        return None, "Unpickling failed: could not open file '_%s'" % filename

    try:
        obj = pickle.load(f)
    except pickle.UnpicklingError:
        return None, "Unpickling failed: could not unpickle object."
    except:
        return None, "Unpickling failed: other error."

    f.close()

    return obj, "Unpickling succeeded."

def delete_pickle(filename):

    fullname = "%s/_%s" % (BASE_PICKLE_JAR, filename)
    try:
        os.remove(fullname)
    except OSError:
        print "  %s couldn't delete pickle." % (filename)


### Cron-specific code ###

_redirect_handler = urllib2.HTTPRedirectHandler()
opener = urllib2.build_opener(_redirect_handler)

def _quarantine_pickle(filename, ssn=False, blacklist_file=False, invalid_PDF=False):

    fullname = "%s/_%s" % (BASE_PICKLE_JAR, filename)
    if ssn:
        destname = "%s/_ssn_%s" % (BASE_PICKLE_JAR, filename)
    elif blacklist_file:
        destname = "%s/_blacklisted_%s" % (BASE_PICKLE_JAR, filename)
    elif invalid_PDF:
        destname = "%s/_invalid_pdf_%s" % (BASE_PICKLE_JAR, filename)
    else:
        destname = "%s/_quarantined_%s" % (BASE_PICKLE_JAR, filename)

    try:
        os.rename(fullname, destname)
    except OSError:
        print "  %s quarantine failed." % (filename)
    else:
        if ssn:
            print "  %s placed in SSN quarantine." % (filename)
        elif blacklist_file:
            print "  %s placed in Blacklist quarantine." % (filename)
        elif invalid_PDF:
            print "  %s placed in Invalid PDF quarantine." % (filename)
        else:
            print "  %s placed in quarantine." % (filename)

def _in_blacklist(filename):

    if BLACKLIST_DICT == {}:
        # Initialize blacklist

        BLACKLIST_LOCATION = ROOT_PATH + "/blacklist"
        try:
            f = open(BLACKLIST_LOCATION, 'r')
        except IOError:
            return False # No blacklist file
        else:
            for line in f:
                # Remove comments, if they exist
                nocomment = line[0:line.find("#")]
                BLACKLIST_DICT[nocomment.strip()] = True;

        f.close()

    return filename.strip() in BLACKLIST_DICT

def _is_invalid_pdf(request, filename):
    pdfbits = request.get_data()

    # There may be a better check for validity - this is quick and dirty
    if pdfbits.startswith("%PDF") == False:
        print "  %s is not a valid PDF." % (filename)
        return True

    return False

def _has_ssn(request, filename):

    pdfbits = request.get_data()

    try:
        # PDFFileReader will infinite loop if the input is not a valid PDF,
        # so be careful to only give it valid data
        pdfreader = PdfFileReader(StringIO.StringIO(pdfbits))
    except PdfReadError:
        # Try to fix by adding EOF
        pdfbits += "%%EOF"
        try:
            pdfreader = PdfFileReader(StringIO.StringIO(pdfbits))
        except PdfReadError:
            print "  %s could not be fixed, no EOF?" % (filename)
            return True #hack for now, will be refactored when we add alien id
        except:
            print "  %s pyPDF read error." % (filename)
            return False
    except:
        print "  %s pyPDF read error." % (filename)
        return False

    # Area number is 3 digits between [001-772] except 000, 666, [734-749]
    area_restr = "|".join(["00[1-9]", "0[1-9]\d", "[1-5]\d\d",
                           "6[0-57-9]\d", "66[0-57-9]", "7[0-25-6]\d",
                           "73[0-3]", "77[0-2]"])
    # Group number is 2 digits [01-99]
    group_restr = "|".join(["0[1-9]", "[1-9]\d"])

    # Serial number is 4 digits [0001-9999]
    serial_restr = "|".join(["000[1-9]", "00[1-9]\d", "0[1-9]\d\d",
                             "[1-9]\d\d\d"])

    ssn_re = re.compile("(%s)-(%s)-(%s)" % (area_restr, group_restr,
                                            serial_restr))

    try:
        numpages = pdfreader.getNumPages()
    except:
        return False

    for pagenum in xrange(numpages):
        try:
            pagetext = pdfreader.getPage(pagenum).extractText()
        except NotImplementedError:
            continue
        except:
            continue
        ssn_match = ssn_re.search(pagetext)
        if ssn_match:
            return True

    return False

def _update_docs_availability(docket):

    court = docket.casemeta["court"]
    casenum = docket.casemeta["pacer_case_num"]

    # Find all the docs that we know about but are not available
    query = Document.objects.filter(court=court, casenum=casenum,
                                    sha1__isnull=False)
    for doc in query:
        docnum = doc.docnum
        subdocnum = doc.subdocnum
        available = doc.available

        docket.set_document_available(docnum, subdocnum, available)


def _dispatch_put(request, ppentry):

    filename = ppentry.filename

    try:
        response = opener.open(request)

    except urllib2.HTTPError, e:

        if e.code == 201: # 201 Created: Success!
            # Delete the entry from the DB
            ppentry.delete()
            # Delete the pickle file
            delete_pickle(filename)

            return True, "IA 201 created (pickle deleted)."

        else: # HTTP Error
            # Unset the processing flag for later
#           ppentry.processing = 0
#           ppentry.save()
            # Leave the pickle file for later

            return False, "IA HTTP error %d (pickle saved)." % e.code

    except urllib2.URLError, e: # URL Error

        # if str(e.reason).startswith("timed out") or \
        # re.match(r'Network Unreachable', str(e.reason)) or \
        # re.match(r'Connection refused', str(e.reason)):
        return False, "IA URL error %s (pickle saved)." % e.reason

        #If none of the whitelisted errors above happens, quarantine the pickle

        # Delete the entry from the DB
        #ppentry.delete()
        # Quarantine the pickle file for analysis
        #_quarantine_pickle(filename)

        #return False, "IA URL error %s (pickle quarantined)." % str(e.reason)

    except socket.timeout:

        # Unset the processing flag for later
#       ppentry.processing = 0
#       ppentry.save()
        # Leave the pickle file for later

        return False, "IA timed out (pickle saved)."

    except httplib.HTTPException: # urllib2 bug... catch httplib errors

        # Unset the processing flag for later
#       ppentry.processing = 0
#       ppentry.save()
        # Leave the pickle file for later

        return False, "urllib2 bug (pickle saved)."

    else: # 200 Error, should be 201 Created
        if response.code == 200:
            ppentry.delete()
            # Delete the pickle file
            delete_pickle(filename)

            return True, "IA 200 created (pickle deleted)."
        else:
            # Delete the entry from the DB
            ppentry.delete()
            # Quarantine the pickle file for analysis
            _quarantine_pickle(filename)

            return False, "IA %d error (pickle quarantined)." % response.code

def _cron_get_updates():
    ''' Async fetch and update after a lock has been unlocked. '''

    # Calculate the TIMEOUT cutoff
    now = datetime.datetime.now()
    timeout_delta = datetime.timedelta(seconds=LOCK_TIMEOUT)
    timeout_cutoff = now - timeout_delta

    # Set both ready and expired locks to the 'processing' state.
    readylocks = BucketLockManager.mark_ready_for_processing(timeout_cutoff)
    #expiredlocks = BucketLockManager.mark_expired_for_processing(timeout_cutoff)

    # Then, go through the ready locks one-by-one with HTTP waiting.
    for lock in readylocks:
        _cron_fetch_update(lock)
    #for expiredlock in expiredlocks:
    #    court = unicode(expiredlock.court)
    #    casenum = unicode(expiredlock.casenum)
    #    print "  %s.%s lock expired." % (court, casenum)
    #    _cron_fetch_update(expiredlock)

def _cron_fetch_update(lock):
    court = unicode(lock.court)
    casenum = unicode(lock.casenum)
    nonce = unicode(lock.nonce)

    docketstring, fetcherror = IADirect.get_docket_string(court, casenum)

    if not docketstring:
        # Couldn't get the docket.  Try again later.

        if nonce:
            BucketLockManager.try_lock_later(lock)
        else:
            lock.delete()
        print "  %s.%s couldn't fetch the docket: %d" % (court, casenum,
                                                         fetcherror)
        return

    ia_docket, message = DocketXML.parse_xml_string(docketstring)

    if not ia_docket:
        # Docket parsing error.

        if nonce:
            BucketLockManager.try_lock_later(lock)
        else:
            lock.delete()
        print "  %s.%s docket parsing error: %s" % (court, casenum,
                                                    message)
        return
    elif ia_docket.nonce == nonce or not nonce:
        # Got the docket and it is either:
        #  1. up-to-date (nonce match), or
        #  2. expired (ignore nonce)
        # In both scenarios, update the local DB.
        DocumentManager.update_local_db(ia_docket, ignore_available=0)

        print "  %s.%s fetched and DB updated." % (court, casenum)

        ia_docket_orig_hash = hash(pickle.dumps(ia_docket))

        local_docket = DocumentManager.create_docket_from_local_documents(court, casenum)

        if local_docket:
            ia_docket.merge_docket(local_docket)

        ia_docket_after_local_merge_hash = hash(pickle.dumps(ia_docket))

        if ia_docket_orig_hash != ia_docket_after_local_merge_hash:
            print " After fetch, some locally stored information was missing from %s.%s. Local info addition scheduled."  % (court, casenum)
            UploadHandler.do_me_up(ia_docket)

        # Remove the lock.
        lock.delete()
    else:
        # Got the docket but it is not update to date.  Try again later.
        BucketLockManager.try_lock_later(lock)
        print "  %s.%s fetched, wait more." % (court, casenum)

def _cron_put_pickles():

    # Get uploader credentials.
    uploader_query = Uploader.objects.filter(key=AUTH_KEY)
    try:
        RECAP_UPLOADER_ID = uploader_query[0].id
    except IndexError:
        print "  could not find uploader with key=%s" % AUTH_KEY
        return

    # Get all ready pickles
    query = PickledPut.objects.filter(ready=1, processing=0) \
                              .order_by('-filename')

    # Set all ready pickles to the processing state
    #for ppentry in query:
    #    ppentry.processing = 1
    #    ppentry.save()

    # Keep track of court, casenum.  Only lock and unlock once for each case.
    curr_court = None
    curr_casenum = None
    lock_nonce = None

    # Process pickles one at a time.
    for ppentry in query:

        filename = ppentry.filename

        ppmeta = IACommon.get_meta_from_filename(filename)

        court = ppmeta["court"]
        casenum = ppmeta["casenum"]

        # Make sure we have the lock for this case.

        if curr_court == court and curr_casenum == casenum:
            # Same case as the previous ppentry.

            if not lock_nonce:
                # Skip if we don't have the lock already.
#               ppentry.processing = 0
#               ppentry.save()
                continue

            # Otherwise, we already have the lock, so continue.

        else:
            # Switching to a new case.

            # Drop the current lock (from previous case), if necessary.
            if curr_court and curr_casenum:
                dropped, errmsg = BucketLockManager.drop_lock(curr_court,
                                                              curr_casenum,
                                                              RECAP_UPLOADER_ID,
                                                              nolocaldb=1)
                if not dropped:
                    print "  %s.%s someone stole my lock?" % \
                        (court, unicode(casenum))

            # Grab new lock
            curr_court = court
            curr_casenum = casenum


            lock_nonce, errmsg = BucketLockManager.get_lock(court, casenum,
                                                            RECAP_UPLOADER_ID,
                                                            one_per_uploader=1)

            if not lock_nonce:
                print "  Passing on %s.%s: %s" % (court, casenum, errmsg)

                # We don't have a lock, so don't drop the lock in the next loop
                curr_court = None
                curr_casenum = None
                continue

        # We'll always have the lock here.

        # Unpickle the object
        obj, unpickle_msg = unpickle_object(filename)

        # Two cases for the unpickled object: Request or DocketXML
        if obj and ppentry.docket:
            print "Processing docket: %s" % filename
            _cron_process_docketXML(obj, ppentry)

        elif obj:
            # Dispatch the PUT request

            _cron_process_PDF(obj, ppentry)

        else:
           # Unpickling failed
           # If unpickling fails, it could mean that another cron job
           # has already finished this PP - not sure how to distinguish this
            print "  %s %s (Another cron job completed?)" % (filename, unpickle_msg)

            # Delete the entry from the DB
            ppentry.delete()
            # Delete the pickle file
            delete_pickle(filename)

    # Drop last lock
    if curr_court and curr_casenum:
        dropped, errmsg = BucketLockManager.drop_lock(curr_court, curr_casenum,
                                                      RECAP_UPLOADER_ID,
                                                      nolocaldb=1)
        if not dropped:
            print "  %s.%s someone stole my lock??" % (court, unicode(casenum))


def _cron_process_PDF(obj, ppentry):

    filename = ppentry.filename
    meta = IACommon.get_meta_from_filename(filename)
    court = meta["court"]
    casenum = meta["casenum"]
    docnum = meta["docnum"]
    subdocnum = meta["subdocnum"]

    invalid_PDF = _is_invalid_pdf(obj, filename)

    # We only want to check for ssns on valid PDFs
    # PyPdf doesn't deal well with bad input
    if not invalid_PDF:
       # SSN privacy check
       has_ssn = _has_ssn(obj, filename)
    else:
       has_ssn = False

    # Blacklist file check
    in_blacklist = _in_blacklist(filename)

    if invalid_PDF or has_ssn or in_blacklist:

        docket = DocketXML.make_docket_for_pdf("", court, casenum, docnum,
                                               subdocnum, available=0)
        UploadHandler.do_me_up(docket)

        # Delete the entry from the DB
        ppentry.delete()
        # Quarantine the pickle file for analysis
        _quarantine_pickle(filename, ssn=has_ssn, blacklist_file= in_blacklist, invalid_PDF= invalid_PDF)

        return


    put_result, put_msg = _dispatch_put(obj, ppentry)

    if put_result:
        # Put success-- mark this document as available in the DB
        DocumentManager.mark_as_available(filename)

        docket = DocketXML.make_docket_for_pdf("", court, casenum, docnum,
                                               subdocnum, available=1)
        UploadHandler.do_me_up(docket)


    print "  %s %s" % (filename, put_msg)

def _cron_process_docketXML(docket, ppentry):
    ''' Required to have the lock. '''

    court = docket.casemeta["court"]
    casenum = docket.casemeta["pacer_case_num"]

    # Force '0' in the XML on docs that failed to upload.
    _update_docs_availability(docket)

    # The docket filename
    docketname = IACommon.get_docketxml_name(court, casenum)

    # Step 1: Try to fetch the existing docket from IA
    docketstring, fetcherror = IADirect.get_docket_string(court, casenum)

    if docketstring:
        # Got the existing docket-- put merged docket file.
        ia_docket, parse_msg = DocketXML.parse_xml_string(docketstring)

        if ia_docket:
            put_result, put_msg = _cron_me_up(ia_docket, docket, ppentry)

            print "  %s %s" % (docketname, put_msg)
        else:
            print "  %s docket parsing error: %s" % (docketname, parse_msg)

    elif fetcherror is IADirect.FETCH_NO_FILE:
        # Bucket exists but no docket-- put a new docket file.
        put_result, put_msg = put_docket(docket, court, casenum, ppentry)

        print "  %s put into existing bucket: %s" % (docketname, put_msg)

    elif fetcherror is IADirect.FETCH_NO_BUCKET:
        # Bucket doesn't exist-- make the bucket and put a new docket file.
        put_result, put_msg = put_docket(docket, court, casenum, ppentry,
                                         newbucket=1)

        print "  %s put into new bucket: %s" % (docketname, put_msg)

    elif fetcherror is IADirect.FETCH_URLERROR:
        # Couldn't get the IA docket

        # Unset the processing flag for later
#        ppentry.processing = 0
#        ppentry.save()
        # Leave the pickle file for later
        # Drop Lock Here?

        print "  %s timed out.  wait for next cron." % (docketname)

    else:
        # Unknown fetch error.

        # Unset the processing flag for later
#        ppentry.processing = 0
#        ppentry.save()
        # Drop Lock Here?

        # Leave the pickle file for later
        print "  %s unknown fetch error.  wait for next cron." % (docketname)

def _cron_me_up(ia_docket, docket, ppentry):
    ''' Merge and update docket'''

    ia_court = ia_docket.casemeta["court"]
    ia_casenum = ia_docket.casemeta["pacer_case_num"]

    # Save the original hash to diff with later
    ia_docket_orig_hash = hash(pickle.dumps(ia_docket))
    ia_casemeta_orig_hash = hash(pickle.dumps(ia_docket.casemeta))

    # Merge ia_docket with our local database information to fill in blank fields that may exist in ia
    local_docket = DocumentManager.create_docket_from_local_documents(ia_court, ia_casenum, docket)

    if local_docket:
        ia_docket.merge_docket(local_docket)

    ia_docket_after_local_merge_hash = hash(pickle.dumps(ia_docket))

    if ia_docket_orig_hash != ia_docket_after_local_merge_hash:
        print " Some locally stored information was missing from %s.%s. Local info added."  % (ia_court, ia_casenum)

    # Step 2: Merge new docket into the existing IA docket
    ia_docket.merge_docket(docket)

    # Step 3: If diff, then upload the merged docket
    ia_docket_merged_hash = hash(pickle.dumps(ia_docket))

    if ia_docket_orig_hash != ia_docket_merged_hash:

        # Generate a new nonce for the docket
        ia_docket.nonce = DocketXML.generate_new_nonce()

        ia_casemeta_merged_hash = hash(pickle.dumps(ia_docket.casemeta))
        casemeta_diff = ia_casemeta_orig_hash != ia_casemeta_merged_hash

        # Put the docket to IA
        put_result, put_msg = put_docket(ia_docket, ia_court, ia_casenum,
                                         ppentry, casemeta_diff=casemeta_diff)

        return put_result, "merged: %s" % put_msg

    else:
        # No difference between IA docket and this docket, no need to upload.

        filename = ppentry.filename

        # Delete the entry from the DB
        ppentry.delete()
        # Delete the pickle file
        delete_pickle(filename)

        # Return False to reflect "no update"
        return False, "not merged: no diff."

def _silence_emails():
    silence_emails = False
    try:
        statinfo = os.stat(ROOT_PATH + '/silence_warning_emails')
    except OSError:
        pass
    else:
        thentime = datetime.datetime.fromtimestamp(statinfo.st_mtime)
        if thentime + datetime.timedelta(hours=6) > datetime.datetime.now(): # silence emails if file has been touched within 6 hours
            silence_emails = True

    return silence_emails


def _get_number_of_running_jobs():
    # The cron job runs as user recap info (UID 1008)
    return int(os.popen("ps -eu harlanyu |grep python2.5| wc -l").read())


def _check_for_long_running_jobs():
    long_running_jobs = os.popen("ps -o etime,pid,comm -u 1008 | grep python | grep -e '\([0-9][0-9]:\)\?[5-9][0-9]:[0-9][0-9]'").read()

    if long_running_jobs and _silence_emails():
        print " Found long running job(s) %s... but emails have been silenced, so NOT sending email" % long_running_jobs.strip()
        return
    elif long_running_jobs:
        print " Found long running job(s) %s...sending email" % long_running_jobs.strip()

        emailmessagecmd = ['/usr/bin/sendEmail', '-f "recaplogger@gmail.com"',
                           '-t dhruv@dkapadia.com sjs@princeton.edu tblee@princeton.edu harlanyu@princeton.edu',
                           '-u "[Automated] Runaway RECAP cron job?"',
                           '-s smtp.gmail.com:587 -xu recaplogger@gmail.com -xp REMOVED',
                           '-m "There is probably a runaway cron job on monocle. See the following ps output:',
                           long_running_jobs.strip(),
                   '\n\nIf you want to silence these emails for 6 hours: log onto monocle, su to harlanyu and touch /var/django/recap_prod/recap-server/silence_warning_emails"']

        os.popen(" ".join(emailmessagecmd))


def _run_cron():

    # Fetch updates from external uploaders.
    _cron_get_updates()
    # Put all pickled requests to IA.
    _cron_put_pickles()


def enter_pdb(sig, frame):
    pdb.set_trace()


def print_stacktrace(sig, frame):
    f = open("/var/django/recap_prod/recap-server/crash.log", "a")
    f.write(str(traceback.extract_stack()))

    f.write("\n")
    f.flush()
    f.close()


def listen_for_interrupts():
    signal.signal(signal.SIGUSR1, print_stacktrace)
    signal.signal(signal.SIGUSR2, enter_pdb)

if __name__ == '__main__':
    os.umask(0012) # necessary to get let pickles and www-data play nicely

    listen_for_interrupts()

    # Print timestamp
    timestamp = datetime.datetime.now()
    timestamp = timestamp.replace(microsecond=0)
    timestamp = timestamp.isoformat(" ")
    print "[%s] Running IA cron..." % timestamp

    _check_for_long_running_jobs()

    num_jobs = _get_number_of_running_jobs()
    if num_jobs > MAX_CONCURRENT_PROCESSES:
       print " Stopping execution, %d jobs already running" % MAX_CONCURRENT_PROCESSES
    else:
       # Run the cron job
       _run_cron()
