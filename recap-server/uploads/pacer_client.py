import re
import urllib2, urllib
import logging

from datetime import date


PACER_BASE_URL = "https://ecf.%s.uscourts.gov/"
PACER_CGI_URL = PACER_BASE_URL + "cgi-bin/"

class PacerClient():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self._opener = None

    def _get_request(self, request):
        """ We can handle errors in requests here """
        response = self._opener.open(request)
        if response.code != 200:
            logging.error('Error retreiving request %s' % request.get_full_url)
            return False
        return response

    def login_and_set_cookie(self, court='nysd'):
        """
        Log on to pacer and install the cookie into our opener. 
        This method currently defaults to logging into the nysd court,
        but the cookie should be valid for all courts.
        Returns True if the cookie is set correctly
        """
        # TODO: We only really need to get the cookie once every X minutes, maybe we should cache it
        if not self._opener:
            self._opener = urllib2.build_opener()
            response = self._get_request(self._build_login_request(court))
            cookie_header = self._parse_cookie_header_from_login_response(response.read())
            if not cookie_header:
                raise RuntimeError('No pacer cookie found')
            self._opener.addheaders = [('Cookie', cookie_header)]

        return True


    def get_opinions_html(self, court, start_date=date.today(), end_date=date.today()):
        """
        Get the written opinions report (WrtOpRpt.pl) for the given date range and court
        """
        self.login_and_set_cookie(court)

        # First get the magic number from the opinions report submit page
        req = self._build_basic_opinions_report_req(court)
        response = self._get_request(req)

        opinions_html = response.read()

        if self._has_security_violation_text(opinions_html):
            raise PacerPageNotAvailableException('Security violation text found instead of opinion page')

        magic_string = self._parse_magic_number_from_opinions_form(opinions_html)

        # Then, let's get hte actual report for the dates we are interested in 
        req = self._build_opinions_report_req(court, start_date, end_date, magic_string)
        response = self._get_request(req)

        return response.read()

    def get_pdf_show_doc(self, court, casenum, de_seq_num, dm_id, doc_num):
        """
        Download a pdf document using the 'show_doc.pl' syntax.
        """
        self.login_and_set_cookie(court)

        # First, get the show_doc page and parse it. We need the doc1 num
        req = self._build_show_doc_req(court, casenum, de_seq_num, dm_id, doc_num)
        response = self._get_request(req)
        docid = self._parse_docid_from_show_doc_page(response.read())

        # Then get the doc1 page, which contains an iframe to show_temp
        req = self._build_doc1_pdf_req(court, casenum, de_seq_num, docid)
        response = self._get_request(req)

        # Some courts will give us back a pdf at this point (njd for example)
        # other courts make us do a bit more parsing

        if self._is_pdf_response(response):
            return response.read()

        filename = self._parse_show_temp_filename_from_doc1_page(response.read())
        # Finally use the show_temp filename to actually get the pdf
        req = self._build_show_temp_req(court, filename) 

        #TK: pdfs may be large, maybe don't store as a string?
        response = self._get_request(req)
        return response.read()

    def _parse_cookie_header_from_login_response(self, response_html):
        """
        Pacer uses javascript to set the cookie after logging in, so we need to 
        scrape out the data we need to send as a cookie in subsequent requests
        """

        cookies = []

        m = re.search(r'PacerUser=\\"(.*)\\"', response_html)
        if m:
            cookies.append('PacerUser="%s"' % m.group(1))
        else:
            # some courts have PacerSession instead
            m = re.search(r'PacerSession=(.*); path', response_html)
            if m:
                cookies.append('PacerSession=%s' % m.group(1))
            else:
                # Give up!
                return None
                       
        cookies.extend(['PacerPref="receipt=Y"',
                        'PacerClient=""',
                        'ClientDesc=""',
                        'MENU=slow'])

        return "; ".join(cookies)

    def _parse_magic_number_from_opinions_form(self, opinion_report_html):
        m = re.search(r'WrtOpRpt.pl\?([-_0-9a-zA-Z]+)', opinion_report_html)
        return m.group(1)

    def _parse_docid_from_show_doc_page(self, show_doc_html):
        m = re.search(r'/doc1/(\d+)', show_doc_html)
        return m.group(1)

    def _parse_show_temp_filename_from_doc1_page(self, doc1_html):
        m = re.search(r'/show_temp.pl.*file=(.*)&', doc1_html)
        return m.group(1)

    def _build_login_request(self, court):
        post_params = {'login': self.username,
                       'key': self.password}
        params = urllib.urlencode(post_params)
        url = PACER_CGI_URL % court + "login.pl?logout"
        return urllib2.Request(url, params)

    def _build_basic_opinions_report_req(self, court):
        """
        In order to get the opinions report, we have to first grab a magic number
        from the WrtOpRpt page. So a general workflow to get an opinion report 
        would be to a) call this function to get a basic req, b) parse that req 
        for the magic number, c) call the more specific req builder passing in the 
        magic number
        """
        url = PACER_CGI_URL % court + "WrtOpRpt.pl"
        return urllib2.Request(url)

    def _build_opinions_report_req(self, court, start_date, end_date, magic_string):
        url = PACER_CGI_URL % court + "WrtOpRpt.pl?%s" % magic_string
        post_params = {'filed_from': start_date.strftime('%m/%d/%Y'),
                       'filed_to': end_date.strftime('%m/%d/%Y'),
                       'ShowFull': 1,
                       'Key1': 'de_date_filed'}
        params = urllib.urlencode(post_params)
        return urllib2.Request(url, params)

    def _build_show_doc_req(self, court, casenum, de_seq_num, dm_id, doc_num):
        url = PACER_CGI_URL % court 
        url += "show_doc.pl?caseid=%s&de_seq_num=%s&dm_id=%s&doc_num=%s" % (casenum, de_seq_num,\
                                                                            dm_id, doc_num)
        return urllib2.Request(url)
    
    def _build_doc1_pdf_req(self, court, casenum, de_seq_num, docid):
        # doc1 urls are just a little different, no cgi-bin
        url = PACER_BASE_URL % court + 'doc1/%s' % docid
        post_params = {'caseid': casenum, 
                       'de_seq_num': de_seq_num,
                       'got_receipt': 1,
                       'pdf_toggle_possible': 1}
        params = urllib.urlencode(post_params)
        return urllib2.Request(url, params)

    def _build_show_temp_req(self, court, filename):
        url = PACER_CGI_URL % court 
        url += "show_temp.pl?file=%s&type=application/pdf" % filename
        return urllib2.Request(url)

    def _is_pdf_response(self, response):
        return response.headers.getheader('content-type').find('application/pdf') >= 0

    def _has_security_violation_text(self, html):
        return html.find('Security violation: You do not have access rights to this program (WrtOpRpt.pl).') >= 0

class PacerClientException(Exception):
    '''
    Base exception for exceptions in this module
    '''
    pass

class PacerPageNotAvailableException(PacerClientException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

