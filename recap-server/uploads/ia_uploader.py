#################### DJANGO CONFIG ####################
import sys, os
sys.path.extend(('..', '.'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'recap-server.settings'
#######################################################
import urllib, urllib2
import httplib
import socket
import time

import InternetArchiveDirect as IADirect
import InternetArchiveCommon as IACommon
import DocketXML

from recap_config import config
import cPickle as pickle
import pika

import logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(name)s: %(message)s',
    filename = 'uploader.log',
    filemode = 'a'
)
logger = logging.getLogger('ia_uploader')    

SERVER_URL_BASE = "%s%s" % (config["SERVER_HOSTNAME"], config["SERVER_BASEDIR"])
if not SERVER_URL_BASE.endswith("/"):
    SERVER_URL_BASE += "/"
LOCK_URL = SERVER_URL_BASE + "lock/?"
UNLOCK_URL = SERVER_URL_BASE + "unlock/?"

RECAP_AUTH_KEY = config['OPINIONS_UPLOADER_AUTHKEY']
opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())

connection = pika.BlockingConnection(pika.ConnectionParameters(
                            'localhost'))
channel = connection.channel()
channel.queue_declare(queue='dockets')

def decode_message(ch, method, properties, body):
    message = pickle.loads(body)
    delay_message = _should_delay_message(message)

    if delay_message:
        logger.debug('Skipping message, not time yet!')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch.basic_publish(exchange='',
                     routing_key='dockets',
                     body=pickle.dumps(message))
        return

    try:
        success, msg = lock_and_handle_message(message)
    except IOError, e:
        logger.error('IOError when processing case %s.%s, deleting message. Error message: %s' % 
                                (message['court'], message['casenum'], str(e)))
        # Not really successful, but this will delete the message below
        success = True

    # Acknowledge the message to take it off the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)

    if not success:
        logger.warning('A failure occurred. Attempting to requeue the message')
        logger.warning('Upload message for %s.%s did not succeed: %s' % (message['court'],
                                                                       message['casenum'],
                                                                       msg))
        _requeue_message(ch, message)

def lock_and_handle_message(message):
    court = message['court']
    casenum = message['casenum']

    logger.info('Starting upload for %s.%s', court, casenum)
    got_lock, lock_message = _lock(court, casenum)

    if not got_lock:
        logger.warning('Could not get lock for %s.%s: %s' %
                                (court, casenum, lock_message))
        return False, "Could not acquire lock"

    success, msg = _handle_message(message, lock_message)
        
    modified = 0 if msg == "Unmodified" else 1

    logger.debug('Finished processing %s.%s. Releasing lock.' %
                                (court, casenum))

    released_lock, lock_msg = _unlock(court, casenum, modified=int(modified))

    if success:
        _cleanup_successful_message(message)
    return success, msg


""" Main method to handle uploading. Message should be a dict (format fluid). Nonce is required for docket uploads
    Returns a tuple (successful_upload, message)"""
def _handle_message(message, nonce):
    # messages must contain a docket, which will give us some metadata
    docket = _unpickle_object(message['docket_filename'])
        
    #TK: This seems awkward. Almost certainly a better way to do this.
    success = True 
    # documents are an optional part of each message
    # if we want to handle different types of docs (audio files, for example, we'd do it here)
    if message.get('docnums_to_filename'):
        # Docket is modified inside _upload_documents if uploads succeed
        logger.info('Uploading %s documents for %s.%s'  % 
                         (len(message['docnums_to_filename']), 
                            docket.get_court(), docket.get_casenum()))
        success, msg = _upload_documents(docket, message['docnums_to_filename'])

    if success:
        success, msg = upload_docket(docket, nonce)
        
    return success, msg 

