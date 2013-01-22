from uploads.BeautifulSoup import BeautifulSoup,HTMLParseError, Tag, NavigableString
import uploads.ParsePacer as PP
import uploads.DocketXML as DocketXML
import re, os
from lxml import etree

from mock import patch, Mock

from django.test.client import Client
from django.utils import simplejson

from uploads.models import Document, Uploader, BucketLock, PickledPut
import uploads.InternetArchiveCommon as IACommon
import uploads.InternetArchive as IA

import unittest
import datetime
import time

from test_constants import TEST_SUPPORT_PATH, TEST_OPINION_PATH, TEST_DOC1_PATH

TEST_DOCKET_PATH  = TEST_SUPPORT_PATH + "testdockets/"
TEST_DOCUMENT_PATH = TEST_SUPPORT_PATH + "testdocuments/"
BANK_TEST_DOCKET_PATH = TEST_DOCKET_PATH + "bankruptcydockets/"

TEST_DOCKET_LIST = ["cacd", "deb", "almb", "almd", "alsd", "cit", "cit2", "cit7830", "cit7391", "cand", "cand2", "cand3", "caed", "ded", "flsb", "txed"] #akd doesn't parse

class TestParsePacer(unittest.TestCase):
  def setUp(self):
      pass


  def test_docket_output(self):
    docket_list = ["nysd.39589.html"]
    
    for filename in docket_list:
      court, casenum = filename.split(".")[:2]
      f = open("/".join([TEST_DOCKET_PATH, filename]))
      filebits = f.read()
      
      docket = PP.parse_dktrpt(filebits, court, casenum)

      docket_xml = docket.to_xml()
    
  def test_parse_dktrpt(self):
    test_dockets = ['mieb.600286.html']

    for filename in test_dockets:
      court, casenum = filename.split(".")[:2]
      f = open("/".join([BANK_TEST_DOCKET_PATH, filename]))
      filebits = f.read()
      
      docket = PP.parse_dktrpt(filebits, court, casenum)
    

  def test_all_bankruptcy_dockets_for_case_metadata(self):
    count =0
    no_assigned_to_dockets = ['njb.764045.html', 'flmb.923870.html']

    unknown_cases= []
    no_date_filed = []

    for filename in os.listdir(BANK_TEST_DOCKET_PATH):
       soup = _open_soup("/".join([BANK_TEST_DOCKET_PATH, filename]))

       court, casenum = filename.split(".")[:2]
       case_data = PP._get_case_metadata_from_dktrpt(soup, court)
	    
       try:
           print count, filename, court, casenum, case_data["docket_num"], case_data["case_name"],"::", case_data["assigned_to"]
       except KeyError:
	  pass
	    
       #self.assertTrue("date_case_filed" in case_data)
       self.assertTrue("docket_num" in case_data)
       self.assertTrue("case_name" in case_data)
       self.assertTrue("date_case_filed" in case_data)

       if filename not in no_assigned_to_dockets:
	    self.assertTrue("assigned_to" in case_data)
	    
       if "date_case_filed" not in case_data:
            no_date_filed.append(filename)

       if case_data["case_name"] == "Unknown Bankruptcy Case Title":
            unknown_cases.append( (filename, case_data["case_name"]))

       count+=1

    print "No Date filed:"
    for filename in no_date_filed:
	    print filename
	    
    print "\nUnknown casename cases:"
    for filename, name in unknown_cases:
       print filename, name
#	    self.assertNotEquals(case_data["case_name"],"Unknown Bankruptcy Case Title")

  def test_merge_dockets(self):
    no_parties_path = TEST_DOCKET_PATH + "noPartiesXML/"
    no_parties_list = ["cit7830", "cit7391", "caedSomeParties", "candSomeAttys"]
    no_parties_filebits = {}
    for xml in no_parties_list:
        f = open(no_parties_path + xml + ".xml")
	no_parties_filebits[xml] = f.read()
	f.close()
    docketfilebits = {}
     

    for docket in TEST_DOCKET_LIST:
	    f = open(TEST_DOCKET_PATH + docket + "docket.html")
	    docketfilebits[docket] = f.read()
	    f.close()

    # Test merging with no parties in original (olddocket)
    docket = PP.parse_dktrpt(docketfilebits["cit7830"],"cit", "7830")
    olddocket, err =  DocketXML.parse_xml_string(no_parties_filebits["cit7830"]) 

    # Sanity Check
    self.assertNotEquals([], docket.parties)
    self.assertEquals([], olddocket.parties)
    olddocket.merge_docket(docket)
    self.assertEquals(olddocket.parties, docket.parties)


    
    docket = PP.parse_dktrpt(docketfilebits["cit7391"],"cit", "7391")
    olddocket, err =  DocketXML.parse_xml_string(no_parties_filebits["cit7391"]) 

    # Sanity Check
    self.assertNotEquals([], docket.parties)
    self.assertEquals([], olddocket.parties)
    olddocket.merge_docket(docket)
    self.assertEquals(olddocket.parties, docket.parties)

    
    # Test merging with some parties in original (olddocket)
    docket = PP.parse_dktrpt(docketfilebits["caed"],"caed", "7830")
    olddocket, err =  DocketXML.parse_xml_string(no_parties_filebits["caedSomeParties"]) 
    # Sanity Check
    self.assertEquals(6, len(docket.parties))
    self.assertEquals(4, len(olddocket.parties))

    olddocket.merge_docket(docket)

    self.assertEquals(6, len(olddocket.parties))
    self.assertTrue(sorted(olddocket.parties) == sorted(docket.parties))

    # Test merging with same num of parties but different number of attorneys
    docket = PP.parse_dktrpt(docketfilebits["cand2"],"cand2", "7830")
    olddocket, err =  DocketXML.parse_xml_string(no_parties_filebits["candSomeAttys"]) 

    # Sanity
    self.assertEquals("James Brady", olddocket.parties[0]["name"])
    self.assertEquals(1, len(olddocket.parties[0]["attorneys"]))
    self.assertEquals(3, len(docket.parties[0]["attorneys"]))

    self.assertEquals(-1, olddocket.parties[0]["attorneys"][0]["attorney_role"].find("TERMINATED"))

    olddocket.merge_docket(docket)

    self.assertEquals(3, len(olddocket.parties[0]["attorneys"]))
    self.assertNotEquals(-1, olddocket.parties[0]["attorneys"][0]["attorney_role"].find("TERMINATED"))

