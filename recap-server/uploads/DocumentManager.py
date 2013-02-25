
import logging

from MySQLdb import IntegrityError

from uploads.models import Document
import InternetArchiveCommon as IACommon
import ParsePacer
from DocketXML import DocketXML

def update_local_db(docket, ignore_available=1):

    court = docket.casemeta["court"]
    casenum = docket.casemeta["pacer_case_num"]

    for docmeta in docket.documents.values():

        docnum = docmeta["doc_num"]
        subdocnum = docmeta["attachment_num"]

        docquery = Document.objects.filter(court=court,
                                           casenum=casenum,
                                           docnum=docnum,
                                           subdocnum=subdocnum)

        try:
            docentry = docquery[0]
        except IndexError:
            # Add this new document to our DB
            docentry = Document(court=court, casenum=casenum,
                                docnum=docnum, subdocnum=subdocnum)
        try:
            docentry.docid = docmeta["pacer_doc_id"]
        except KeyError:
            pass
        try:
            docentry.de_seq_num = docmeta["pacer_de_seq_num"]
        except KeyError:
            pass
        try:
            docentry.dm_id = docmeta["pacer_dm_id"]
        except KeyError:
            pass
        try:
            docentry.sha1 = docmeta["sha1"]
        except KeyError:
            pass
        if not ignore_available:
            try:
                docentry.available = docmeta["available"]
            except KeyError:
                pass
        try:
            docentry.lastdate = docmeta["upload_date"]
        except KeyError:
            pass

        try:
            docentry.free_import = docmeta["free_import"]
        except KeyError:
            pass

        try:
            docentry.save()
        except IntegrityError:
            logging.error("update_local_db: could not save %s %s %s %s"
                          % (court, casenum, docnum, subdocnum))

def mark_as_available(filename):
    docmeta = IACommon.get_meta_from_filename(filename)

    docquery =  Document.objects.filter(court=docmeta["court"],
                                        casenum=docmeta["casenum"],
                                        docnum=docmeta["docnum"],
                                        subdocnum=docmeta["subdocnum"])

    try:
        docentry = docquery[0]
    except IndexError:
        # Unexpected case.  No Document entry
        logging.error("mark_as_available: no entry for %s." % (filename))
    else:
        docentry.available = 1
        try:
            docentry.save()
        except IntegrityError:
            logging.error("mark_as_available: could not save %s."
                              % (filename))

def handle_adddocmeta(docid, court, casenum, de_seq_num, dm_id,
                      docnum, subdocnum):

    docid = ParsePacer.coerce_docid(docid)

    query = Document.objects.filter(court=court, casenum=casenum,
                                    docnum=docnum, subdocnum=subdocnum)

    try:
        doc = query[0]
    except IndexError:
        doc = Document(docid=docid, court=court, casenum=casenum,
                       de_seq_num=de_seq_num, dm_id=dm_id, docnum=docnum,
                       subdocnum=subdocnum)
    else:
        doc.de_seq_num = de_seq_num
        doc.dm_id = dm_id
        doc.docnum = docnum
        doc.docid = docid

    try:
        doc.save()
    except IntegrityError:
        logging.error("handle_adddocmeta: could not save docid %s" % (docid))



def create_docket_from_local_documents(court, casenum, removedocket=None):

    docket = DocketXML(court, casenum)
    localdocs = Document.objects.filter(court=court, casenum=casenum)

    try:
        currdoc = localdocs[0]
    except IndexError:
        return None

    for doc in localdocs:
        docket.add_document_object(doc)

    if not removedocket:
       return docket

    # We've already added the information in 'removedocket' to the local db, hence the information shows up in local
    #   so we want to remove any conflicts before merging local_docket - this will give us
    #   accurate readings of when we are actually adding locally stored information
    #   Note that this isn't perfect - information added through adddocmeta will be included in docket uploads as well
    for dockey in removedocket.documents.keys():
        for metakey in removedocket.documents[dockey].keys():
            try:
                del docket.documents[dockey][metakey]
            except KeyError:
                pass

    return docket

