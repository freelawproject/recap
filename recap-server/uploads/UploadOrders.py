import sys
import os
import glob
import re
#################### DJANGO CONFIG ####################                         
sys.path.extend(('../..', '..', '.'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'recapsite.settings'
#######################################################


import UploadMalamudTarball as UM
import ParsePacer as PP
import InternetArchive as IA
import InternetArchiveDirect as IADirect
import cPickle as pickle

import pdb




def create_docket_pickles(path, court):
    #check if docket pickle directory exists and pickle generation has completed
    opinion_reports= glob.glob(os.path.join(path, "*.opinions.*"))


    try:
        os.mkdir(os.path.join(path, 'docket_pickles'))
    except OSError:
        #delete docket_pickles
        pass

    for report in opinion_reports:
        filebits = open(report).read()
        dockets = PP.parse_opinions(filebits, court)

        if dockets:
            print "Found %s dockets in %s " % (len(dockets), report)
            for docket in dockets:
                if len(docket.documents) != 1:
                    raise "This docket has more than one document! docket text: " % docket
                doc = docket.documents.values()[0]
                filename = _get_docket_pickle_filename(court, doc['casenum'], doc['doc_num'], doc['attachment_num'])
                success, msg = IA.pickle_object(docket, filename, os.path.join(path, "docket_pickles"))

                if not success:
                    print "Error pickling file %s: %s " % (filename, msg)



def mark_directory_complete(current_path):
    f = open(os.path.join(current_path, '../completed_directories'), "a")
    f.write(os.path.basename(current_path))
    f.write("\n")

def read_documents_from_mapping(current_path):
    f = open(os.path.join(current_path, 'mapping'), "r")

    documents = {}
    for line in f:
        url, docid = line.strip().split(' ')
        args = re.split(r'&', url)
        document = {}
        for s in args:
            (k, v) = re.split(r'=', s)
            if k == 'de_seq_num':
                document['pacer_de_seq_num'] = v
            if k == 'dm_id':
                document['pacer_dm_id'] = v
            if k == 'doc_num':
                document['doc_num'] = v
            if re.match(r'^.*caseid$', k):
                document['casenum'] = v
        document['docid'] = docid
        #hopefully a good assumption
        document['attachment_num'] = '0'

        documents[docid] = document

    return documents

def upload_documents(path, court, documents):
    for docid in sorted(documents.keys()):
        document = documents[docid]

        success, msg = _upload_document(path, court, document)

        #handle retry stuff here



def _upload_document(path, court, document):
    filename = _get_docket_pickle_filename(court, document['casenum'], document['doc_num'], document['attachment_num'])

    docket, msg = IA.unpickle_object(filename, os.path.join(path, 'docket_pickles'))
    if not docket:
        return False, 'Could not unpickle: %s' % msg

    casenum = docket.get_casenum()
    got_lock, nonce_or_message = UM.lock(court, casenum)
    # We need to: grab a lock
    if got_lock:
        print "got the lock: %s" % (nonce_or_message)
        nonce = nonce_or_message
    else:
        return False, "could not get lock: %s" % (nonce_or_message)

    # Get the existing ia docket, if it exists
    ia_docket = None
    ia_docket_orig_string = ""
    ia_casemeta_orig_hash = ""

    ia_docketstring, fetcherror = IADirect.get_docket_string(court, casenum)

    if ia_docketstring:
        # Got the existing docket-- parse it.
        ia_docket, parseerror = DocketXML.parse_xml_string(ia_docketstring)
        if not ia_docket:
            reason = "could not parse IA docket: %s" % (parseerror)
            UM.print_unlock_message(UM.unlock(court, casenum, False))
            return False, "***Skipping %s.%s: %s... " % (court, casenum, reason),
        else:
            # Save the original docket hashes
            ia_docket_orig_string = ia_docketstring
            ia_casemeta_orig_hash = hash(pickle.dumps(ia_docket.casemeta))

        print "There is a docket for %s, %s! " % (court, casenum)
    elif fetcherror is IADirect.FETCH_NO_FILE:
        # Bucket exists but no docket-- ok.
        pass

    elif fetcherror is IADirect.FETCH_NO_BUCKET:
        # Bucket doesn't exist-- either make_bucket failed or not yet ready.
        # That's okay, we'll make the bucket with the first upload

        #if casenum not in bucket_made:
            # If make_bucket failed, try make_bucket again.
        #    print "  make bucket...",
        #    make_bucket(casenum)

    elif fetcherror is IADirect.FETCH_TIMEOUT:
        # Couldn't contact IA, skip.
        UM.print_unlock_message(UM.unlock(court, casenum, False))
        #TK: Handle retry logic here?
        return False, "***Skipping %s.%s: IA is down... " % (court, casenum),

    elif not ia_docketstring:
        # Unknown fetch error, skip.
        UM.print_unlock_message(UM.unlock(court, casenum, False))
        return False, "***Skipping %s.%s: unknown docket fetch error: %s..." % \
            (court, casenum, fetcherror),
    
    # Step 1b: If necessary, merge the two dockets.
    if ia_docket:
        ia_docket.merge_docket(docket)
    else:
        ia_docket = docket

    # Upload the pdf

    #TK: add some better status updates here, maybe uploading doc 123 of 1234
    print "  uploading document %s.%s.%s..." % (court, casenum, document['doc_num']),
    try:
        doc_filename = os.path.join(path, document['docid'], ".pdf"
        pdfbits = open(doc_filename)).read()
    except IOError:
        UM.print_unlock_message(UM.unlock(court, casenum, False))
        return False, "  ***Could not open file %s " % doc_filename

    #TK: probably need to make the bucket before doing this
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
            # TK: handle retry here
            UM.print_unlock_message(UM.unlock(court, casenum, False))
            return False, " fail: %s" % pdferror
        else:
            print "done."

            # Add this document's metadata into the ia_docket
        ia_docket.merge_docket(doc_docket)

       
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





        
    UM.print_unlock_message(UM.unlock(court, casenum, modified = False))
    return True, "Document uploaded"


def _get_docket_pickle_filename(court, casenum, doc_num, attachment_num):
    return ".".join([court, casenum, doc_num, attachment_num, 'docket'])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <directory>\n" % sys.argv[0])
        sys.exit(1)

    #this should be the directory
    # mirrored from http://protect.theinfo.org/pacer/
    dirarg = os.path.abspath(sys.argv[1])
    # a set will make it easy for us to subtract completed directires 
    directories = set([d for d in os.listdir(dirarg) if os.path.isdir(os.path.join(dirarg, d))])

    completed_directories = set([line.strip() for line in open(os.path.join(dirarg, 'completed_directories')).readlines()])

    directories -= completed_directories


    for directory in sorted(directories):
        print "Opening directory %s " % directory

        court = directory.split('.')[1]

        current_path = os.path.join(dirarg, directory)
        create_docket_pickles(current_path, court)

        #- Read in a mapping file, find the appropriate doc and docket
        documents = read_documents_from_mapping(current_path)

        #read in completed documents, remove from documents hash
        #completed_documents = set([line.strip() for line in open(os.path.join(current_path, 'completed_documents')).readlines()])
        #for docid in completed_documents:
        #    del 

        upload_documents(current_path, court, documents) 


        
        #loop over entries in documetns hash, :

        pdb.set_trace()


        #upload pickles
        mark_directory_complete(current_path)



        break

        
        
        
        







        

    #directories_completed = open(somefile).read