#    print docket.to_xml()
#    print olddocket.to_xml()


  def test_bankruptcy_parties_info_from_dkrpt(self):
    bank_dockets_list = ["njb.658906", "mnb.325447", "mdb.532409", "nvb.242643", "mieb.600286", "mdb.541423"]

    bank_soups = {}
    for docket in bank_dockets_list:
        bank_soups[docket] = _open_soup(BANK_TEST_DOCKET_PATH + docket + ".html")

    # Normal bankruptcy proceedings
    parties = PP._get_parties_info_from_dkrpt(bank_soups["mdb.532409"], "mdb")
    self.assertEquals(len(parties), 3)
    self.assertEquals(parties[0]["name"], "Rodney K. Cunningham")
    self.assertEquals(parties[0]["type"], "Debtor")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Sopo Ngwa")
    self.assertEquals(parties[1]["name"], "Karen S. Cunningham")
    self.assertEquals(parties[1]["type"], "Debtor")
    self.assertEquals(len(parties[1]["attorneys"]), 1)
    self.assertEquals(parties[1]["attorneys"][0]["attorney_name"], "Sopo Ngwa")
    self.assertEquals(parties[2]["type"], "Trustee")
     
    parties = PP._get_parties_info_from_dkrpt(bank_soups["nvb.242643"], "nvb")
    self.assertEquals(len(parties), 4)
    self.assertEquals(parties[0]["name"], "PAUL OGALESCO")
    self.assertTrue("PRO SE" in parties[0]["attorneys"][0]["contact"])
    self.assertEquals(parties[0]["type"], "Debtor")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[1]["name"], "RICK A. YARNALL")
    self.assertEquals(parties[1]["type"], "Trustee")
    self.assertTrue("TERMINATED" in parties[1]["extra_info"])

    # Adversary Proceeding type docket
    parties = PP._get_parties_info_from_dkrpt(bank_soups["njb.658906"], "njb")
    self.assertEquals(len(parties), 6)
    self.assertEquals(parties[0]["name"], "Richard A. Spair")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Eugene D. Roth")
    self.assertEquals(parties[1]["attorneys"][1]["attorney_role"], "LEAD ATTORNEY")
    self.assertEquals(parties[3]["name"], "Albert Russo")
    self.assertEquals(parties[3]["type"], "Trustee")


    parties = PP._get_parties_info_from_dkrpt(bank_soups["mnb.325447"], "mnb")
    self.assertEquals(len(parties), 2)
    self.assertEquals(parties[0]["name"], "RANDALL L SEAVER")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(parties[0]["extra_info"], "101 W. Burnsville Pkwy., Suite 201\nBurnsville, MN 55337")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Matthew R. Burton")
    
    parties = PP._get_parties_info_from_dkrpt(bank_soups["mieb.600286"], "mieb")
    

    miebfilebits = open(BANK_TEST_DOCKET_PATH+ "mieb.600286" + ".html").read()

    miebdocket = PP.parse_dktrpt(miebfilebits, "mieb", "600286")
    
    # mdb Adversary proceedings have slightly different formats, more similar to normal bank, but still different enough to crash parsepacer
    parties = PP._get_parties_info_from_dkrpt(bank_soups["mdb.541423"], "mdb")
    self.assertEquals(len(parties), 3)
    self.assertEquals(parties[0]["name"], "Metamorphix, Inc.")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(parties[0]["extra_info"], "Metamorphix, Inc.\nAttn: Dr. Edwin Quattlebaum\n8000 Virginia Manor Road\nBeltsville, MD 20705")
    self.assertEquals(len(parties[0]["attorneys"]), 2)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Peter D. Guattery")
    self.assertEquals(parties[1]["name"], "Edwin Quattlebaum")
    self.assertEquals(parties[1]["type"], "Plaintiff")
    self.assertEquals(parties[2]["name"], "Theresa Brady")
    self.assertEquals(parties[2]["type"], "Defendant")



  def test_all_bankruptcy_dktrpts_for_parties_basics(self):
    count =0

    no_parties_dockets = []
    one_parties_dockets = []

    for filename in os.listdir(BANK_TEST_DOCKET_PATH):
       court, casenum = filename.split(".")[:2]
       soup = _open_soup("/".join([BANK_TEST_DOCKET_PATH, filename]))

       parties = PP._get_parties_info_from_dkrpt(soup,court) 

       if len(parties)==0:
           no_parties_dockets.append(filename)
       if len(parties) == 1: 
	   one_parties_dockets.append(filename)

    print ""
    print "Dockets with no parties:"
    for filename in no_parties_dockets:
         print filename

    print "Dockets with only one party (possible error): "
    for filename in one_parties_dockets:
	 print filename

	  


  def test_get_parties_info_from_dkrpt(self): 
    testdockets = {}
    for docket in TEST_DOCKET_LIST:
	    testdockets[docket] = _open_soup(TEST_DOCKET_PATH + docket + "docket.html")

    parties = PP._get_parties_info_from_dkrpt(testdockets["txed"], "txed")
    self.assertEquals(len(parties), 14)
    self.assertEquals(parties[0]["name"], "AOL LLC")
    self.assertEquals(parties[0]["extra_info"], "TERMINATED: 03/26/2008")
    self.assertEquals(parties[2]["type"], "Mediator")
    self.assertEquals(parties[2]["name"], "James W. Knowles")

    parties = PP._get_parties_info_from_dkrpt(testdockets["deb"], "deb")

    self.assertEquals(len(parties), 9)
    self.assertEquals(parties[0]["name"], "American Business Financial Services, Inc., a Delaware Corporation")
    self.assertEquals(parties[0]["type"], "Debtor")
    self.assertEquals(len(parties[0]["attorneys"]), 9)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Bonnie Glantz Fatell")
    self.assertEquals(parties[0]["attorneys"][0]["attorney_role"], "TERMINATED: 04/11/2006")
    self.assertEquals(len(parties[1]["attorneys"]), 11)
    self.assertEquals(len(parties[1]["attorneys"]), 11)

    
    parties = PP._get_parties_info_from_dkrpt(testdockets["almb"], "almb")

    self.assertEquals(len(parties), 2)
    self.assertEquals(parties[0]["name"], "Ruthie Harris")
    # Should be no attorneys object
    self.assertEquals(parties[1].get("attorneys"), None)


    parties = PP._get_parties_info_from_dkrpt(testdockets["almd"], "almd")

    self.assertEquals(len(parties), 2)
    self.assertEquals(parties[0]["name"], "Joyce Efurd")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(len(parties[0]["attorneys"]), 3)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Allen Durham Arnold")
    self.assertEquals(parties[0]["attorneys"][0]["attorney_role"], "LEAD ATTORNEY\nATTORNEY TO BE NOTICED")
    self.assertEquals(len(parties[1]["attorneys"]), 3)
    # Should be no extra_info
    self.assertEquals(parties[0].get("extra_info"), None)
    
    parties = PP._get_parties_info_from_dkrpt(testdockets["cit"], "cit")
    self.assertEquals(len(parties), 4)
    self.assertEquals(parties[0]["name"], "New Hampshire Ball Bearing, Inc.")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Frank H. Morgan")
    self.assertEquals(parties[0]["attorneys"][0]["attorney_role"], "LEAD ATTORNEY\nATTORNEY TO BE NOTICED")
