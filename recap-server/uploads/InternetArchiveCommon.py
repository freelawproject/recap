
import urllib2
import socket

from recap_config import config

AUTH_HEADER = config["IA_S3_UPLOAD_KEY"]
STORAGE_URL = config["IA_STORAGE_URL"]
COLLECTION = config["IA_COLLECTION"]
BASE_DOWNLOAD_URL = "http://www.archive.org/download"

socket.setdefaulttimeout(60)

def get_bucketname(court, casenum):

    prefix = config["BUCKET_PREFIX"]
    bucketlist = ["gov", "uscourts", court, unicode(casenum)]
    if prefix:
        bucketlist.insert(0, prefix)

    #return "court-test-20"
    #return "NOBUCKET" # safeguard so nothing gets pushed to IA
    #return "court-test.gov.uscourts.mad.102407"
    return ".".join(bucketlist)

def get_pdfname(court, casenum, docnum, subdocnum):
    namelist = ["gov", "uscourts", court, unicode(casenum), 
                unicode(docnum), unicode(subdocnum), "pdf"]
    return ".".join(namelist)

def get_docketxml_url(court, casenum):
    bucketname = get_bucketname(court, casenum)
    docketname = get_docketxml_name(court, casenum)

    return "%s/%s/%s" % (BASE_DOWNLOAD_URL, bucketname, docketname)

def get_dockethtml_url(court, casenum):
    bucketname = get_bucketname(court, casenum)
    docketname = get_dockethtml_name(court, casenum)

    return "%s/%s/%s" % (BASE_DOWNLOAD_URL, bucketname, docketname)

def get_bucketcheck_url(court, casenum):
    bucketname = get_bucketname(court, casenum)
    return "%s/%s" % (STORAGE_URL, bucketname)

def get_pdf_url(court, casenum, docnum, subdocnum):
    bucketname = get_bucketname(court, casenum)
    filename = get_pdfname(court, casenum, docnum, subdocnum)

    return "%s/%s/%s" % (BASE_DOWNLOAD_URL, bucketname, filename)

def get_docketxml_name(court, casenum):
    namelist = ["gov", "uscourts", court, casenum, "docket.xml"]
    return ".".join(namelist)

def get_dockethtml_name(court, casenum):
    namelist = ["gov", "uscourts", court, casenum, "docket.html"]
    return ".".join(namelist)

def get_meta_from_filename(filename):
    namelist = filename.split(".")
    suffix = namelist.pop()
    meta = {}
    if suffix == "pdf":
        meta["subdocnum"] = namelist.pop()
        meta["docnum"] = namelist.pop()
        meta["casenum"] = namelist.pop()
        meta["court"] = namelist.pop()
    elif suffix == "xml":
        namelist.pop() # "docket"
        meta["casenum"] = namelist.pop()
        meta["court"] = namelist.pop()

    return meta

def _return_put():
    return 'PUT'

def _return_delete():
    return 'DELETE'

def _init_put(storage_path):
    
    request = urllib2.Request("%s/%s" % (STORAGE_URL, storage_path))

    request.add_header('authorization', AUTH_HEADER)
    request.add_header('x-archive-meta-collection', COLLECTION)
    request.add_header('x-archive-meta-mediatype', 'texts')
    request.add_header('x-archive-meta-language', 'eng')
#    request.add_header('x-archive-meta-noindex', 'true')
#    request.add_header('x-archive-meta-neverindex', 'true')        
    request.add_header('x-archive-queue-derive', '0')
    # Don't use a lambda function here-- it's not pickleable.
    request.get_method = _return_put

    return request

def _init_delete(storage_path):
    request = urllib2.Request("%s/%s" % (STORAGE_URL, storage_path))
    request.add_header('authorization', AUTH_HEADER)
    request.get_method = _return_delete

    return request


