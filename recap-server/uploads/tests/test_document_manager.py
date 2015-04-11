import unittest
from datetime import datetime
from uploads.models import Document
from uploads.DocketXML import DocketXML
from uploads import DocumentManager

#TODO: This doesn't test the entirety of documentmanager
class TestDocumentManager(unittest.TestCase):

    def setUp(self):
        self.doc_xml = DocketXML('nysd', '1234')
        self.doc_xml.add_document('1', '2')

    def tearDown(self):
        Document.objects.all().delete()

    def test_update_local_db_basic(self):
        DocumentManager.update_local_db(self.doc_xml)
        created_doc = Document.objects.all()[0]

        self.assertEquals(1, Document.objects.count())
        self.assertEquals('nysd', created_doc.court)
        self.assertEquals(1234, created_doc.casenum)
        self.assertEquals(1, created_doc.docnum)
        self.assertEquals(2, created_doc.subdocnum)
    
    def test_update_local_db_updates_existing(self):
        d1 = Document(court='nysd', casenum='1234', docnum='1', subdocnum='2')
        d1.save()
        self.assertEquals(1, Document.objects.count())

        doc_meta = self.doc_xml.get_document_metadict('1', '2')
        doc_meta['pacer_doc_id'] = '12'

        DocumentManager.update_local_db(self.doc_xml)
        created_doc = Document.objects.all()[0]
        self.assertEquals(1, Document.objects.count())
        self.assertEquals('12', created_doc.docid)
    
    def test_update_local_db_doesnt_overwrite_local(self):
        d1 = Document(court='nysd', casenum='1234', 
                      docnum='1', subdocnum='2',
                      docid='120')
        d1.save()
        self.assertEquals(1, Document.objects.count())

        # This document doesn't have docid, but we shouldn't overwrite
        DocumentManager.update_local_db(self.doc_xml)

        created_doc = Document.objects.all()[0]
        self.assertEquals(1, Document.objects.count())
        self.assertEquals('120', created_doc.docid)

    def test_update_local_db_translates_opt_fields_correctly(self):
        i_dict = {'doc_num': '2', 'attachment_num': '3',
                         'pacer_doc_id': '789', 
                         'pacer_de_seq_num': '20',
                         'pacer_dm_id': '12',
                         'upload_date': '2007-12-25',
                         'free_import': 1,
                         'sha1': 'hash'}

        self.doc_xml.remove_document('1', '2')
        self.doc_xml.add_document('2', '3', i_dict)
        DocumentManager.update_local_db(self.doc_xml)
        self.assertEquals(1, Document.objects.count())
        created_doc = Document.objects.all()[0]
        self.assertEquals(int(i_dict['doc_num']), created_doc.docnum)
        self.assertEquals(int(i_dict['attachment_num']), created_doc.subdocnum)
        self.assertEquals(i_dict['pacer_doc_id'], created_doc.docid)
        self.assertEquals(int(i_dict['pacer_de_seq_num']), created_doc.de_seq_num)
        self.assertEquals(int(i_dict['pacer_dm_id']), created_doc.dm_id)
        self.assertEquals(i_dict['sha1'], created_doc.sha1)
        expected_upload_date = datetime.strptime(i_dict['upload_date'], 
                                                "%Y-%m-%d")
        self.assertEquals(expected_upload_date, created_doc.lastdate)
        self.assertEquals(int(i_dict['free_import']), created_doc.free_import)

    
    def test_update_local_db_ignore_available(self):
        doc_meta = self.doc_xml.get_document_metadict('1', '2')
        doc_meta['available'] = '1'
        
        DocumentManager.update_local_db(self.doc_xml)
        created_doc = Document.objects.all()[0]
        self.assertEquals(0, created_doc.available)
        
        DocumentManager.update_local_db(self.doc_xml, ignore_available=0)
        created_doc = Document.objects.all()[0]
        self.assertEquals(1, created_doc.available)
