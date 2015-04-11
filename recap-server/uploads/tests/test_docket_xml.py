import unittest
from uploads.DocketXML import DocketXML
from uploads.DocketXML import parse_xml_string
from uploads.models import Document 

""" Tests for DocketXml object
    Note that merge_docket tests are found in alltests.py
    We probably should refactor those out of that test file
    at some point"""
class TestDocketXml(unittest.TestCase):

    def setUp(self):
        self.doc_xml = DocketXML('test_court', '1234')

    
    def test_object_creation(self):
        self.assertEquals('test_court', self.doc_xml.get_court())
        self.assertEquals('1234', self.doc_xml.get_casenum())
        self.assertEquals([], self.doc_xml.parties)
        self.assertEquals({}, self.doc_xml.documents)
        self.assertFalse(self.doc_xml.nonce == None)

    def test_add_document(self):
        meta_dict = {'test_key': 'test_value'}
        self.doc_xml.add_document('1', '2', meta_dict)
        docs = self.doc_xml.documents

        self.assertEquals(['1-2'], docs.keys())

        meta_dict['doc_num'] = '1'
        meta_dict['attachment_num'] = '2'
        self.assertEquals(meta_dict, docs['1-2'])
    
    def test_add_document_object(self):
        d1 = Document(court='nysd', casenum='1234', 
                      docnum='2', subdocnum='3',
                      de_seq_num='20', dm_id='12',
                      docid='789',
                      sha1='hash', available='1', 
                      free_import=1,
                      lastdate='lastdate', modified='1')

        expected_dict = {'doc_num': '2', 'attachment_num': '3',
                         'pacer_doc_id': '789', 
                         'pacer_de_seq_num': '20',
                         'pacer_dm_id': '12',
                         'upload_date': 'lastdate',
                         'available': '1',
                         'free_import': '1',
                         'sha1': 'hash'}

        self.doc_xml.add_document_object(d1)
        actual_dict = self.doc_xml.get_document_metadict('2','3')
        self.assertEquals(expected_dict, actual_dict)

    def test_set_document_available(self):
        meta_dict = {'test_key': 'test_value'}
        self.doc_xml.add_document('1', '2', meta_dict)
        self.doc_xml.set_document_available('1', '2', '0')
        doc_dict = self.doc_xml.get_document_metadict('1','2')
        self.assertEquals("0", doc_dict['available'])
    
    def test_set_document_available_no_preexiting_document(self):
        self.doc_xml.set_document_available('1', '2', '0')
        doc_dict = self.doc_xml.get_document_metadict('1','2')
        self.assertEquals("0", doc_dict['available'])
    
    def test_get_document_sha1(self):
        meta_dict = {'sha1': 'sha1test'}
        self.doc_xml.add_document('1', '2', meta_dict)
        actual_sha1 = self.doc_xml.get_document_sha1('1', '2')
        self.assertEquals('sha1test', actual_sha1)
    
    def test_remove_document(self):
        self.doc_xml.add_document('1', '2')
        self.doc_xml.remove_document('1', '2')
        self.assertEquals({}, self.doc_xml.documents)

    def test_add_party(self):
        party = {'name': 'Dhruv'}
        self.doc_xml.add_party(party)
        self.assertEquals([party], self.doc_xml.parties)

    def test_update_parties_simple(self):
        party_list= [{'name': 'Dhruv'}]

        #Test updates when no pre-existing parties
        self.doc_xml.update_parties(party_list)
        self.assertEquals(party_list, self.doc_xml.parties)

        # Test that equivalent updates change nothing
        self.doc_xml.update_parties(party_list)
        self.assertEquals(party_list, self.doc_xml.parties)
    
    def test_update_parties_same_name(self):
        party = {'name': 'Dhruv'}
        self.doc_xml.add_party(party)
        party_update = {'name': 'Dhruv', 'phone': '1234'}

        self.doc_xml.update_parties([party_update])

        self.assertEquals([party_update], self.doc_xml.parties)
    
    def test_update_parties_different_name(self):
        party = {'name': 'Dhruv'}
        self.doc_xml.add_party(party)
        party_update = {'name': 'Harlan', 'phone': '1234'}

        self.doc_xml.update_parties([party_update])

        self.assertEquals([party, party_update], self.doc_xml.parties)

    def test_update_case(self):
        new_casemeta = {'Nature of Suit': 'Something'}
        self.doc_xml.update_case(new_casemeta)
        new_casemeta['pacer_case_num'] = '1234'
        new_casemeta['court'] = 'test_court'
        self.assertEquals(new_casemeta, self.doc_xml.casemeta)

    def test_get_root(self):
        # TODO: there's a lot of logic in this method, but
        #       testing it is overkill for now
        #       we should refactor it to make it easier to test

        xml_obj = self.doc_xml.get_root()
        self.assertFalse(xml_obj == None)

    def test_to_xml(self):
        # TODO: better test here (after refactoring get_root)
        meta_dict = {'free_import': 1}
        self.doc_xml.add_document('1', '2', meta_dict)
        xml_text = self.doc_xml.to_xml()
        self.assertFalse(xml_text == None)
        self.assertTrue(xml_text.find('free_import') > 0)
    
    def test_to_html(self):
        # TODO: better test here (after refactoring get_root)
        html_text = self.doc_xml.to_html()
        self.assertFalse(html_text == None)

    def test_parse_xml_string(self):
        meta_dict = {'free_import': 1}
        self.doc_xml.add_document('1', '2', meta_dict)
        xml_text = self.doc_xml.to_xml()
        parsed_docket, msg = parse_xml_string(xml_text)

        self.assertEquals(1, len(parsed_docket.documents))
        self.assertEquals('1', parsed_docket.documents['1-2']['free_import'])