def make_pdf_request(filebits, court, casenum, docnum, subdocnum, metadict, makenew=False):

    bucketname = get_bucketname(court, casenum)
    filename = get_pdfname(court, casenum, docnum, subdocnum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_put(storage_path)
    
    # Add the payload
    request.add_data(filebits)

    # Make sure the metadict has all of the metadata
    metadict["court"] = court
    metadict["pacer_case_num"] = casenum
    metadict["doc_num"] = docnum
    metadict["attachment_num"] = subdocnum
    
    if makenew:
        request.add_header('x-archive-auto-make-bucket', '1')
        add_description_header(request, court, casenum)

    # Add the HTTP meta headers
    for k,v in metadict.items():
        try:
            v = v.encode("ascii", "replace")
        except AttributeError:
            # if v is not a string, just pass through as usual.
            pass
        request.add_header('x-archive-meta-%s' % k, v)

    return request

def make_pdf_delete_request(court, casenum, docnum, subdocnum):

    bucketname = get_bucketname(court, casenum)
    filename = get_pdfname(court, casenum, docnum, subdocnum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_delete(storage_path)
    request.add_header('x-archive-cascade-delete', '1')

    return request

def make_docketxml_delete_request(court, casenum):

    bucketname = get_bucketname(court, casenum)
    filename = get_docketxml_name(court, casenum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_delete(storage_path)
    request.add_header('x-archive-cascade-delete', '1')

    return request

def make_dockethtml_delete_request(court, casenum):

    bucketname = get_bucketname(court, casenum)
    filename = get_dockethtml_name(court, casenum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_delete(storage_path)
    request.add_header('x-archive-cascade-delete', '1')

    return request

def make_docketxml_request(docketbits, court, casenum, metadict={}, makenew=0):
    """  """

    bucketname = get_bucketname(court, casenum)
    filename = get_docketxml_name(court, casenum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_put(storage_path)

    if makenew:
        request.add_header('x-archive-auto-make-bucket', '1')
        add_description_header(request, court, casenum)
    
    for k,v in metadict.items():
        try:
            v = v.encode("ascii", "replace")
        except AttributeError:
            # if v is not a string, just pass through as usual.
            pass

        request.add_header('x-archive-meta-%s' % k, v)

    # add the payload
    request.add_data(docketbits)
    
    return request

def make_dockethtml_request(docketbits, court, casenum, metadict={}):

    bucketname = get_bucketname(court, casenum)
    filename = get_dockethtml_name(court, casenum)

    storage_path = "%s/%s" % (bucketname, filename)
    request = _init_put(storage_path)
    
    for k,v in metadict.items():
        try:
            v = v.encode("ascii", "replace")
        except AttributeError:
            # if v is not a string, just pass through as usual.
            pass

        request.add_header('x-archive-meta-%s' % k, v)

    # add the payload
    request.add_data(docketbits)

    return request
    
def make_bucket_request(court, casenum, metadict={}, makenew=0):
    """ Make an new Internet Archive bucket. """

    # The storage_path is just the bucketname
    bucketname = get_bucketname(court, casenum)
    request = _init_put(bucketname)

    if makenew:
        request.add_header('x-archive-auto-make-bucket', '1')
	request.add_header('content-length', '0')
    else:
        request.add_header('x-archive-ignore-preexisting-bucket', '1')

    add_description_header(request, court, casenum)

    for k,v in metadict.items():
        try:
            v = v.encode("ascii", "replace")
        except AttributeError:
            # if v is not a string, just pass through as usual.
            pass

        request.add_header('x-archive-meta-%s' % k, v)

    return request


def make_casemeta_request(court, casenum, metadict={}):
    ''' Return a Request for replacing the case metadata '''
    
    return make_bucket_request(court, casenum, metadict)


def add_description_header(request, court, casenum):

    url = get_dockethtml_url(court, casenum)

    description = '<a href="%s">Click here</a> to see available docket information and document downloads for this case.  If you need the complete docket, you should consult PACER directly.' % url

    request.add_header('x-archive-meta-description', description)

if __name__ == "__main__":

    request = urllib2.Request("http://monocle.princeton.edu")
    add_description_header(request, "mad", "123456")

    #print request.headers
    #print make_casemeta_request("asdf", "123454").headers
    #print make_docketxml_request("", "asdf", "123455", makenew=1).headers