""" Upload a map of documents. 
    Params:
    docket should be the docket to which these documents belong. 
        docket is modified when docs are successfully uploaded

    docmap should be a map of docnums-> filename:
        ({'1-2': 'filename_for_docnum_1_and_subdoc_2'})

"""
def _upload_documents(docket, docmap):
    court = docket.get_court()
    casenum = docket.get_casenum()
    for dockey, filename in docmap.items():
        #TK: abstract this split into a separate function
        docnum, subdocnum = dockey.split('-')
        pdfbits = _unpickle_object(filename)

        # make a docket that contains some metadata (sha1, etc) for this docket
        temp_docket = DocketXML.make_docket_for_pdf(pdfbits, court, casenum, 
                                           docnum, subdocnum, available=0, free_import=1)

        docket.merge_docket(temp_docket)

        doc_success, doc_msg = upload_document(pdfbits, court, casenum, 
                                                        docnum, subdocnum)
        if doc_success:
            docket.set_document_available(docnum, subdocnum, "1")
        else:
            #TK: I don't think we unlock correctly here
            return False, doc_msg

    return True, "All documents uploaded"

        

def _should_delay_message(message):
    if not message.get('next_attempt_time'):
        return False
    current_time = time.time()
    if message['next_attempt_time'] > current_time:
        return True
    return False 

def _requeue_message(ch, message):
    """ Attempt to requeue message if it has not been requeued too many times before. 
        Returns True on successfully requeue, False otherwise"""
    try:
        attempt_num = message['attempt_num']
        next_attempt_time = message['next_attempt_time']
    except KeyError:
        attempt_num = 0 
        next_attempt_time = time.time()

    attempt_num += 1
    time_delta = 2 ** attempt_num
    next_attempt_time += time_delta

    message['attempt_num'] = attempt_num
    message['next_attempt_time'] = next_attempt_time 

    # 2^ 15 ~= 9 hours
    if(attempt_num > 15):
        logger.warning('Message for %s.%s has failed %s times. Giving up forever!' % \
                        (message['court'], message['casenum'], attempt_num))
        return False
    
    logger.warning('Message for %s.%s has failed %s times. Trying again in %s seconds' % \
                        (message['court'], message['casenum'], attempt_num, time_delta))
    ch.basic_publish(exchange='',
                     routing_key='dockets',
                     body=pickle.dumps(message))

    return True

def _cleanup_successful_message(message):
    logger.debug('Deleting file: %s' % message['docket_filename'])
    os.unlink(message['docket_filename'])
    if(message.get('docnums_to_filename')):
        for dockey, filename in message['docnums_to_filename'].items():
            logger.debug('Deleting file: %s' % filename)
            os.unlink(filename)

def upload_docket(docket, nonce):
    """Case should be locked prior to this method"""
    ia_docket, message = _get_docket_from_IA(docket) 
    if ia_docket:
        docket.merge_docket(ia_docket)

    # Don't upload if nothing has changed
    if docket == ia_docket: 
        return True, 'Unmodified'

    docket.nonce = nonce

    #TK: Check that it's okay to always request a new bucket made
    request = IACommon.make_docketxml_request(docket.to_xml(), 
                                                  docket.get_court(), 
                                                  docket.get_casenum(),
                                                  docket.casemeta, 
                                                  makenew=True)
            
    success, msg = _post_request(request)

    if not success:
        logger.error('XML Docket upload for %s.%s failed: %s', docket.get_court(), 
                                                                docket.get_casenum(),
                                                                msg)
        return False, msg

    logger.info('XML Docket upload for %s.%s succeeded', docket.get_court(), 
                                                          docket.get_casenum())


    # TK: Maybe handle this in a separate function that can deal with html?
    # Assuming this is sucessful, also upload an update to the html page
    request = IACommon.make_dockethtml_request(docket.to_html(), 
                                               docket.get_court(), 
                                               docket.get_casenum(),
                                               docket.casemeta)

    success, msg = _post_request(request)
    if not success:
        logger.error('HTML Docket upload for %s.%s failed: %s', docket.get_court(), 
                                                                 docket.get_casenum(),
                                                                 msg)
        return False, msg

    logger.info('HTML Docket upload for %s.%s succeeded', docket.get_court(), 
                                                          docket.get_casenum())
    return success, msg

