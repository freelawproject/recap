import sys, os
sys.path.extend(('../..','..', '.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from uploads.models import Document
import remove_document, urllib2
import InternetArchiveCommon as IACommon

def delete_docket_xml_from_IA(court, casenum):
    request = IACommon.make_docketxml_delete_request(court, casenum)
    try:
       response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
       if e.code != 204:
          print "   the response to the delete request was %s. This may not be an error" % e.code

def delete_docket_html_from_IA(court, casenum):
    request = IACommon.make_dockethtml_delete_request(court, casenum)
    try:
       response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
       if e.code != 204:
          print "   the response to the delete request was %s. This may not be an error" % e.code

def archive_docket_xml_locally(court, casenum, directory = "archived_dockets"):
    docket_url = IACommon.get_docketxml_url(court, casenum)

    if os.system("wget --quiet --directory-prefix=%s %s" % (directory, docket_url)) != 0:
        print "Could not archive this docket, exiting without trying to delete..."
        exit()

    print " saved docket %s.%s for analysis in %s directory" % (court, casenum, directory)

def get_court_casenum_from_argv():
    if len(sys.argv) != 2:
        print "Error: incorrect number of arguments\n"
        print usage()
        exit()

    try:
        court, casenum = sys.argv[1].split(".")
    except ValueError:
        print "Error: could not parse command line arguments\n"
        print usage()
        exit()

    return court, casenum

def get_documents(court, casenum):
    query = Document.objects.filter(court=court,
                                    casenum=casenum)

    if len(query) == 0:
        print "No documents belong to %s.%s" % court, casenum
        print usage()
        exit()
    return query

def main():
    court, casenum = get_court_casenum_from_argv()
    documents = get_documents(court, casenum)
    for document in documents:
        if document.available:
            print document.docnum
            print document.subdocnum
            remove_document.archive_document_locally(document)
            remove_document.delete_document_from_IA(document)
        document.delete()

    archive_docket_xml_locally(court, casenum)
    delete_docket_xml_from_IA(court, casenum)
    delete_docket_html_from_IA(court, casenum)




def usage():
    return "Usage: python remove_docket.py <court>.<casenum>"


if __name__ == '__main__':
    main()
