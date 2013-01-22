import sys, os
sys.path.extend(('../..','..', '.'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from uploads.models import Document
import InternetArchiveDirect as IADirect
import InternetArchiveCommon as IACommon
import DocketXML
import remove_docket, remove_document, urllib2
from optparse import OptionParser

def delete_documents_from_docket(court, casenum, documents):
    # Step 1: Get docket and convert into DocketXML
    docketstring, fetcherror = IADirect.get_docket_string(court, casenum)

    if not docketstring:
        print "Could not find docket on IA, exiting...."
        exit()
    
    ia_docket, message = DocketXML.parse_xml_string(docketstring)

    if not ia_docket:
        print "Docket parsing error: %s.%s, exiting...." % (court, casenum)
        exit()

    # Step 2: Remove documents from DocketXML object

    for document in documents:
        ia_docket.remove_document(document.docnum, document.subdocnum)

    # Step 3: upload modified xml
    docketbits = ia_docket.to_xml()

    request = IACommon.make_docketxml_request(docketbits, court, casenum,
                                              ia_docket.casemeta) 

    success_status = False
    try:
       response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        if e.code == 201 or e.code == 200: # 201 Created: Success!
            print "Updated %s %s docket.xml" % (court, casenum)
            success_status = True

    
    #attempt to upload a new version of html
    html_put_msg = IADirect.cleanup_docket_put(court, casenum, ia_docket, 
                                               metadiff=0)

    print "   Updated %s %s : %s" % (court, casenum, html_put_msg)

    return success_status

def get_documents(court, casenum, docrange, show_warning=True):
    docnum_list = [] 

    #if it's a single document
    if len(docrange.split(",")) == 1 and docrange.find('-') < 0:
       docnum_list.append(docrange)
    else:
       for d in docrange.split(","):
          if d.find("-") > -1:
              start, end = d.split("-")
              docnum_list += range(int(start), int(end)+1)
          else:
              docnum_list.append(d)


    query = Document.objects.filter(court=court, 
                                    casenum=casenum, 
                                    docnum__in=docnum_list, 
                                    subdocnum=0)

    try: 
        doc = query[0]
    except IndexError:
        print "could not find any documents, exiting..."
        exit()
    #after sanity checks above, add in all associated subdocuments 
    query = Document.objects.filter(court=court, 
                                    casenum=casenum, 
                                    docnum__in=docnum_list)
        
    if show_warning:
        print "You are about to remove %s documents (#'s: %s ) from this case. Are you sure? (y/N) " % ( str(len(query)), [str(d.docnum) for d in query] ),
        s = sys.stdin.read(1)

        if s != 'y':
          exit()

    return query

def parse_args():
    parser = OptionParser()
    parser.add_option("--court", dest="court",
		               help="3 or 4 letter court abbreviation (e.g: cand, mad) (required)")
    parser.add_option("--casenum", dest="casenum",
                       help="pacer case number of docket (required)")
    parser.add_option("--action", dest="action", 
                       help="action to modify this docket (delete_document depends on docranged)", 
                       default="delete_documents")

    parser.add_option("--docrange", dest="docrange", 
                       help="docrange to delete (no spaces!: '3,4,33-55')")
    
    parser.add_option("--no_warn", action="store_false", dest="show_warning", 
                       help="don't require user confirmation before deleting ")

    (options, args) = parser.parse_args()
    

    if not (options.court and options.casenum):
       parser.print_help()
       exit()
    if options.action == "delete_documents" and not options.docrange:
       parser.print_help()
       exit()
    if options.action != "delete_documents":
       print "The only supported action right now is 'delete_documents'"
       exit()

    return (options, args)

def main():
    (options, args) = parse_args()

    court = options.court
    casenum = options.casenum

    if options.action == "delete_documents":
        documents = get_documents(court, casenum, options.docrange, options.show_warning)

        # Safety first! - put these in a different directory than our normal ones
        remove_docket.archive_docket_xml_locally(court, casenum, "backup_dockets")
        for document in documents:
          if document.available:
             remove_document.archive_document_locally(document, "backup_documents")

        
        status = delete_documents_from_docket(court, casenum, documents)

        if not status:
            print "IA Docket update did not succeed, exiting...."
            exit()
        
        print "not deleting items from IA - not setup to deal with large numbers of deletions"
        print "If this is a relatively small number of files, open this script and uncomment the lines below :"
        for document in documents:
            #print "    deleting document %s.%s from IA" % (document.docnum, document.subdocnum)
            #remove_document.delete_document_from_IA(document)
            document.delete()

if __name__ == '__main__':
    main()