def upload_document(pdfbits, court, casenum, docnum, subdocnum):
    logger.info('   Uploading document %s.%s.%s.%s' % (court, casenum, docnum, subdocnum))
    request = IACommon.make_pdf_request(pdfbits, court, casenum, 
                                        docnum, subdocnum, metadict = {},
                                        makenew=True)
    success, msg = _post_request(request)
    if not success:
        logger.error('   Failed to upload document %s.%s.%s.%s' % (court, casenum, docnum, subdocnum))
        return False, msg
    logger.info('  Uploaded document %s.%s.%s.%s' % (court, casenum, docnum, subdocnum))
    return success, msg



def _post_request(request):
    try:
        response = opener.open(request)
    except urllib2.HTTPError, e:
        if e.code == 201:
            return True, "IA 201 created."
        else:
            return False, "IA HTTP error %d." % e.code
    except urllib2.URLError, e: # URL Error
        return False, "IA URL error %s." % e.reason
    except socket.timeout:
        return False, "IA timed out."
    else:
        if response.code == 200:
            return True, "Success"
        else:
            return False, "IA %d error" % response.code
        
def _lock(court, casenum):
    argstring = urllib.urlencode({"court": court, 
                                  "casenum": casenum,
                                  "key": RECAP_AUTH_KEY})

    lockurl = LOCK_URL + argstring
    request = urllib2.Request(lockurl)
    try:
        response = opener.open(request)
    except urllib2.HTTPError, e: # URL Error
        return False, unicode(e.code)
    except urllib2.URLError, e:
        return False, unicode(e.reason)
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, "urllib2 bug"
    except socket.timeout:
        return False, "socket timeout"
    
    got_lock, nonce_or_message = _split_lock_message(response.read())
    return got_lock, nonce_or_message


def _unlock(court, casenum, modified=1, ignore_nonce=0):

    argstring = urllib.urlencode({"court": court, 
                                  "casenum": casenum,
                                  "key": RECAP_AUTH_KEY,
                                  "modified": int(modified),
                                  "nononce": int(ignore_nonce)})

    unlockurl = UNLOCK_URL + argstring
    request = urllib2.Request(unlockurl)
    try:
        response = opener.open(request)
    except urllib2.HTTPError, e: # URL Error
        return False, unicode(e.code)
    except urllib2.URLError, e:
        return False, unicode(e.reason)
    except socket.timeout:
        return False, "socket timeout"
    except httplib.HTTPException: # urllib2 bug... catch httplib errors
        return False, "urllib2 bug"

    released_lock, message = _split_lock_message(response.read())
    
    return released_lock, message

def _get_docket_from_IA(docket):
    docketstring, fetcherror = IADirect.get_docket_string(docket.get_court(), docket.get_casenum())

    if docketstring:
        # Got the existing docket-- put merged docket file.
        ia_docket, parse_msg = DocketXML.parse_xml_string(docketstring)

        if ia_docket:
            return ia_docket, fetcherror
        else:
            print "  %s docket parsing error: %s" % (docketname, parse_msg)
            return None, parse_msg 
    return None, fetcherror 

def _split_lock_message(html_response):
    logger.debug("Lock/Unlock message is: %s" % html_response)
    resp_parts = html_response.split("<br>")

    got_or_released_lock = bool(int(resp_parts[0]))

    try:
        nonce_or_message = resp_parts[1]
    except IndexError:
        # There is only sometimes a message
        nonce_or_message = None

    return got_or_released_lock, nonce_or_message

def _unpickle_object(filename):
    f = open(filename)
    obj = pickle.load(f)
    f.close()
    return obj 

def run_uploader():
    logger.info('IA Uploader started: Listening for messages')
    listen_for_messages()

def listen_for_messages():
    channel.basic_consume(decode_message, 
                            queue = 'dockets')
    channel.start_consuming()

if __name__ == "__main__":
    run_uploader()
