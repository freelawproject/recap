import os
import logging
import datetime
import hashlib
import string
import random
import re
import cStringIO as StringIO
from django.conf import settings

from lxml.etree import Element, SubElement, tostring, \
    fromstring, XMLSyntaxError, XSLT, parse

THIS_DIR = os.path.dirname(__file__)
XSL_PATH = THIS_DIR + "/docket.xsl"


class DocketXML(object):
    """ See docket.dtd for metadata fields. """

    def __init__(self, court_s, casenum_s, meta_dict=None):
        """ A U.S. federal court case docket.
            Requires the docket to have a court and a case number.
        """
        if not meta_dict:
            meta_dict = {}

        # Case-level metadata
        self.casemeta = {"court": unicode(court_s),
                         "pacer_case_num": unicode(casenum_s)}
        for k, v in meta_dict.items():
            meta_dict[k] = unicode(v)
        self.casemeta.update(meta_dict)

        # List of parties, including party and attorney info
        self.parties = []

        # Dict of document-level metadata, keyed by '<docnum>-<subdocnum>'
        self.documents = {}

        # Assign each DocketXML a new random nonce
        self.nonce = generate_new_nonce()

    def get_court(self):
        return self.casemeta["court"]

    def get_casenum(self):
        return self.casemeta["pacer_case_num"]

    def get_casemeta(self):
        return self.casemeta

    def __eq__(self, other):
        if other is None:
            return False
        return self.to_xml() == other.to_xml()

    def add_document(self, docnum_s, subdocnum_s="0", meta_dict=None):
        """ Add a document to the list.
            Requires the document to have a docnum (and a subdocnum).
        """
        if not meta_dict:
            meta_dict = {}

        # If docnum_s and subdocnum_s aren't integers, skip.
        try:
            int(docnum_s)
            int(subdocnum_s)
        except ValueError:
            return

        dockey = "%s-%s" % (unicode(docnum_s), unicode(subdocnum_s))
        self.documents[dockey] = {"doc_num": unicode(docnum_s),
                                  "attachment_num": unicode(subdocnum_s)}
        for k, v in meta_dict.items():
            meta_dict[k] = unicode(v)
        self.documents[dockey].update(meta_dict)

    def add_document_object(self, theDocument):
        """ Adds a document object (taken from db, generally) to the list
        """
        metadatadict = theDocument.__dict__

        # We'll store the docnum and subdocnum differently inside add_document
        docnum = metadatadict['docnum']
        subdocnum = metadatadict['subdocnum']
        del metadatadict['docnum']
        del metadatadict['subdocnum']

        # Change some names to match docketxml naming schema
        metadatadict["pacer_doc_id"] = metadatadict["docid"]
        del metadatadict["docid"]

        metadatadict["pacer_de_seq_num"] = metadatadict["de_seq_num"]
        del metadatadict["de_seq_num"]

        metadatadict["pacer_dm_id"] = metadatadict["dm_id"]
        del metadatadict["dm_id"]

        metadatadict["upload_date"] = metadatadict["lastdate"]
        del metadatadict["lastdate"]

        # These are not stored in DocketXML document objects
        del metadatadict["modified"]
        del metadatadict["court"]
        del metadatadict["casenum"]
        del metadatadict["id"]

        # Clean up any other None value keys
        for k, v in metadatadict.items():
            if not v:
                del metadatadict[k]

        self.add_document(docnum,
                          subdocnum,
                          metadatadict)

    ### Not used.
    # def update_document(self, docnum_s, subdocnum_s="0", metadict={}):
    # ''' Merge document-level metadata with pairs in metadict. '''
    #
    # dockey = "%s-%s" % (unicode(docnum_s), unicode(subdocnum_s))
    # for k,v in metadict.items():
    # metadict[k] = unicode(v)
    #        self.documents[dockey].update(metadict)

    def get_document_metadict(self, docnum, subdocnum):
        dockey = "%s-%s" % (unicode(docnum), unicode(subdocnum))
        return self.documents[dockey]

    def set_document_available(self, docnum, subdocnum, flag):
        dockey = "%s-%s" % (unicode(docnum), unicode(subdocnum))
        try:
            self.documents[dockey]["available"] = flag
        except KeyError:
            self.add_document(docnum, subdocnum, {"available": flag})

    def get_document_sha1(self, docnum, subdocnum):
        dockey = "%s-%s" % (unicode(docnum), unicode(subdocnum))
        try:
            return self.documents[dockey]["sha1"]
        except KeyError:
            return ""

    def remove_document(self, docnum_s, subdocnum_s="0"):
        """ Remove a document from the list. """

        dockey = "%s-%s" % (unicode(docnum_s), unicode(subdocnum_s))

        try:
            del self.documents[dockey]
        except KeyError:
            pass

    def add_party(self, metadict=None):
        if not metadict:
            metadict = {}
        if metadict:
            self.parties.append(metadict)

    def update_parties(self, party_list=None):
        if not party_list:
            party_list = []
        if party_list:
            if not self.parties:
                self.parties = party_list
            elif self.parties == party_list:
                return
            else:
                # I feel there has to be a more efficient way to do this:
                for party in party_list:
                    index = self.find_party_index_by_name(party.get("name"))

                    if index is not None:
                        self.parties[index].update(party)
                    else:
                        self.parties.append(party)

    def find_party_index_by_name(self, name=""):
        for i, s in enumerate(self.parties):
            if s.get("name") == name:
                return i

        return None

    def update_case(self, metadict={}):
        """ Merge case-level metadata with pairs in metadict. """

        for k, v in metadict.items():
            metadict[k] = unicode(v)
        self.casemeta.update(metadict)

    def merge_docket(self, new_docket):
        """ Merges contents of new_docket into this docket. """

        # Sanity check that these two dockets are from the same case
        if self.get_court() != new_docket.get_court() or \
                        self.get_casenum() != new_docket.get_casenum():
            logging.error(
                "merge_docket failed sanity check: (%s,%s) != (%s %s)"
                % (self.get_court(), self.get_casenum(),
                   new_docket.get_court(),
                   new_docket.get_casenum()))

        # Merge case metadata
        self.update_case(new_docket.casemeta)

        # Merge parties metadata
        try:
            self.update_parties(new_docket.parties)
        except AttributeError:
            self.update_parties([])

        # Merge document metadata
        for dockey in new_docket.documents.keys():

            try:
                self.documents[dockey].update(new_docket.documents[dockey])
            except KeyError:
                self.documents[dockey] = new_docket.documents[dockey]

    def get_root(self):
        """ Actually create and return the nested Element. """

        root = Element("gov_uscourts_docket")

        # Create nonce element.
        SubElement(root, "nonce").text = self.nonce

        # Create basic case info.
        case_e = SubElement(root, "case_details")
        # We need a specific ordering.
        case_keys = ["court", "docket_num", "case_name",
                     "pacer_case_num", "date_case_filed",
                     "date_case_terminated", "date_last_filing",
                     "assigned_to", "referred_to", "case_cause",
                     "nature_of_suit", "jury_demand", "jurisdiction",
                     "demand", ]

        for k in case_keys:
            try:
                SubElement(case_e, k).text = unicode(self.casemeta[k])
            except KeyError:
                pass

        try:
            if self.parties:
                pass
        except AttributeError:
            self.parties = []

        # Create list of attorneys, if it exists
        if self.parties:
            parties_e = SubElement(root, "party_list")
            party_meta_keys = ["name", "type", "extra_info"]
            for party in self.parties:
                party_e = SubElement(parties_e, "party")

                for p_key in party_meta_keys:
                    try:
                        SubElement(party_e, p_key).text = unicode(party[p_key])
                    except KeyError:
                        pass

                    except ValueError:  # lxml doesn't like hex escape chars
                        try:
                            printable_characters_only = "".join(
                                [char for char in party[p_key] if
                                 char in string.printable])
                            SubElement(party_e, p_key).text = unicode(
                                printable_characters_only)
                        except ValueError:
                            pass

                try:
                    attorneys_list = party["attorneys"]
                except KeyError:
                    pass

                else:

                    if attorneys_list:
                        attorneys_e = SubElement(party_e, "attorney_list")
                        att_meta_keys = ["attorney_name", "contact",
                                         "attorney_role"]

                        for attdict in attorneys_list:

                            att_e = SubElement(attorneys_e, "attorney")
                            for att_meta_key in att_meta_keys:
                                try:
                                    SubElement(att_e,
                                               att_meta_key).text = unicode(
                                        attdict[att_meta_key])
                                except KeyError:
                                    pass

        # Create list of documents.
        documents_e = SubElement(root, "document_list")
        doc_meta_keys = ["pacer_doc_id", "pacer_de_seq_num", "pacer_dm_id",
                         "date_filed", "date_entered", "long_desc",
                         "short_desc", "upload_date", "available", "sha1",
                         "free_import"]

        for doc_key in sorted(self.documents.keys(), dockey_compare):
            doc_e = SubElement(documents_e, "document")
            doc_e.set("doc_num",
                      unicode(self.documents[doc_key]["doc_num"]))
            doc_e.set("attachment_num",
                      unicode(self.documents[doc_key]["attachment_num"]))
            for doc_meta_key in doc_meta_keys:
                try:
                    SubElement(doc_e, doc_meta_key).text = \
                        unicode(self.documents[doc_key][doc_meta_key])
                except (KeyError, ValueError):
                    pass

        return root

    def to_xml(self):
        retstr = '<?xml version="1.0" encoding="utf-8"?>\n'
        retstr += '<!DOCTYPE gov_uscourts_docket ' + \
                  'SYSTEM "docket.dtd">\n'
        retstr += tostring(
            self.get_root(),
            encoding='utf-8',
            pretty_print=True
        )
        return retstr

    def to_html(self):
        """ Transforms XML to HTML using the docket XSLT """

        xml_string = self.to_xml()

        # Read the XSL file.
        xslfile = open(XSL_PATH)
        docket_xsl = parse(xslfile)
        xslfile.close()

        # Do the XML->HTML transform
        docket_xsl_transform = XSLT(docket_xsl)

        xmldoc = parse(StringIO.StringIO(xml_string))
        html = unicode(
            docket_xsl_transform(
                xmldoc,
                DEV_BUCKET_PREFIX="'%s'" % settings.DEV_BUCKET_PREFIX,
            )
        ).encode("utf-8")

        return html


