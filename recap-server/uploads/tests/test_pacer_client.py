import unittest 
import urllib2
from datetime import date

from test_constants import TEST_SUPPORT_PATH, TEST_OPINION_PATH, TEST_PDF_PATH, TEST_DOC1_PATH
from uploads.recap_config import config
from uploads.pacer_client import PacerClient, PacerPageNotAvailableException
import uploads.ParsePacer as PP

import pdb

PACER_USERNAME = config['PACER_USERNAME']
PACER_PASSWORD = config['PACER_PASSWORD']

class TestPacerClient(unittest.TestCase):
    def setUp(self):
        # we need to create a pacer client each time, since some courts have a different login
        self.pacer_client = PacerClient(username=PACER_USERNAME, password=PACER_PASSWORD)
    
    def test_pacer_client_creation(self):
        self.pacer_client.username = PACER_USERNAME
        self.pacer_client.password = PACER_PASSWORD


    def test_login_and_set_cookie(self):
        success = self.pacer_client.login_and_set_cookie()
        self.assertFalse(self.pacer_client._opener == None)
        self.assertTrue(self.pacer_client._opener.addheaders[0][0] == 'Cookie')
        self.assertTrue(success)

    def test_login_and_set_cookie_failures(self):
        bad_pacer_client = PacerClient(username='test', password='badpass')
        self.assertRaises(RuntimeError, bad_pacer_client.login_and_set_cookie)

    def test_download_opinions(self):
        #TODO: Change this test to only use html tests.
        # Pacer client tests shouldn't depend on parse pacer
        test_date = date(2011, 06, 17)
        
        expected_html = open(TEST_OPINION_PATH + "nysd.2011_06_17.opinions.html").read()
        expected_dockets = PP.parse_opinions(expected_html, 'nysd')

        opinions_html = self.pacer_client.get_opinions_html(court='nysd',
                                                       start_date = test_date,
                                                       end_date = test_date)

        dockets = PP.parse_opinions(opinions_html, 'nysd')

        self.assertEquals(len(expected_dockets), len(dockets))

        for d in dockets:
            self.assertTrue(d.get_casenum() in [e.get_casenum() for e in expected_dockets])
            casemeta = d.get_casemeta()
            self.assertTrue(casemeta['case_name'] in [e.get_casemeta()['case_name'] 
                                                            for e in expected_dockets])

    def test_opinion_html_download_fails_security_exception(self):
        self.assertRaises(PacerPageNotAvailableException, self.pacer_client.get_opinions_html, 'iasd')
    
    def test_parse_cookies_from_login_response(self):
        response_html = open(TEST_SUPPORT_PATH + "nysd.login_response.html").read()
        pacer_cookie_header = self.pacer_client._parse_cookie_header_from_login_response(response_html)
        #PacerUser is really the only thing we care about
        expected_header='PacerUser="pc357201308498844                                REMOVED"; PacerPref="receipt=Y"; PacerClient=""; ClientDesc=""; MENU=slow'
        
        self.assertEquals(expected_header, pacer_cookie_header)
        
    def test_parse_cookies_from_alnd_login_response(self):
        response_html = open(TEST_SUPPORT_PATH + "alnd.login_response.html").read()
        pacer_cookie_header = self.pacer_client._parse_cookie_header_from_login_response(response_html)

        # Some courts care about this PacerSession thing.
        expected_header='PacerSession=REMOVED; PacerPref="receipt=Y"; PacerClient=""; ClientDesc=""; MENU=slow'
        self.assertEquals(expected_header, pacer_cookie_header)

    def test_parse_cookies_from_bad_login_response(self):
        pacer_cookie_header = self.pacer_client._parse_cookie_header_from_login_response("")
        self.assertEquals(None, pacer_cookie_header)
    
    def test_download_show_doc_pdf_no_iframe(self):
        '''
        Some courts have a slightly different workflow on the show doc page - they don't have an iframe
        '''
        court = 'njd'; casenum = '224278'; doc_num = 21 
        de_seq_num = '59'
        dm_id = '5368016'

        response_pdf_bits = self.pacer_client.get_pdf_show_doc(court, casenum, de_seq_num, dm_id, doc_num)
        expected_pdf_bits = open(TEST_PDF_PATH + 'gov.uscourts.njd.224278.21.0.pdf').read()
        self.assertEquals(expected_pdf_bits, response_pdf_bits)
        
   
    def test_download_show_doc_pdf(self):
        court = 'nysd'; casenum = '351385'; doc_num = 14
        de_seq_num = '65'
        dm_id = '8714323'

        response_pdf_bits = self.pacer_client.get_pdf_show_doc(court, casenum, de_seq_num, dm_id, doc_num)
        expected_pdf_bits = open(TEST_PDF_PATH + 'gov.uscourts.nysd.351385.14.0.pdf').read()
        self.assertEquals(expected_pdf_bits, response_pdf_bits)


    def test_parse_docid_from_show_doc_page(self):
        show_doc_html = open(TEST_DOC1_PATH + "ecf.cand.uscourts.gov.03517852828").read()
        docid = self.pacer_client._parse_docid_from_show_doc_page(show_doc_html)
        self.assertEquals('03517852828', docid)
    
    def test_parse_show_temp_filename_from_doc1_page(self):
        doc1_html = open(TEST_DOC1_PATH + "ecf.nysd.uscourts.gov.12719373604").read()
        docid = self.pacer_client._parse_show_temp_filename_from_doc1_page(doc1_html)
        self.assertEquals('8742096-0--513.pdf', docid)

    def test_parse_magic_number_from_opinions_form(self):
        sample_html = '''<FORM ENCTYPE='multipart/form-data' method=POST action="/cgi-bin/WrtOpRpt.pl?677835669591644-L_819_0-1" >'''
        magic_number = self.pacer_client._parse_magic_number_from_opinions_form(sample_html)
        self.assertEquals("677835669591644-L_819_0-1", magic_number)
