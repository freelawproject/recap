from __future__ import with_statement
import os
import unittest
import re
from datetime import date
from mock import Mock
import cPickle as pickle

from test_constants import TEST_OPINION_PATH, TEST_PDF_PATH
import uploads.ParsePacer as PP

from django.conf import settings as config
from uploads.opinions_downloader import OpinionsDownloader

PACER_USERNAME = config.PACER_USERNAME
PACER_PASSWORD = config.PACER_PASSWORD

""" This is currently not fuctional, just here so that I can think about interfaces to this opinions downloader thingy - DK"""
class TestOpinionsDownloader(unittest.TestCase):
    downloader = None

    def setUp(self):
        if self.downloader == None:
            self.__class__.downloader= OpinionsDownloader(username=PACER_USERNAME, password=PACER_PASSWORD)

    def test_download_opinion_dockets(self):
        test_date = date(2011, 06, 17)
        
        opinion_dockets = self.downloader.get_opinions(court='nysd',
                                                       start_date = test_date,
                                                       end_date = test_date)
        
        self.assertEquals(2, len(opinion_dockets))

    def test_enqueue_opinions(self):
        test_date = date(2011, 06, 17)
        expected_html = open(TEST_OPINION_PATH + "nysd.2011_06_17.opinions.html").read()
        expected_dockets = PP.parse_opinions(expected_html, 'nysd')
        
        expected_pdf_bits = open(TEST_PDF_PATH + 'gov.uscourts.nysd.351385.14.0.pdf').read()

        # Set up the test environment 
        # monkey patch out dependencies on pacer and rabbitmq
        self.downloader.get_opinions = Mock(return_value=expected_dockets)
        self.downloader.get_document = Mock(return_value=expected_pdf_bits)
        self.downloader.channel.basic_publish = mock_publish_call = Mock()

        self.downloader.enqueue_opinions('nysd', test_date, test_date)
        self.assertEquals(2, mock_publish_call.call_count)
        
        messages = [pickle.loads(args[1]['body']) \
                        for args in mock_publish_call.call_args_list]

        filenames = [m['docket_filename'] for m in messages]
        
        document_maps = [m['docnums_to_filename'] for m in messages]
                        
        #print filenames
        for filename in filenames:
            with open(filename) as f:
                self.assertTrue(f.read() != None)
            # cleanup
            os.unlink(filename)

        for docmap in document_maps:
            self.assertEquals(1, len(docmap))
            self.assertTrue(re.match(r'\d+-0', docmap.keys()[0]))