#    self.assertEquals(parties[2]["name"], "United States Customs and Border Protection")
    self.assertEquals(len(parties[2]["attorneys"]), 1)
    
    # This document has no parties, but it shouldn't break anything when doing that
    parties = PP._get_parties_info_from_dkrpt(testdockets["cit2"], "cit")
    self.assertEquals(len(parties), 0)

    """ this docket doesn't work - errors in creating beautiful soup
    parties = PP._get_parties_info_from_dkrpt(testdockets["akd"], "akd")
    print_parties(parties)
    self.assertEquals(len(parties), 4)
    self.assertEquals(parties[0]["name"], "West American Insurance Company")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["attorneys"][0]["attorney_name"], "Brewster H. Jamieson")
    self.assertEquals(parties[0]["attorneys"][0]["attorney_role"], "LEAD ATTORNEY\nATTORNEY TO BE NOTICED")
    self.assertEquals(len(parties[1]["attorneys"]), 0)
    """
    parties = PP._get_parties_info_from_dkrpt(testdockets["cand"], "cand")
    self.assertEquals(len(parties), 3)
    self.assertEquals(parties[0]["name"], "John Michael Balbo")
    self.assertEquals(parties[0]["type"], "Petitioner")
    self.assertTrue("PRO SE" in parties[0]["attorneys"][0]["contact"])
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[1]["extra_info"], "Secretary CDCR")

    parties = PP._get_parties_info_from_dkrpt(testdockets["cand2"], "cand")
    self.assertEquals(len(parties), 4)
    self.assertEquals(parties[0]["name"], "James Brady")
    self.assertEquals(parties[0]["type"], "Plaintiff")
    self.assertEquals(parties[1]["name"], "Sarah Cavanagh")
    self.assertEquals(parties[1]["type"], "Plaintiff" )
    self.assertEquals(parties[1]["extra_info"], "individually and on behalf of all others similarly situated" )
    self.assertEquals(len(parties[0]["attorneys"]), 3)
    self.assertEquals(parties[2]["name"], "Deloitte & Touche LLP")
    self.assertEquals(parties[2]["extra_info"], "a limited liability partnership")
    self.assertEquals(parties[3]["name"], "Deloitte Tax LLP")
    self.assertEquals(parties[3]["extra_info"], "TERMINATED: 08/14/2008")


    # There is extra metadata in this one that doesn't appear in others - Pending courts, highest offense level, disposition, etc, not collecting those currently
   # parties = PP._get_parties_info_from_dkrpt(testdockets["cand3"], "cand")
   # self.assertEquals(len(parties), 2)
   # self.assertEquals(len(parties[0]["attorneys"]), 1)
   # self.assertEquals(parties[0]["name"], "Gustavo Alfaro-Medina")

    parties = PP._get_parties_info_from_dkrpt(testdockets["caed"], "caed")
    self.assertEquals(len(parties), 6)
    self.assertEquals(len(parties[0]["attorneys"]), 1)
    self.assertEquals(parties[0]["name"], "Corey Mitchell")
    self.assertEquals(parties[1]["extra_info"], "Correctional Officer")

    parties = PP._get_parties_info_from_dkrpt(testdockets["ded"], "ded")
    self.assertEquals(len(parties), 4)
    self.assertEquals(len(parties[0]["attorneys"]), 2)
    self.assertEquals(parties[0]["name"], "Cubist Pharmaceuticals Inc.")

    parties = PP._get_parties_info_from_dkrpt(testdockets["cacd"], "cacd")
    self.assertEquals(len(parties), 18)
    self.assertEquals(len(parties[0]["attorneys"]), 2)
    self.assertEquals(parties[0]["name"], "LA Printex Industries Inc")


