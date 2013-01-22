from __future__ import with_statement
import unittest
import urllib2
import re
import time

from uploads.DocketXML import DocketXML
from uploads import ia_uploader

from mock import Mock, patch

class TestIAUploader(unittest.TestCase):
    """ This class would replace the adhoc do_me_up steps we have in various places (actual recap uploader (eventually), batch uploaders """
    def setUp(self):
        mock_response = Mock(file)
        setattr(mock_response,'code', 200)
        self.mock_open = Mock(return_value=mock_response)
        # Monkey patch
        ia_uploader.opener.open = self.mock_open

        self.upload_message = {'docket_filename': 'fake filename',
                               'court': 'nysd',
                               'casenum': '1234'}

        self.docmap = {'1-0' : 'Fake document filename'}

    def test_should_delay_message(self):
        message = {}
        self.assertFalse(ia_uploader._should_delay_message(message))
        message['next_attempt_time'] = time.time() - 9001
        self.assertFalse(ia_uploader._should_delay_message(message))
        message['next_attempt_time'] = time.time() +  9001
        self.assertTrue(ia_uploader._should_delay_message(message))

    def test_requeue_message(self):
        mock_channel = Mock()
        # First make sure that it doesn't requeue after too many attempts
        message = {}
        message['court'] = 'nysd'
        message['casenum'] = '1234'
        message['attempt_num'] = 15
        message['next_attempt_time'] = 200

        success = ia_uploader._requeue_message(mock_channel, message)
        self.assertFalse(success)
        self.assertEquals(0, len(mock_channel.method_calls))
        
        message['attempt_num'] = 1
        
        success = ia_uploader._requeue_message(mock_channel, message)
        self.assertTrue(success)
        self.assertEquals(1, len(mock_channel.method_calls))

    def test_requeue_message_no_previous_retries(self):
        mock_channel = Mock()
        message = {}
        message['court'] = 'nysd'
        message['casenum'] = '1234'
        success = ia_uploader._requeue_message(mock_channel, message)
        self.assertTrue(success)
        self.assertEquals(1, message['attempt_num'])

    @patch('uploads.ia_uploader._lock', Mock(return_value=(True, 'nonce')))
    @patch('uploads.ia_uploader._unlock', Mock(return_value=(True, None)))
    @patch('uploads.ia_uploader._handle_message', Mock(return_value=(True, "message")))
    @patch('uploads.ia_uploader._cleanup_successful_message', Mock())
    def test_lock_and_handle_message_success_case(self):
        success = ia_uploader.lock_and_handle_message(self.upload_message)
        self.assertTrue(success)
        self.assertEquals(1, ia_uploader._lock.call_count)
        self.assertEquals(1, ia_uploader._unlock.call_count)
        self.assertEquals(1, ia_uploader._cleanup_successful_message.call_count)
    
    @patch('uploads.ia_uploader._lock', Mock(return_value=(True, 'nonce')))
    @patch('uploads.ia_uploader._unlock', Mock(return_value=(True, None)))
    @patch('uploads.ia_uploader._handle_message', Mock(return_value=(True, "Unmodified")))
    @patch('uploads.ia_uploader._cleanup_successful_message', Mock())
    def test_lock_and_handle_message_unmodified_case(self):
        success = ia_uploader.lock_and_handle_message(self.upload_message)
        self.assertEquals(0, ia_uploader._unlock.call_args[1]['modified'])
    
    @patch('uploads.ia_uploader._unpickle_object', Mock(return_value=DocketXML('nysd', '1234')))
    @patch('uploads.ia_uploader.upload_docket', Mock(return_value=(True, 'message')))
    def test_handle_message_success_case_docket(self):
        success, msg = ia_uploader._handle_message(self.upload_message, 'nonce')
        self.assertTrue(success)
        self.assertEquals(msg, 'message')
    
    @patch('uploads.ia_uploader._unpickle_object', Mock(return_value=DocketXML('nysd', '1234')))
    @patch('uploads.ia_uploader.upload_docket', Mock(return_value=(True, 'message')))
    @patch('uploads.ia_uploader._upload_documents', Mock(return_value=(True, 'message')))
    def test_handle_message_success_case_docket(self):
        self.upload_message['docnums_to_filename'] = self.docmap
        success, msg = ia_uploader._handle_message(self.upload_message, 'nonce')
        self.assertTrue(success)
        self.assertEquals(msg, 'message')

    def test_upload_docket_does_nothing_if_no_differences(self):
        # Given a docketxml object, upload the docket, 
        # by downloading, merging and uploading
        same_docket = DocketXML('nysd', '1234')
        with patch('uploads.ia_uploader._get_docket_from_IA', 
                    Mock(return_value=(same_docket, None))):
            success, msg = ia_uploader.upload_docket(same_docket, None)

        self.assertTrue(success)
        self.assertEquals(msg, 'Unmodified')
    
    @patch('uploads.ia_uploader._get_docket_from_IA', Mock(return_value=(None, None)))
    def test_upload_docket_no_existing_IA_docket(self):
        docket = DocketXML('nysd', '1234')
        success, msg = ia_uploader.upload_docket(docket, None)
        self.assertTrue(success)
        # docket upload and html docket upload
        self.assertEquals(2, self.mock_open.call_count)
        docket_url = self.mock_open.call_args_list[0][0][0].get_full_url()
        html_url = self.mock_open.call_args_list[1][0][0].get_full_url()
        self.assertTrue(docket_url.find('gov.uscourts.nysd.1234.docket.xml') > 0)
        self.assertTrue(html_url.find('gov.uscourts.nysd.1234.docket.html') > 0)

    @patch('uploads.ia_uploader._split_lock_message', Mock(return_value=(1,1)))
    def test_lock(self):
        ia_uploader._lock('nysd', '1234')
        self.assertEquals(1, self.mock_open.call_count)
        url = self.mock_open.call_args[0][0].get_full_url()
        self.assertTrue(url.find('recap/lock/?casenum=1234&court=nysd&key=authkey') > 0)
    
    @patch('uploads.ia_uploader._split_lock_message', Mock(return_value=(1,1)))
    def test_unlock_modified(self):
        ia_uploader._unlock('nysd', '1234')
        self.assertEquals(1, self.mock_open.call_count)
        url = self.mock_open.call_args[0][0].get_full_url()
        self.assertTrue(url.find('recap/unlock/?casenum=1234&court=nysd&modified=1&key=authkey&nononce=0') > 0)


    @patch('uploads.ia_uploader._unpickle_object', Mock(return_value="documentfilebits"))
    @patch('uploads.ia_uploader.upload_document', Mock(return_value=(True, 'message')))
    def test_upload_document_success(self):
        docket = DocketXML('nysd', '1234')
        docnum, subdocnum = self.docmap.keys()[0].split('-')
        docket.add_document(docnum, subdocnum)
        # Sanity Check
        self.assertFalse(docket.get_document_metadict(docnum, subdocnum).get('available'))

        success, msg = ia_uploader._upload_documents(docket, self.docmap)
        self.assertTrue(success)
        self.assertEquals("1", docket.get_document_metadict(docnum, subdocnum)['available'])
        #sha1 of "documentfilebits"
        self.assertEquals("0fff5bc4b311d46f0bad0c840a59ec6859276265",
                          docket.get_document_metadict(docnum, subdocnum)['sha1'])
    
    @patch('uploads.ia_uploader._unpickle_object', Mock(return_value="documentfilebits"))
    @patch('uploads.ia_uploader.upload_document', Mock(return_value=(False, 'message')))
    def test_upload_document_failure(self):
        docket = DocketXML('nysd', '1234')
        docnum, subdocnum = self.docmap.keys()[0].split('-')
        docket.add_document(docnum, subdocnum)
        # Sanity Check
        self.assertFalse(docket.get_document_metadict(docnum, subdocnum).get('available'))

        success, msg = ia_uploader._upload_documents(docket, self.docmap)
        self.assertFalse(success)
        self.assertEquals("0", docket.get_document_metadict(docnum, subdocnum)['available'])

    def test_merge_docket_with_IA_docket(self):
        pass
    
    def test_download_docket_from_IA(self):
        pass
