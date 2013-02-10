
import re
import logging
import csv

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.utils import simplejson

from uploads.models import Document, Uploader, PickledPut
import InternetArchiveCommon as IACommon
import UploadHandler
import BucketLockManager
import DocumentManager
import ParsePacer
import datetime

def index(request):
    return HttpResponse("Well hello, there's nothing to see here.")

### File upload functions ###

def upload(request):
    """ Public upload view for all incoming data. """

    if request.method != "POST":
        message = "upload: Not a POST request."
        logging.error(message)
        return HttpResponse(message)

    try:
        if not request.FILES:
            message = "upload: No request.FILES attribute."
            logging.error(message)
            return HttpResponse(message)
    except IOError:
        # Not something we can fix I don't think.  Client fails to send data.
        message = "Client read error (Timeout?)"
        logging.warning("upload: %s" % message)
        return HttpResponse(message)
    except SystemError:
        message = "Could not parse POST arguments."
        logging.warning("uploads: %s" % message)
        return HttpResponse(message)

    try:
        data = request.FILES["data"]
    except KeyError:
        try:
            # TK: Only used in testing - get rid of me
            data = request.FILES["data_file"]
        except KeyError:
            message = "upload: No FILES 'data' attribute."
            logging.error(message)
            return HttpResponse(message)

    try:
        court = request.POST["court"]
    except KeyError:
        message = "upload: No POST 'court' attribute."
        logging.error(message)
        return HttpResponse(message)
    else:
        court = court.strip()

    if request.POST.get("casenum"):
        casenum_re = re.compile(r'\d+(-\d+)?')
        casenum = request.POST["casenum"].strip()
        if not casenum_re.match(casenum):
            message = "upload: 'casenum' invalid: %s" % \
                request.POST["casenum"]
            logging.error(message)
            return HttpResponse(message)
    else:
        casenum = None

    try:
        mimetype = request.POST["mimetype"].strip()
    except KeyError:
        message = "upload: No POST 'mimetype' attribute."
        logging.error(message)
        return HttpResponse(message)

    try:
        url = request.POST["url"].strip()
    except KeyError:
        url = None

    message = UploadHandler.handle_upload(data, court, casenum,
                                          mimetype, url)

    return HttpResponse(message)



def query(request):
    """  Query the database to check which PDF documents we have.

         The json input is {"court": <court>,
                            "urls": <list of PACER doc1 urls>}

         The json output is a set of mappings:
                           {<pacer url>: { "filename": <public url>,
                                           "timestamp": <last time seen> },
                            <pacer url>: ... }
    """

    response = {}

    if request.method != "POST":
        message = "query: Not a POST request."
        logging.error(message)
        return HttpResponse(message)

    try:
        jsonin = simplejson.loads(request.POST["json"])
    except KeyError:
        message = "query: no 'json' POST argument"
        logging.warning(message)
        return HttpResponse(message)
    except ValueError:
        message = "query: too many url args"
        logging.warning(message)
        return HttpResponse(message)
    except IOError:
        # Not something we can fix I don't think.  Client fails to send data.
        message = "query: Client read error (Timeout?)"
        logging.warning(message)
        return HttpResponse(message)

    try:
        court = jsonin["court"].strip()
    except KeyError:
        message = "query: missing json 'court' argument."
        logging.warning(message)
        return HttpResponse(message)

    try:
        urls = jsonin["urls"]
    except KeyError:
        message = "query: missing json 'urls' argument."
        logging.warning(message)
        return HttpResponse(message)

    for url in urls:

        # detect show_doc style document links
        sdre = re.search("show_doc\.pl\?(.*)",url)

        if sdre:
            argsstring = sdre.group(1)
            args = argsstring.split("&")
            argsdict = {}

            for arg in args:
                (key, val) = arg.split("=")
                argsdict[key] = val

            # maybe need to add some checks for whether
            # these vars exist in argsdict

            query = Document.objects.filter(court=court) \
                .filter(docnum=int(argsdict["doc_num"])) \
                .filter(casenum=int(argsdict["caseid"])) \
                .filter(dm_id=int(argsdict["dm_id"])) \
                .filter(available=1)

        else:
            # otherwise, assume it's a normal doc1 style url
            docid = UploadHandler.docid_from_url_name(url)
            query = Document.objects.filter(docid=docid) \
                .filter(available=1)


        if query:
            query = query[0]
            real_casenum = query.casenum
            if ParsePacer.is_appellate(court):
                real_casenum = ParsePacer.uncoerce_casenum(real_casenum)

            response[url] = {
                "filename": IACommon.get_pdf_url(court,
                                                 real_casenum,
                                                 query.docnum,
                                                 query.subdocnum),
                "timestamp": query.lastdate.strftime("%m/%d/%y")}


            if query.subdocnum == 0:

                subquery = Document.objects.filter(court=court,
                                                   casenum=query.casenum,
                                                   docnum=query.docnum,
                                                   available=1).exclude(
                                                   subdocnum=0)

                if len(subquery) > 0:
                    response[url]["subDocuments"] = {}

                    for subDoc in subquery:
                        real_sub_casenum = subDoc.casenum
                        if ParsePacer.is_appellate(court):
                            real_sub_casenum = ParsePacer.uncoerce_casenum(real_sub_casenum)
                        response[url]["subDocuments"][subDoc.subdocnum] = {
                                     "filename" : IACommon.get_pdf_url(court,
                                                              real_sub_casenum,
                                                              subDoc.docnum,
                                                              subDoc.subdocnum),
                                     "timestamp": subDoc.lastdate.strftime("%m/%d/%y")}


    jsonout = simplejson.dumps(response)

    return HttpResponse(jsonout, mimetype="application/json")