class TestParseOpinions(unittest.TestCase):
  def test_parse_opinions(self):
    opinion_filelist = ["akd.1900", "akd.2010", "nysd.2009"]

    #test empty file
    filebits = open('/dev/null').read()
    dockets = PP.parse_opinions(filebits, 'test')
    self.assertEquals([], dockets)

    filebits = {}

    for opinion_file in opinion_filelist:
        f = open(TEST_OPINION_PATH + opinion_file + ".opinions.html")
        filebits[opinion_file] = f.read()
        f.close()
    
    #test valid opinion file with no entries
    dockets = PP.parse_opinions(filebits["akd.1900"], "akd")
    self.assertEquals([], dockets) 

    dockets = PP.parse_opinions(filebits["akd.2010"], "akd")
    self.assertEquals(78, len(dockets) ) # number of entries in the opinions table
    
    #check basic metadata
    self.assertEquals("akd", dockets[0].get_court())
    self.assertEquals("12460", dockets[0].get_casenum())
    casemeta = dockets[0].get_casemeta()
    self.assertEquals("Steffensen v. City of Fairbanks et al", casemeta['case_name'])
    self.assertEquals("4:09-cv-00004-RJB", casemeta['docket_num'])
    self.assertEquals("42:1983 Prisoner Civil Rights", casemeta["case_cause"])
    self.assertEquals("Civil Rights: Other", casemeta["nature_of_suit"])
    self.assertEquals(1, len(dockets[0].documents))

    document = dockets[0].documents['98-0']
    self.assertEquals("98", document['doc_num'])
    self.assertEquals("0", document['attachment_num'])
    self.assertEquals("563", document['pacer_de_seq_num'])
    self.assertEquals("602530", document['pacer_dm_id'])
    self.assertEquals("2010-01-05", document['date_filed'])
    self.assertEquals("Order Dismissing Case", document['long_desc'])


    self.assertEquals("akd", dockets[1].get_court())
    self.assertEquals("18239", dockets[1].get_casenum())
    casemeta = dockets[1].get_casemeta()
    self.assertEquals("Kahle v. Executive Force Australia PTY LTD", casemeta['case_name'])
    self.assertEquals("2:09-cv-00008-JWS", casemeta['docket_num'])
    self.assertEquals("28:1441 Petition for Removal- Personal Injury", casemeta["case_cause"])
    self.assertEquals("Personal Inj. Prod. Liability", casemeta["nature_of_suit"])
    self.assertEquals(1, len(dockets[1].documents))

    document = dockets[1].documents['27-0']
    self.assertEquals("27", document['doc_num'])
    self.assertEquals("0", document['attachment_num'])
    self.assertEquals("142", document['pacer_de_seq_num'])
    self.assertEquals("603861", document['pacer_dm_id'])
    self.assertEquals("2010-01-07", document['date_filed'])
    self.assertEquals("Order on Motion for Hearing, Order on Motion to Amend/Correct, Order on Motion to Remand to State Court, Order on Motion to Strike", document['long_desc'])

    self.assertEquals("akd", dockets[5].get_court())
    self.assertEquals("15580", dockets[5].get_casenum())
    casemeta = dockets[5].get_casemeta()
    self.assertEquals("USA v. Celestine et al", casemeta['case_name'])
    self.assertEquals("3:2009-cr-00065-HRH", casemeta['docket_num'])
    self.assertEquals(None, casemeta.get("case_cause"))
    self.assertEquals(None, casemeta.get("nature_of_suit"))
    self.assertEquals(1, len(dockets[5].documents))

    document = dockets[5].documents['135-0']
    self.assertEquals("135", document['doc_num'])
    self.assertEquals("0", document['attachment_num'])
    self.assertEquals("794", document['pacer_de_seq_num'])
    self.assertEquals("616260", document['pacer_dm_id'])
    self.assertEquals(datetime.date.today().isoformat(), document['date_filed'])
    self.assertEquals("Order on Motion for Bill of Particulars, Order on Motion for Joinder", document['long_desc'])

    #Sometimes the document url case id does not match the court case id
    #  In these cases we want to use the parent case number, but also have access to the child casenum
    self.assertEquals("akd", dockets[2].get_court())
    self.assertEquals("4655", dockets[2].get_casenum())
    casemeta = dockets[2].get_casemeta()
    self.assertEquals("USA v. Kott et al", casemeta['case_name'])
    self.assertEquals("3:2007-cr-00056-JWS", casemeta['docket_num'])
    self.assertEquals(1, len(dockets[2].documents))

    document = dockets[2].documents['429-0']
    self.assertEquals("429", document['doc_num'])
    self.assertEquals("0", document['attachment_num'])
    self.assertEquals("1946", document['pacer_de_seq_num'])
    self.assertEquals("606429", document['pacer_dm_id'])
    self.assertEquals("2010-01-13", document['date_filed'])
    self.assertEquals("Order on Motion to Dismiss", document['long_desc'])

    self.assertEquals("4656", document['casenum'])


    # Some dockets have a different linking format from akd. Let's test these out
    dockets = PP.parse_opinions(filebits["nysd.2009"], "nysd")
    self.assertEquals(5916, len(dockets) ) # number of entries in the opinions table

    
    self.assertEquals("nysd", dockets[0].get_court())
    self.assertEquals("53122", dockets[0].get_casenum())
    casemeta = dockets[0].get_casemeta()
    self.assertEquals("Kingsway Financial v. Pricewaterhouse, et al", casemeta['case_name'])
    self.assertEquals("1:03-cv-05560-RMB-HBP", casemeta['docket_num'])
    self.assertEquals("15:78m(a) Securities Exchange Act", casemeta["case_cause"])
    self.assertEquals("Securities/Commodities", casemeta["nature_of_suit"])
    self.assertEquals(1, len(dockets[0].documents))
    
    document = dockets[0].documents['380-0']
    self.assertEquals("380", document['doc_num'])
    self.assertEquals("0", document['attachment_num'])
    self.assertEquals("6095482", document['pacer_de_seq_num'])
    self.assertEquals("5453339", document['pacer_dm_id'])
    self.assertEquals("2009-01-05", document['date_filed'])
    self.assertEquals("Memorandum & Opinion", document['long_desc'])
    

    # Some sanity checks about iquery type opinion pages

    for docket in dockets:
        self.assertEquals(1, len(docket.documents))
        document = docket.documents.values()[0]
        casenum_diff = int(docket.get_casenum()) - int(document['casenum'])
        self.assertTrue(casenum_diff <= 0)