def dockey_compare(key1, key2):
    """ Compare two dockeys, for sorting dockeys. """
    key1docnum, key1subdocnum = key1.split("-")
    key2docnum, key2subdocnum = key2.split("-")
    if key1docnum != key2docnum:
        return int(key1docnum) - int(key2docnum)
    else:
        return int(key1subdocnum) - int(key2subdocnum)


def parse_xml_string(xml_string):
    """ Parse an existing docket XML string and return the DocketXML object.
    """

    # TK: DTD validation
    try:
        root = fromstring(xml_string)
    except XMLSyntaxError, e:
        # Validation error, try replacing & with &amp;
        new_string = re.sub("&(?!(quot|amp|apos|lt|gt);)", "&amp;", xml_string)
        try:
            root = fromstring(new_string)
        except XMLSyntaxError, e:
            return None, e.message
        else:
            return do_parse_xml(root), ""
    else:
        return do_parse_xml(root), ""


def do_parse_xml(root):
    casemeta = {}

    # Parse the case_details
    case_e = root.find("case_details")

    for node in case_e:
        try:
            casemeta[node.tag] = node.text.strip()
        except AttributeError:
            casemeta[node.tag] = ''

    docket = DocketXML(casemeta["court"],
                       casemeta["pacer_case_num"],
                       casemeta)

    # Parse the nonce
    try:
        docket.nonce = root.find("nonce").text.strip()
    except AttributeError:  # There's no nonce
        docket.nonce = None

    # Parse the parties list

    parties_e = root.find("party_list")

    if parties_e is not None:
        for party_e in parties_e:
            partymeta = {}

            for node in party_e:

                # Each party optionally contains an attorney list, with info
                # on each attorney
                if node.tag == "attorney_list":
                    partymeta["attorneys"] = []

                    for att_e in node:
                        attmeta = {}

                        for att_info_node in att_e:
                            attmeta[
                                att_info_node.tag] = att_info_node.text.strip()

                        if attmeta:
                            partymeta["attorneys"].append(attmeta)

                else:
                    partymeta[node.tag] = node.text.strip()

            docket.add_party(partymeta)

    # Parse the document_list
    documents_e = root.find("document_list")
    for doc_e in documents_e:

        docmeta = {}

        for (attr_key, attr_val) in doc_e.items():
            docmeta[attr_key] = attr_val.strip()

        for node in doc_e:
            # Harlan: is this OK?
            try:
                docmeta[node.tag] = node.text.strip()
            except AttributeError:
                pass

        docket.add_document(docmeta["doc_num"],
                            docmeta["attachment_num"], docmeta)

    return docket