def query_cases(request):
    """  Query the database for the url of the html docket, if it exists

         The json input is {"court": <court>,
                            "casenum": <casenum>}

         The json output is
                           {"docket_url": <public url>,
                            "timestamp": <last time seen> }
    """

    response = {}

    if request.method != "POST":
        message = "query_cases: Not a POST request."
        logging.error(message)
        return HttpResponse(message)

    try:
        jsonin = simplejson.loads(request.POST["json"])
    except KeyError:
        message = "query_cases: no 'json' POST argument"
        logging.warning(message)
        return HttpResponse(message)
    except ValueError, err:
        message = "query_cases: %s." % unicode(err)
        logging.warning(message)
        return HttpResponse(message)
    except IOError:
        message = "query_cases: Client read error (Timeout?)"
        logging.warning(message)
        return HttpResponse(message)

    try:
        court = jsonin["court"].strip()
    except KeyError:
        message = "query_cases: missing json 'court' argument."
        logging.warning(message)
        return HttpResponse(message)

    try:
        casenum = unicode(int(jsonin["casenum"]))
    except ValueError:
        message = "query_cases: 'casenum' is not an integer: %s" % \
                                jsonin["casenum"]
        logging.warning(message)
        return HttpResponse(message)
    except:
        message = "query_cases: missing json 'casenum' argument."
        logging.warning(message)
        return HttpResponse(message)

    doc_query = Document.objects.filter(court=court) \
                  .filter(casenum=casenum) \
                  .order_by('-lastdate', '-modified')

    yesterday = datetime.datetime.now() - datetime.timedelta(1)

    old_or_avail_query = doc_query.filter(available=1) \
                         | doc_query.filter(modified__lte=yesterday)
    query = None
    try:
        query = old_or_avail_query[0]
    except IndexError:
        try:
            query = doc_query[0]
        except IndexError:
            query = None
        else:
            ppquery = PickledPut.objects.filter(filename=IACommon.get_docketxml_name(court, casenum))
            if len(ppquery) > 0:
                query = None



    if query:
        try:
            # we only have a last date for documents that have been uploaded
            date = query.lastdate.strftime("%m/%d/%y")
        except AttributeError:
            try:
                date = query.modified.strftime("%m/%d/%y")
          except AttributeError:
                date = "Unknown"

        response = {
                      "docket_url": IACommon.get_dockethtml_url(court,
                                                 casenum),
                      "timestamp": date}


    jsonout = simplejson.dumps(response)
    return HttpResponse(jsonout, mimetype="application/json")
                    #No documents exist, therefore no dockets exist



def adddocmeta(request):
    """ add metadata to Document table on our server. """

    if request.method != "POST":
        message = "adddocmeta: Not a POST request."
        logging.error(message)
        return HttpResponse(message)

    try:
        docid = request.POST["docid"].strip()
        court = request.POST["court"].strip()
        casenum = int(request.POST["casenum"])
        de_seq_num = int(request.POST["de_seq_num"])
        dm_id = int(request.POST["dm_id"])
        docnum = int(request.POST["docnum"])
        subdocnum = 0
    except KeyError, err:
        message = "adddocmeta: %s not specified." % unicode(err)
        logging.error(message)
        return HttpResponse(message)
    except ValueError, err:
        message = "adddocmeta: %s." % unicode(err)
        logging.error(message)
        return HttpResponse(message)

    # Necessary to preserve backwards compatibility with 0.6
    #  This param prevents tons of garbage from being printed to
    #  the error console after an Adddocmeta request
    try:
        add_case_info = request.POST["add_case_info"]
    except KeyError:
        add_case_info = None


    DocumentManager.handle_adddocmeta(docid, court, casenum, de_seq_num,
                                      dm_id, docnum, subdocnum)
    if add_case_info:
        response = {"documents": UploadHandler._get_documents_dict(court, casenum),
                  "message": "adddocmeta: DB updated for docid=%s" % (docid) }
        message = simplejson.dumps(response)
    else:
        message = "adddocmeta: DB updated for docid=%s" % (docid)

    return HttpResponse(message)