class TestViews(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        Document.objects.all().delete()


    # test index
    def test_index_view(self):
        response = self.client.get('/recap/')
        self.assertEquals("Well hello, there's nothing to see here.", response.content)

    # test upload view

    # test get_updated_cases
    def test_get_updated_cases_no_key(self):
        response = self.client.get('/recap/get_updated_cases/')
        self.assertEquals(403, response.status_code)
    
    def test_get_updated_cases_incorrect_key(self):
        response = self.client.get('/recap/get_updated_cases/', {'key' : 'incorrect_key'})
        self.assertEquals(403, response.status_code)
    
    def test_get_updated_cases_valid_request(self):
        d1 = Document(court='nysd', casenum='1234', docnum='1', subdocnum='0')
        d1.save()
        d2 = Document(court='dcd', casenum='100', docnum='1', subdocnum='0')
        d2.save()
        yesterday = time.time() - 60 * 60 * 24
        response = self.client.post('/recap/get_updated_cases/', {'key' : REMOVED, 
                                                                 'tpq' : yesterday})
        self.assertEquals(200, response.status_code)
        self.assertEquals('%s,%s\r\n%s,%s\r\n' % (d1.court, d1.casenum, d2.court, d2.casenum), response.content)
        self.assertEquals({'Content-Type': 'text/csv'}, response.headers)
                
    
    # heartbeat view tests
    def test_heartbeat_view_no_key(self):
        response = self.client.get('/recap/heartbeat/')
        self.assertEquals(403, response.status_code)
    
    def test_heartbeat_view_incorrect_key(self):
        response = self.client.get('/recap/heartbeat/', {'key' : 'incorrect_key'})
        self.assertEquals(403, response.status_code)
    
    def test_heartbeat_correct_key_no_db_connection(self):
        response = self.client.get('/recap/heartbeat/', {'key' : 'REMOVED'})
        self.assertEquals(500, response.status_code)
        self.assertEquals("500 Server error: He's Dead Jim", response.content)
        
    def test_heartbeat_correct_key_with_db_connection(self):

        document = Document(court='cand', casenum='215270', docnum='1', subdocnum='0')
        document.save()

        response = self.client.get('/recap/heartbeat/', {'key' : 'REMOVED'})
        self.assertEquals(200, response.status_code)
        self.assertEquals("It's Alive!", response.content)

class TestUploadView(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.f = open(TEST_DOCKET_PATH + 'DktRpt_111111.html')
        self.valid_params = {'court': 'nysd', 
                             'casenum' : '1234',
                             'mimetype' : 'text/html',
                             'data': self.f} 
        self.f_pdf = open(TEST_DOCUMENT_PATH + 'gov.uscourts.cand.206019.18.0.pdf')
        self.valid_params_pdf = {'court': 'cand', 
                                 'casenum': '206019',
                                 'mimetype': 'application/pdf',
                                 'url': 'https://ecf.cand.uscourts.gov/doc1/123456', #docid
                                 'data': self.f_pdf} 

        #Doc id is 'coerced', so doesn't match one above
        self.pdf_doc = Document(court='cand', casenum='206019', 
                                docnum='18', subdocnum='0', docid=123056)
        self.pdf_doc.save()
        
        self.f_doc1 = open(TEST_DOC1_PATH + 'ecf.cand.uscourts.gov.03517852828')
        self.valid_params_doc1 = {'court': 'cand', 
                                 'casenum': '206019',
                                 'mimetype': 'text/html',
                                 'data': self.f_doc1} 

    def tearDown(self):
        self.f.close()
        self.f_pdf.close()
        self.f_doc1.close()
        for p in PickledPut.objects.all():
            IA.delete_pickle(p.filename)
            p.delete()
        Document.objects.all().delete()
    
    def test_upload_post_request_only(self):
        response = self.client.get('/recap/upload/', {'blah' : 'foo'})
        self.assertEquals('upload: Not a POST request.', response.content)
    
    def test_upload_no_params(self):
        response = self.client.post('/recap/upload/')
        self.assertEquals("upload: No request.FILES attribute.", response.content)
    
    def test_upload_docket_no_court_param(self):
        del self.valid_params['court']
        response = self.client.post('/recap/upload/', self.valid_params)
        self.assertEquals("upload: No POST 'court' attribute.", response.content)
    
    def test_upload_docket_invalid_casenum_param(self):
        self.valid_params['casenum'] = 'garbage_data'
        response = self.client.post('/recap/upload/', self.valid_params)
        self.assertEquals("upload: 'casenum' is not an integer: garbage_data", response.content)
    
    def test_upload_docket_no_casenum_param(self):
        del self.valid_params['casenum']
        response = self.client.post('/recap/upload/', self.valid_params)
        self.assertEquals("upload: docket has no casenum.", response.content)
    
    def test_upload_docket_no_mimetype_param(self):
        del self.valid_params['mimetype']
        response = self.client.post('/recap/upload/', self.valid_params)
        self.assertEquals("upload: No POST 'mimetype' attribute.", response.content)
    
    def test_upload_docket_report(self):
        response = self.client.post('/recap/upload/', self.valid_params)
        output = simplejson.loads(response.content)
        self.assertEquals(3, len(output))
        self.assertEquals("DktRpt successfully parsed.", output['message'])
        # After upload, a pickled put should be created
        # If this fails, make sure you've created a picklejar directory
        self.assertEquals(1, PickledPut.objects.all().count())
        pp = PickledPut.objects.all()[0]
        self.assertEquals(1, pp.ready)
    
    def test_upload_docket_report_for_unlocked_bucket(self):
        # Setup - Upload a docket
        response = self.client.post('/recap/upload/', self.valid_params)
        # After upload, a pickled put should be created
        self.assertEquals(1, PickledPut.objects.all().count())

        #Do it again, to test whether merges are handled correctly
        response = self.client.post('/recap/upload/', self.valid_params)
        output = simplejson.loads(response.content)
        self.assertEquals("DktRpt successfully parsed.", output['message'])
        self.assertEquals(1, PickledPut.objects.all().count())
        pp = PickledPut.objects.all()[0]
        self.assertEquals(1, pp.ready)
    
    #TK: This case seems wrong, we discard the newer docket if an old docket
    # on the same case is being uploaded. Might be too edge casey to worry about
    # The function test behavior is the same as the one above, so going to leave it 
    # unimplemented for now
    def test_upload_docket_report_for_locked_bucket(self):
        pass
    
    def test_upload_document_without_url(self):
        del self.valid_params_pdf['url']
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        self.assertEquals('upload: pdf failed. no url supplied.', response.content)
    
    #TK: Handle this case better? Most likely isn't possible
    def test_upload_document_no_associated_document_with_docid(self):
        self.pdf_doc.delete()
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        self.assertEquals('upload: pdf ignored.', response.content)
    
    def test_upload_document_no_record_of_docid(self):
        self.pdf_doc.docid=99999
        self.pdf_doc.save()
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        self.assertEquals('upload: pdf ignored.', response.content)
    
    def test_upload_document_metadata_mismatch(self):
        self.valid_params_pdf['court'] = 'azb'
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        self.assertEquals('upload: pdf metadata mismatch.', response.content)
    
    def test_upload_document(self):
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        output = simplejson.loads(response.content)
        self.assertEquals('pdf uploaded.', output['message'])
        self.assertEquals(2, PickledPut.objects.all().count())
        self.pdf_doc = Document.objects.all()[0]
        self.assertTrue(self.pdf_doc.sha1 != None)
        self.assertEquals("5741373aff552f22fa2f14f2bd39fea4564aa49c", self.pdf_doc.sha1)
    
    def test_upload_document_no_sha1_difference(self):
        #set the sha1 to what we know it to be
        self.pdf_doc.sha1 = "5741373aff552f22fa2f14f2bd39fea4564aa49c"
        self.pdf_doc.save()
        response = self.client.post('/recap/upload/', self.valid_params_pdf)
        output = simplejson.loads(response.content)
        self.assertEquals('pdf uploaded.', output['message'])
        # we only upload a docket update if the doc is the same
        self.assertEquals(1, PickledPut.objects.all().count())
    
    # have to do some patching to get around the filename issue
    @patch('uploads.UploadHandler.is_doc1_html', Mock(return_value=True))
    @patch('uploads.UploadHandler.docid_from_url_name', Mock(return_value='9999999'))
    def test_upload_doc1_no_matching_docid(self):
        response = self.client.post('/recap/upload/', self.valid_params_doc1)
        self.assertEquals('upload: doc1 ignored.', response.content)
    
    # have to do some patching to get around the filename issue
    @patch('uploads.UploadHandler.is_doc1_html', Mock(return_value=True))
    @patch('uploads.UploadHandler.docid_from_url_name', Mock(return_value='123056'))
    def test_upload_doc1(self):
        response = self.client.post('/recap/upload/', self.valid_params_doc1)
        output = simplejson.loads(response.content)
        self.assertEquals('doc1 successfully parsed.', output['message'])
        self.assertTrue('cases' in output)



class TestQueryCasesView(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_params = {'court': 'nysd', 
                             'casenum' : '1234'} 
        
        self.available_doc = Document(court='nysd', casenum='1234', docnum='2', subdocnum='0', 
                                        dm_id = '1234', de_seq_num = '111', docid = '1230445')
        self.available_doc.available = '1'
        self.available_doc.lastdate = datetime.datetime.now()
        self.available_doc.save()
    
    def tearDown(self):
        Document.objects.all().delete()

    def test_query_cases_post_request_only(self):
        response = self.client.get('/recap/query_cases/', {'blah' : 'foo'})
        self.assertEquals('query_cases: Not a POST request.', response.content)
    
    def test_query_cases_no_params(self):
        response = self.client.post('/recap/query_cases/')
        self.assertEquals("query_cases: no 'json' POST argument", response.content)
    
    def test_query_cases_missing_court_param(self):
        del self.valid_params['court']
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("query_cases: missing json 'court' argument.", response.content)
    
    def test_query_cases_missing_casenum_param(self):
        del self.valid_params['casenum']
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("query_cases: missing json 'casenum' argument.", response.content)

    def test_valid_query_cases_response_no_match(self):

        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("{}", response.content)
    
    def test_valid_query_cases_response_no_match(self):
        self.valid_params['casenum'] = '99999'
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("{}", response.content)
    
    def test_valid_query_cases_response_available_doc_match(self):
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        output= simplejson.loads(response.content)

        self.assertEquals(2, len(output))
        self.assertEquals(self.available_doc.lastdate.strftime("%m/%d/%y"), output['timestamp'])
        self.assertEquals(IACommon.get_dockethtml_url('nysd', '1234'), output['docket_url'])
    
    def test_valid_query_cases_response_unavailable_doc_currently_uploading(self):
        self.available_doc.available = 0
        self.available_doc.save()
        ppquery = PickledPut(filename=IACommon.get_docketxml_name('nysd', '1234'))
        ppquery.save()
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("{}", response.content)
        PickledPut.objects.all().delete()
    
    def test_valid_query_cases_response_old_doc_currently_uploading(self):
        self.available_doc.available = 0
        two_days_ago = datetime.datetime.now() - datetime.timedelta(2)
        self.available_doc.modified= two_days_ago
        self.available_doc.save()

        ppquery = PickledPut(filename=IACommon.get_docketxml_name('nysd', '1234'))
        ppquery.save()
        response = self.client.post('/recap/query_cases/', {'json': simplejson.dumps(self.valid_params)})
        
        output= simplejson.loads(response.content)

        self.assertEquals(2, len(output))
        self.assertEquals(self.available_doc.lastdate.strftime("%m/%d/%y"), output['timestamp'])
        self.assertEquals(IACommon.get_dockethtml_url('nysd', '1234'), output['docket_url'])
        PickledPut.objects.all().delete()




class TestQueryView(unittest.TestCase): 
    def setUp(self):
        self.client = Client()
        self.not_avail_doc= Document(court='nysd', casenum='1234', docnum='1', subdocnum='0', 
                                        dm_id = '1234', de_seq_num = '111', docid = '12304213')
        self.not_avail_doc.save()

        self.available_doc = Document(court='nysd', casenum='1234', docnum='2', subdocnum='0', 
                                        dm_id = '1234', de_seq_num = '111', docid = '1230445')
        self.available_doc.available = '1'
        self.available_doc.lastdate = datetime.datetime.now()
        self.available_doc.save()

        self.docs = [self.not_avail_doc, self.available_doc]

        self.valid_params = {'court': 'nysd', 
                             'urls' : [self._show_doc_url_for_document(d) for d in self.docs]}
        
        self.valid_params_doc1 = {'court': 'nysd', 
                                 'urls' : [self._doc1_url_for_document(d) for d in self.docs]}
    
    def tearDown(self):
        Document.objects.all().delete()

    def _show_doc_url_for_document(self, doc):
        show_doc_url = "".join(['/cgi-bin/show_doc.pl?',
                                'caseid=%(casenum)s',
                                '&de_seq_num=%(de_seq_num)s',
                                '&dm_id=%(dm_id)s',
                                '&doc_num=%(docnum)s',
                                '&pdf_header=2'])
        show_doc_dict = {'casenum': doc.casenum, 'de_seq_num': doc.de_seq_num,
                            'dm_id': doc.dm_id, 'docnum': doc.docnum}

        return show_doc_url % show_doc_dict
    
    def _doc1_url_for_document(self, doc):
        return "/doc1/%s" % doc.docid

    def _ia_url_for_doc(self, doc):
        return IACommon.get_pdf_url(doc.court, doc.casenum, doc.docnum, doc.subdocnum)


    def test_query_post_request_only(self):
        response = self.client.get('/recap/query/', {'blah' : 'foo'})
        self.assertEquals('query: Not a POST request.', response.content)
    
    def test_query_no_params(self):
        response = self.client.post('/recap/query/')
        self.assertEquals("query: no 'json' POST argument", response.content)
    
    # TK: what does too many url args mean as a message
    def test_query_invalid_json(self):
        response = self.client.post('/recap/query/', {'json': 'dkkfkdk'})
        self.assertEquals("query: too many url args", response.content)

    def test_query_missing_court_param(self):
        del self.valid_params['court']
        response = self.client.post('/recap/query/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("query: missing json 'court' argument.", response.content)

    def test_query_missing_url_param(self):
        del self.valid_params['urls']
        response = self.client.post('/recap/query/', {'json': simplejson.dumps(self.valid_params)})
        self.assertEquals("query: missing json 'urls' argument.", response.content)
    
    def test_valid_show_doc_query_response(self):
        response = self.client.post('/recap/query/', {'json': simplejson.dumps(self.valid_params)})
       
        output = simplejson.loads(response.content)
        avail_show_doc_url = self._show_doc_url_for_document(self.available_doc)
        self.assertTrue(avail_show_doc_url in output)
        self.assertFalse(self._show_doc_url_for_document(self.not_avail_doc) in output)
        self.assertEquals(self.available_doc.lastdate.strftime("%m/%d/%y"), output[avail_show_doc_url]['timestamp'])
        self.assertEquals(self._ia_url_for_doc(self.available_doc), output[avail_show_doc_url]['filename'])
    
    def test_valid_doc1_url_query_response(self):
        response = self.client.post('/recap/query/', {'json': simplejson.dumps(self.valid_params_doc1)})
        output = simplejson.loads(response.content)

        avail_show_doc_url = self._doc1_url_for_document(self.available_doc)
        self.assertFalse(self._doc1_url_for_document(self.not_avail_doc) in output)
        self.assertEquals(self.available_doc.lastdate.strftime("%m/%d/%y"), output[avail_show_doc_url]['timestamp'])
        self.assertEquals(self._ia_url_for_doc(self.available_doc), output[avail_show_doc_url]['filename'])
    
    def test_valid_query_response_with_subdocuments(self):
        subdoc1 = Document(court='nysd', casenum='1234', docnum='2', subdocnum='1', 
                                    available=1, lastdate = datetime.datetime.now())
        subdoc2 = Document(court='nysd', casenum='1234', docnum='2', subdocnum='2',
                                    available=1, lastdate = datetime.datetime.now())
        subdoc3 = Document(court='nysd', casenum='1234', docnum='2', subdocnum='3')
        subdoc1.save()
        subdoc2.save()
        subdoc3.save()
        
        response = self.client.post('/recap/query/', {'json': simplejson.dumps(self.valid_params)})
        output = simplejson.loads(response.content)
        
        avail_show_doc_url = self._show_doc_url_for_document(self.available_doc)
        self.assertTrue(avail_show_doc_url in output)
        self.assertTrue('subDocuments' in output[avail_show_doc_url])
        subdoc_dict = output[avail_show_doc_url]['subDocuments']
        self.assertEquals(2, len(subdoc_dict))
        self.assertEquals(self._ia_url_for_doc(subdoc1), subdoc_dict['1']['filename'])

class TestAddDocMetaView(unittest.TestCase): 
    def setUp(self):
        self.client = Client()
        self.existing_document  = Document(court='nysd', casenum='1234', docnum='1', subdocnum='0')
        self.existing_document.save()
        self.adddocparams =  { 'court': 'nysd', 'casenum': '1234', 
                               'docnum': '1', 'de_seq_num': '1111',
                               'dm_id': '2222', 'docid': '3330'}
    def tearDown(self):
        Document.objects.all().delete()


    
    def test_adddoc_only_post_requests_allowed(self):
        response = self.client.get('/recap/adddocmeta/')
        self.assertEquals("adddocmeta: Not a POST request.", response.content)
    
    def test_adddoc_request_data_missing(self):
        response = self.client.post('/recap/adddocmeta/', {'docid': '1234'})
        self.assertTrue(response.content.startswith("adddocmeta: \"Key 'court' not found"))

    def test_adddoc_updates_meta(self):
        self.assertEquals(None, self.existing_document.docid)
        response = self.client.post('/recap/adddocmeta/', self.adddocparams)
        self.assertEquals("adddocmeta: DB updated for docid=3330", response.content)
        query = Document.objects.filter(court='nysd', casenum='1234', 
                                        docnum='1', subdocnum='0')

        saved_document = query[0]
        self.assertEquals(1111, saved_document.de_seq_num)
        self.assertEquals(2222, saved_document.dm_id)
        self.assertEquals('3330', saved_document.docid)
    
    def test_adddoc_coerces_doc_id(self):
        self.adddocparams['docid'] = '123456789'
        response = self.client.post('/recap/adddocmeta/', self.adddocparams)
        query = Document.objects.filter(court='nysd', casenum='1234', 
                                        docnum='1', subdocnum='0')

        saved_document = query[0]
        self.assertEquals('123056789', saved_document.docid)
    
    def test_adddoc_creates_new_document(self):
        query = Document.objects.filter(court='nysd', casenum='5678', 
                                        docnum='1', subdocnum='0')

        self.adddocparams['casenum'] = '5678'
        self.assertEquals(0, query.count()) 
        response = self.client.post('/recap/adddocmeta/', self.adddocparams)
        self.assertEquals(1, query.count()) 
        created_doc = query[0]
        created_doc.docid = self.adddocparams['docid']
    
    def test_adddoc_responds_with_document_dict(self):
        self.adddocparams['add_case_info'] = True
        response = self.client.post('/recap/adddocmeta/', self.adddocparams)
        response_dict = simplejson.loads(response.content)
        self.assertEquals(1, len(response_dict['documents']))
        self.assertTrue(self.adddocparams['docid'] in response_dict['documents'])
        


class TestThirdPartyViews(unittest.TestCase):
    # test lock
    def setUp(self):
        self.client = Client()
        self.uploader = Uploader(key='testkey', name='testuploader')
        self.uploader.save()

    def tearDown(self):
        Uploader.objects.all().delete()
        BucketLock.objects.all().delete()

    def test_lock_no_key(self):
        response = self.client.get('/recap/lock/', {'court' : 'nysd', 'casenum' : 1234})
        self.assertEquals("0<br>Missing arguments.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_lock_invalid_key(self):
        response = self.client.get('/recap/lock/', {'key' : 'invalid_key', 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        self.assertEquals("0<br>Authentication failed.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_lock_valid_request(self):
        response = self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        created_lock = BucketLock.objects.all()[0]
        self.assertEquals("1<br>%s" % created_lock.nonce, response.content)
        self.assertEquals(200, response.status_code)
    
    def test_lock_already_locked_bucket_same_requester(self):
        #lock a case
        self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        
        created_lock = BucketLock.objects.all()[0]
        response = self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        self.assertEquals("1<br>%s" % created_lock.nonce, response.content)
        self.assertEquals(200, response.status_code)
    
    def test_lock_ready_but_not_processing(self):
        #lock a case
        self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})

        # unlock it, it should be marked ready for upload
        response = self.client.get('/recap/unlock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 1,
                                                    'nononce' : 0})
        created_lock = BucketLock.objects.all()[0]
        self.assertEquals(1, created_lock.ready)
        self.assertEquals(0, created_lock.processing)
        
        #lock it again
        self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        
        created_lock = BucketLock.objects.all()[0]
        self.assertEquals(0, created_lock.ready)
        self.assertEquals(0, created_lock.processing)

    
    def test_lock_already_locked_bucket_different_requester(self):
        other_guy = Uploader(key='otherkey', name='imposter')
        other_guy.save()

        #lock a case
        self.client.get('/recap/lock/', {'key' : self.uploader.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        
        response = self.client.get('/recap/lock/', {'key' : other_guy.key, 
                                                    'court' : 'nysd', 
                                                    'casenum' : 1234})
        self.assertEquals("0<br>Locked by another user.", response.content)
        self.assertEquals(200, response.status_code)

    # test unlock
    def test_unlock_no_key(self):
        response = self.client.get('/recap/unlock/', {'court' : 'nysd', 'casenum' : 1234})
        self.assertEquals("0<br>Missing arguments.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_unlock_invalid_key(self):
        response = self.client.get('/recap/unlock/', {'key' : 'invalid_key',
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 1,
                                                    'nononce' : 0})
        self.assertEquals("0<br>Authentication failed.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_unlock_valid_nonexisting_lock(self):
        response = self.client.get('/recap/unlock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 1,
                                                    'nononce' : 0})
        self.assertEquals('1', response.content)
        self.assertEquals(200, response.status_code)
    
    def test_unlock_valid_not_modified(self):
        #create a lock
        self.client.get('/recap/lock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234})

        created_lock = BucketLock.objects.all()[0]
        self.assertNotEquals(None, created_lock)

        response = self.client.get('/recap/unlock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 0,
                                                    'nononce' : 0})
        self.assertEquals('1', response.content)
        self.assertEquals(200, response.status_code)
        self.assertEquals(0, BucketLock.objects.count())
    
    def test_unlock_valid_modified(self):
        #create a lock
        self.client.get('/recap/lock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234})

        created_lock = BucketLock.objects.all()[0]
        self.assertNotEquals(None, created_lock)

        response = self.client.get('/recap/unlock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 1,
                                                    'nononce' : 0})
        self.assertEquals('1', response.content)
        self.assertEquals(200, response.status_code)
        self.assertEquals(1, BucketLock.objects.count())
        self.assertEquals(1, BucketLock.objects.all()[0].ready)

    def test_unlock_bucket_different_requester(self):
        other_guy = Uploader(key='otherkey', name='imposter')
        other_guy.save()

        #lock a case
        self.client.get('/recap/lock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234})
        
        response = self.client.get('/recap/unlock/', {'key' : other_guy.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234,
                                                    'modified' : 1,
                                                    'nononce' : 0})
        self.assertEquals("0<br>Locked by another user.", response.content)
        self.assertEquals(200, response.status_code)

    # test querylocks
    def test_querylocks_no_key(self):
        response = self.client.get('/recap/querylocks/')
        self.assertEquals("0<br>Missing arguments.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_querylocks_invalid_key(self):
        response = self.client.get('/recap/querylocks/', {'key' : 'invalid_key'})
        self.assertEquals("0<br>Authentication failed.", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_querylocks_valid_no_locks(self):
        response = self.client.get('/recap/querylocks/', {'key' : self.uploader.key})
        self.assertEquals("0<br>", response.content)
        self.assertEquals(200, response.status_code)
    
    def test_querylocks_valid_two_locks(self):
        response = self.client.get('/recap/lock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 1234})
        response = self.client.get('/recap/lock/', {'key' : self.uploader.key,
                                                    'court' : 'nysd',
                                                    'casenum' : 5678})
        response = self.client.get('/recap/querylocks/', {'key' : self.uploader.key})
        #remainder of content is nonce and other case
        self.assertEquals("2<br>nysd,1234", response.content[0:14])
        self.assertEquals(200, response.status_code)



def print_parties(parties):

    for party in parties:
     print party["type"]
     print party["name"]
     print party["extra_info"]
     att_list = party["attorneys"]
     for att in att_list:
	print_attorney(att)



def print_attorney(att):
	   print "  Attorney: "
	   print "   %s " % att['attorney_name'] 
	   try:
	      print "   %s " % att['contact']
	   except KeyError:
              print "   NO CONTACT"

	   try:
		print "  %s " % att['attorney_role']
	   except KeyError:
		print "   NO ROLE"
	   print ""
    
def _open_soup(filename):
    f = open(filename)
    filebits = f.read()

    try:
        the_soup = BeautifulSoup(filebits, convertEntities="html")
    except TypeError:
        # Catch bug in BeautifulSoup: tries to concat 'str' and 'NoneType' 
        #  when unicode coercion fails.
        message = "DktRpt BeautifulSoup error %s.%s" % \
            (court, casenum)
        logging.warning(message)
        
        filename = "%s.%s.dktrpt" % (court, casenum)
        try:
            error_to_file(filebits, filename)
        except NameError:
            pass
        
        return None

    except HTMLParseError:
        # Adjust for malformed HTML.  Wow, PACER.

        # Strip out broken links from DktRpt pages
        badre = re.compile("<A HREF=\/cgi-bin\/.*\.pl[^>]*</A>")
        filebits = badre.sub('', filebits)

        filebits = filebits.replace("&#037; 20", 
                                    "&#037;20")
        filebits = filebits.replace(" name=send_to_file<HR><CENTER>", 
                                    " name=send_to_file><HR><CENTER>")

	bad_end_tag_re = re.compile("</font color=.*>")

	filebits = bad_end_tag_re.sub("</font>", filebits)
        try:
            the_soup = BeautifulSoup(filebits, convertEntities="html")
        except HTMLParseError, err:

            message = "DktRpt parse error. %s %s line: %s char: %s." % \
                (filename, err.msg, err.lineno, err.offset)
            print message

	    print court
        
            return None

    return the_soup

def suite(): 
     suite = unittest.TestSuite()
#     suite.addTest(TestParsePacer('test_parse_dktrpt'))
#     suite.addTest(TestParsePacer('test_bankruptcy_parties_info_from_dkrpt'))
#     suite.addTest(TestParsePacer('test_get_parties_info_from_dkrpt'))
#     suite.addTest(TestParsePacer('test_all_bankruptcy_dockets_for_case_metadata'))
#     suite.addTest(TestParsePacer('test_all_bankruptcy_dktrpts_for_parties_basics'))
#     suite.addTest(TestParsePacer('test_docket_output'))
#     suite.addTest(TestParsePacer('test_parse_opinions'))

#    Test everything: 
#     suite.addTest(unittest.makeSuite(TestParsePacer))
     suite.addTest(unittest.makeSuite(TestViews))
     
     return suite


 
if __name__ == '__main__':
	unittest.TextTestRunner(verbosity=2).run(suite())




"""

    party_set= the_soup.findAll(text = re.compile(r"Defendant|Plaintiff|Debtor|Trustee|Mediator|Creditor Committee"))


    entry = party_set[9]

    party_cols = entry.findParent('tr').findAll('td')

    attorneys = party_cols[2]

    bonnie = attorneys.font

    att_list = []
    attdict = {}
    for node in bonnie:
	 if(isinstance(node, Tag)):
		 if node.name == 'b':
			 if attdict:
				 att_list.append(attdict)
			 attdict = {}
			 attdict['attorney_name'] = node.string.strip()
		 elif node.name == 'i':
			 try:
			   attdict['attorney_role'] += "\n" + node.string.strip() 
			 except KeyError:
		           if node.string.strip():
			     attdict['attorney_role'] = node.string.strip()
	 elif(isinstance(node, NavigableString)):
		if node.string:
		 try: 
		   attdict['contact'] += "\n" + node.string.strip()
		 except KeyError:
		   if node.string.strip():
		    attdict['contact'] = node.string.strip()
    # Append final lawyer
    if attdict:
      att_list.append(attdict)

    for att in att_list:
	   print "Attorney: "
	   print att['attorney_name'] 
	   try:
	      print att['contact']
	   except KeyError:
              print "NO CONTACT"

	   try:
		print att['attorney_role']
	   except KeyError:
		print "NO ROLE"
	   print ""

    print "I count %d attorneys for this party" % len(att_list)
"""