def generate_new_nonce():
    return "".join([random.choice(string.letters + string.digits)
                    for _ in xrange(6)])


def make_docket_for_pdf(filebits, court, casenum, docnum, subdocnum,
                        available=1, free_import=0):
    """ Get a new DocketXML that has this document. """

    lastdate = datetime.datetime.now().replace(microsecond=0).isoformat(" ")

    docket = DocketXML(court, casenum)

    docmeta = {"available": available, "upload_date": lastdate,
               "free_import": free_import}
    if filebits:
        sha1 = get_sha1(filebits)
        docmeta["sha1"] = sha1

    docket.add_document(docnum, subdocnum, docmeta)

    return docket


def get_sha1(filebits):
    """ Get the SHA1 for these filebits """

    h = hashlib.sha1()
    h.update(filebits)
    return h.hexdigest()


if __name__ == "__main__":
    # Here is a basic case:

    court = "cand"
    pacer_case_num = 12345
    casemeta = {"case_name": "Plantiff v. Defendant",
                "official_case_num": "3:06-cv-12345",
                "date_case_filed": "2009-01-05"}

    # Create a new docket with simple metadata
    docket = DocketXML(court, pacer_case_num, casemeta)

    # Add some more case metadata
    morecasemeta = {"date_last_filing": "2009-04-02"}
    docket.update_case(morecasemeta)

    # Add attorney metadata
    attorney1 = {"representing": "Probably Guilty",
                 "contact": "Some Schmuck & Another Schmuck>>>"}
    attorney2 = {"representing": "Probably Clean",
                 "contact": "Still A. Schmuck"}

    docket.add_attorney(attorney1)
    docket.add_attorney(attorney2)

    # Some document metadata
    docmeta1 = {"pacer_doc_id": "11111",
                "pacer_de_seq_num": "1111",
                "pacer_dm_id": "111"}
    docmeta2 = {"pacer_doc_id": "22222",
                "pacer_de_seq_num": "2222",
                "pacer_dm_id": "222"}

    # Add three documents
    docnum = 1
    docket.add_document(docnum, meta_dict=docmeta1)
    docnum = 2
    subdocnum = 1
    docket.add_document(docnum, subdocnum, meta_dict=docmeta2)
    subdocnum = 2
    docket.add_document(docnum, subdocnum)

    # The output XML string
    xml_string = docket.to_xml()
    print xml_string

    # The output HTML string
    html_string = docket.to_html()
    print html_string

    # Read it back in to check parsing.
    docket2, err = parse_xml_string(xml_string)
    xml_string2 = docket2.to_xml()

    print xml_string2
    print xml_string == xml_string2

    # Test merging new docket into old docket

    docket3 = DocketXML(court, pacer_case_num,
                        {"date_case_terminated": "2009-04-03",
                         "date_last_filing": "2009-04-10"})
    docket3.add_document(2, 3)
    docket3.add_document(2, 4)
    # Should be a no-op
    docket3.add_attorney({"representing": "Innocent",
                          "contact": "!@#$%^&*() Princeton"})

    docket2.merge_docket(docket3)

    print docket2.to_xml()

    docket2.remove_document(2, 4)
    docket2.remove_document(2, 1)

    parse_xml_string(docket2.to_xml())