def lock(request):

    try:
        key = request.GET["key"].strip()
        court = request.GET["court"].strip()
        casenum = request.GET["casenum"].strip()
        one_per_uploader = 1 if request.GET.get('one_per_uploader') else 0
    except KeyError:
        # Fail.  Missing required arguments.
        return HttpResponse("0<br>Missing arguments.")

    authquery = Uploader.objects.filter(key=key)

    # Authenticate the uploader.
    try:
        uploader = authquery[0]
    except IndexError:
        # Fail. No auth key match.
        return HttpResponse("0<br>Authentication failed.")
    else:
        uploaderid = uploader.id

    # Try to grab the lock.
    lock_nonce, errmsg = BucketLockManager.get_lock(court, casenum,
                                                    uploaderid, one_per_uploader)

    if lock_nonce:
        return HttpResponse("1<br>%s" % lock_nonce)
    else:
        return HttpResponse("0<br>%s" % errmsg)


def unlock(request):

    try:
        key = request.GET["key"].strip()
        court = request.GET["court"].strip()
        casenum = request.GET["casenum"].strip()
        modified = bool(int(request.GET["modified"]))
        ignore_nonce = bool(int(request.GET["nononce"]))
    except KeyError:
        # Fail.  Missing required arguments.
        return HttpResponse("0<br>Missing arguments.")
    except ValueError:
        return HttpResponse("0<br>Invalid integer boolean for 'modified'.")

    authquery = Uploader.objects.filter(key=key)

    # Authenticate the uploader.
    try:
        uploader = authquery[0]
    except IndexError:
        # Fail. No auth key match.
        return HttpResponse("0<br>Authentication failed.")
    else:
        uploaderid = uploader.id


    dropped, errmsg = BucketLockManager.drop_lock(court, casenum, uploaderid,
                                                  modified=modified,
                                                  ignore_nonce = ignore_nonce)

    if dropped:
        return HttpResponse("1")
    else:
        return HttpResponse("0<br>%s" % errmsg)


def querylocks(request):

    try:
        key = request.GET["key"].strip()
    except KeyError:
        # Fail.  Missing required arguments.
        return HttpResponse("0<br>Missing arguments.")

    authquery = Uploader.objects.filter(key=key)

    # Authenticate the uploader.
    try:
        uploader = authquery[0]
    except IndexError:
        # Fail. No auth key match.
        return HttpResponse("0<br>Authentication failed.")
    else:
        uploaderid = uploader.id

    lock_triples = BucketLockManager.query_locks(uploaderid)

    pairs = ""
    numlocks = 0

    for (court, casenum, nonce) in lock_triples:
        pairs += "%s,%s,%s<br>" % (court, casenum, nonce)
        numlocks += 1

    return HttpResponse("%d<br>%s" % (numlocks, pairs))

def get_updated_cases(request):
    """
    This view is used by archive.recapthelaw.org to determine what dockets to download from IA
    """
    API_KEYS = (u'',)

    params = request.POST
    tpq = params.get('tpq', '')
    api_key = params.get('key', '')
    if not tpq or api_key not in API_KEYS:
        return HttpResponseForbidden()

    response = HttpResponse(mimetype='text/csv')
    tpq = float(tpq)
    tpq = datetime.datetime.fromtimestamp(tpq)
    docs = Document.objects.filter(lastdate__gt=tpq) | Document.objects.filter(modified__gt=tpq)
    urls = set()
    docs = docs.values('court', 'casenum')
    for doc in docs:
       urls.add((doc['court'], doc['casenum']))

    w = csv.writer(response)
    for url in urls:
        w.writerow(url)
    return response

def heartbeat(request):
    """
    This view is meant to be used for external monitoring, to ensure uptime
    """
    try:
        key = request.GET["key"].strip()
    except KeyError:
        # Fail.  Missing required arguments.
        return HttpResponseForbidden("403 Forbidden")

    if key != "REMOVED":
        return HttpResponseForbidden("403 Forbidden")

    query = Document.objects.filter(court='cand', casenum='215270')

    if query.count() >0:
        return HttpResponse("It's Alive!")
    else:
        return HttpResponseServerError("500 Server error: He's Dead Jim")
