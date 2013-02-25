import sys, os
sys.path.extend(('../..','..', '.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from uploads.models import Document

import datetime

import DocketXML, UploadHandler, urllib2
import InternetArchiveCommon as IACommon

def remove_document(document):
    mark_document_as_unavailable(document)
    archive_document_locally(document)
    add_document_to_blacklist(document)
    delete_document_from_IA(document)

def mark_document_as_unavailable(document):
    if not document.available:
        print "Exiting: This document isn't currently available on IA"
        print usage()
        exit()

    document.available = 0
    document.lastdate = datetime.datetime.now() # this ensures that the archive.recapthelaw will get the update
    document.save()

    docket = DocketXML.make_docket_for_pdf("", document.court, document.casenum, document.docnum,
                                               document.subdocnum, available=0)
    UploadHandler.do_me_up(docket)

def archive_document_locally(document, directory="blacklisted_documents"):
    doc_url = IACommon.get_pdf_url(document.court, document.casenum,
                                   document.docnum, document.subdocnum)

    if os.system("wget --quiet --directory-prefix=%s %s" % (directory, doc_url)) != 0:
        print "There was an error archiving document (%s.%s.%s.%s), it has been marked as unavailble, but has not been deleted from the Internet Archive" % (document.court, document.casenum, document.docnum, document.subdocnum)
        exit()

    print "    saved document %s.%s for analysis in %s directory" % (document.docnum, document.subdocnum, directory)

def add_document_to_blacklist(document):
    BLACKLIST_PATH = "../blacklist"

    f = open(BLACKLIST_PATH, "a")
    f.write(IACommon.get_pdfname(document.court, document.casenum, document.docnum, document.subdocnum) + "\n")
    f.close()
    print "  added document to %s, you may want to add a comment in that file" % BLACKLIST_PATH

def delete_document_from_IA(document):
    request = IACommon.make_pdf_delete_request(document.court, document.casenum, document.docnum, document.subdocnum)
    try:
       response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
       if e.code != 204:
          print "   the response to the delete request was %s. This may not be an error" % e.code


def get_document_from_argv():
    if len(sys.argv) != 2:
        print "Error: incorrect number of arguments\n"
        print usage()
        exit()

    try:
        court, casenum, docnum, subdocnum = sys.argv[1].split(".")
    except ValueError:
        print "Error: could not parse command line arguments\n"
        print usage()
        exit()

    query = Document.objects.filter(court=court,
                                    casenum=casenum,
                                    docnum=docnum,
                                    subdocnum=subdocnum)

    try:
        document = query[0]
    except IndexError:
        print "Error: could not find document '%s'" % sys.argv[1]
        print usage()
        exit()

    return document

def main():
    document = get_document_from_argv()
    remove_document(document)
def usage():
    return "Usage: python remove_document.py <court>.<casenum>.<docnum>.<subdocnum>"


if __name__ == '__main__':
    main()
