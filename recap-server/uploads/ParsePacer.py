
import re
import datetime
import logging


from BeautifulSoup import BeautifulSoup, HTMLParseError, Tag, NavigableString

import DocketXML
try:
    from settings import ROOT_PATH
except ImportError:
    pass
else:
    BASE_ERROR_JAR = ROOT_PATH + "/errorjar"

def coerce_docid(docid):
    """ Some PACERs use the fourth digit of the docid to flag whether
        the user has been shown a receipt page. We don't care about that,
        so we coerce the fourth digit to be 0 before inserting it into
        the database.
    """
    return docid[:3]+"0"+docid[4:]

def parse_dktrpt(filebits, court, casenum):

    docket = DocketXML.DocketXML(court, casenum)

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

        filebits = filebits.replace("</font color=red>",
                                    "</font>")
        try:
            the_soup = BeautifulSoup(filebits, convertEntities="html")
        except HTMLParseError, err:

            message = "DktRpt parse error. %s.%s %s line: %s char: %s." % \
                (court, casenum, err.msg, err.lineno, err.offset)
            logging.warning(message)

            filename = "%s.%s.dktrpt" % (court, casenum)
            try:
                error_to_file(filebits, filename)
            except NameError:
                pass

            return None

    rows, doctable = _parse_dktrpt_document_table(the_soup, court)

    for row in rows:
        # Pass the first (and hopefully only) link in the "#" column
        docmeta = _parse_dktrpt_table_row(row, casenum)

        try:
            # Update the docket object with doc metadata
            docket.add_document(docmeta["doc_num"],
                                docmeta["attachment_num"],
                                docmeta)

        except KeyError:
            # HTML link did not parse correctly, so no doc add to docket.
            pass

    try:
        # Remove doctable from the_soup so _get_case_metadata won't look there.
        doctable.extract()
    except AttributeError:
        pass

    case_data = _get_case_metadata_from_dktrpt(the_soup, court)

    # Update the docket object with the parsed case meta
    docket.update_case(case_data)

    parties = _get_parties_info_from_dkrpt(the_soup, court)

    if parties:
        docket.update_parties(parties)
#    else:
#       logging.debug("Could not find parties in docket!")


    return docket


def parse_histdocqry(filebits, court, casenum):

    docket = DocketXML.DocketXML(court, casenum)

    try:
        docket_soup = BeautifulSoup(filebits, convertEntities="html")

    except TypeError:
        # Catch bug in BeautifulSoup: tries to concat 'str' and 'NoneType'
        #  when unicode coercion fails.
        message = "HistDocQry BeautifulSoup error %s.%s" % \
            (court, casenum)
        logging.warning(message)

        filename = "%s.%s.histdocqry" % (court, casenum)
        try:
            error_to_file(filebits, filename)
        except NameError:
            pass

        return None

    except HTMLParseError, err:
        message = "HistDocQry parse error. %s.%s %s line: %s char: %s." % \
            (court, casenum, err.msg, err.lineno, err.offset)
        logging.warning(message)

        filename = "%s.%s.histdocqry" % (court, casenum)
        try:
            error_to_file(filebits, filename)
        except NameError:
            pass

        return None

    docmeta_list, doctable = _parse_histdocqry_document_table(docket_soup,
                                                              court)

    for docmeta in docmeta_list:

        try:
            # Update the docket object with doc metadata
            docket.add_document(docmeta["doc_num"],
                                docmeta["attachment_num"],
                                docmeta)
        except KeyError:
            # HTML link did not parse correctly, so no doc add to docket.
            pass

    try:
        # Remove doctable from the_soup so _get_case_metadata won't look there.
        doctable.extract()
    except AttributeError:
        pass

    case_data = _get_case_metadata_from_histdocqry(docket_soup, court)

    # Update the docket object with the parsed case meta
    docket.update_case(case_data)

    return docket


def parse_doc1(filebits, court, casenum, main_docnum):

    docket = DocketXML.DocketXML(court, casenum)


    try:
        index_soup = BeautifulSoup(filebits, convertEntities="html")

    except TypeError:
        # Catch bug in BeautifulSoup: tries to concat 'str' and 'NoneType'
        #  when unicode coercion fails.
        message = "doc1 BeautifulSoup error %s.%s.%s" % \
            (court, casenum, main_docnum)
        logging.warning(message)

        filename = "%s.%s.%s.doc1" % (court, casenum, main_docnum)
        try:
            error_to_file(filebits, filename)
        except NameError:
            pass

        return None

    except HTMLParseError:
        # Adjust for malformed HTML.  Wow, PACER.
        filebits = filebits.replace("FORM method=POST ACTION=\\",
                                    "FORM method=POST ACTION=")
        try:
            index_soup = BeautifulSoup(filebits, convertEntities="html")
        except HTMLParseError, err:
            message = "doc1 parse error. %s.%s.%s %s line: %s char: %s." % \
                (court, casenum, main_docnum, err.msg, err.lineno, err.offset)
            logging.warning(message)

            filename = "%s.%s.%s.doc1" % (court, casenum, main_docnum)
            try:
                error_to_file(filebits, filename)
            except NameError:
                pass

            return None

    links = index_soup.findAll("a")

    docre = re.compile(r"^.*\.(\w*)\.uscourts\.gov\/(.*)\/(\w*)$")

    is_v4 = False

    for link in links:
        try:
            uri = link['href']
        except KeyError: # No href location.
            continue

        docmatch = docre.match(uri)

        if docmatch:

            try:
                subdocnum = int(link.contents[0].strip())
            except (KeyError, ValueError):
                # No link text or not an integer
                continue

            court = docmatch.group(1)
            directory = docmatch.group(2)
            docid = coerce_docid(docmatch.group(3))

            # Check if it's v4 for subdocnum conversion.
            # If this is a v4 doc1 page, no conversion needed.
            if not is_v4:

                # See if the main document has a v4-style "Document number:"
                #   heading in front of it.
                textSiblings = link.parent.findAll(text=re.compile(".*"))
                for sibling in textSiblings:
                    sibling = unicode(sibling).lower().strip()
                    if sibling.find("document number") != -1:
                        is_v4 = True
                        # Skip the main document- already know about it.
                if is_v4:
                    continue

                # Otherwise, this is a v3 docket.
                # Skip the main document (#1)- already know about it
                if subdocnum == 1:
                    continue
                else:
                    # Otherwise, convert v3->v4 style subdocnums
                    subdocnum = subdocnum-1

            # TK: if we need to, we can get de_seq_num here.
            #      it is the 3rd argument to the goDLS onclick().

            # Get short description
            try:
                short_desc = link.parent.findNextSibling("td").string
                short_desc = short_desc.strip()
            except AttributeError:
                # No short description
                docket.add_document(main_docnum, subdocnum,
                                    {"pacer_doc_id": docid})
            else:
                docket.add_document(main_docnum, subdocnum,
                                    {"pacer_doc_id": docid,
                                     "short_desc": short_desc})

    # Try to get officialcasenum from Pacer Service Center Receipt
    case_data = _get_case_metadata_from_pacer_receipt_table(index_soup, court)

    # Update the docket object with the parsed case meta
    docket.update_case(case_data)

    return docket

def parse_opinions(filebits, court):
    if not filebits:
        return []

    the_soup = _open_soup(filebits, court, "multi", "opinions")
    dockets = _parse_opinion_report_table(the_soup, court)


    return dockets

def _parse_opinion_report_table(the_soup, court):
    dockets = []

    opinion_table = None
    #Assume the first table is the right table
    tables = the_soup.findAll('table')

    for table in tables:
        try:
            first_row = table('tr')[0]
        except IndexError:
            continue

        for cell in first_row(["td", "th"]):
            if cell.string == 'Case Number & Name:':
                opinion_table = table
                break

    if opinion_table == None:
        return dockets

    rows = opinion_table.findAll('tr')
    headers = [cell.string for cell in rows[0].findAll('th')]

    if len(headers) != 5:
        raise "Unexpected number of headers!: %s" % str(headers)

    casenum_re = re.compile(r'/cgi-bin/DktRpt.pl\?(\d+)')
    iquery_casenum_re = re.compile(r'/cgi-bin/iquery.pl\?.*-(\d+)$')

    for row in rows[1:]:
        #for each row, we'll create a docket and a document
        document = {} #initialize with court?
        case_data = {}

        casenum = None
        cells = row.findAll('td')

        #I've only observed 'Cause and NOS' so far
        #Caseflags and Office are two other often included keys
        notes_metadict= { "assigned_to" : r"Assigned to: *(.*)$",
                          "referred_to" : r"Referred to: *(.*)$",
                          "case_cause" : r"Cause: *(.*)$",
                          "nature_of_suit" : r"NOS: *(.*)$",
                          "jury_demand": r"Jury Demand: *(.*)$",
                          "jurisdiction": r"Jurisdiction: *(.*)$",
                          "demand": r"^Demand: *(.*)$"
        }

        for index, cell in enumerate(cells):
            key = headers[index]
            if key == 'Case Number & Name:':
                #these are required for frontend, so strips() should fail loudly
                case_data['case_name'] = cell.b.string.strip()
                match = casenum_re.search(cell.a['href'])
                if not match:
                    match = iquery_casenum_re.search(cell.a['href'])
                # If there's no match the following line will fail loudly
                # this is good.
                casenum = match.group(1)
                case_data['docket_num'] = cell.a.string.strip()
            elif key == 'Doc. #':
                document["doc_num"] = cell.a.string.strip()
                document["attachment_num"] = '0' # assume all docs are primary

                linkstring = cell.a['href']
                args = re.split(r'&', linkstring)
                for s in args:
                    (k, v) = re.split(r'=', s)
                    if(k == 'de_seq_num'):
                        document['pacer_de_seq_num'] = v
                    if(k == 'dm_id'):
                        document['pacer_dm_id'] = v
                    # this value may differ from the docket casenum, this is okay
                    if re.match(r'^.*caseid$', k):
                        document['casenum'] = v
            elif key == 'Date Filed:':
                datestr = cell.string
                try:
                    month, day, year = datestr.split("/")
                    document["date_filed"]= datetime.date(int(year),
                                            int(month),
                                            int(day)).isoformat()
                except ValueError: #sometimes there will be a blank date filed space
                    #TK: find a better default value
                    document["date_filed"] = datetime.date.today()

            elif key == 'Description:':
                document["long_desc"] = "".join(cell.findAll(text=True))
            elif key == 'Notes:':
                # optional case level metadata
                for k, v in notes_metadict.items():
                    metadata_entry = _get_simple_metadata_following_regex(cell, v)
                    if metadata_entry:
                        case_data[k] = metadata_entry


        # sanity checks
        if casenum == None:
            raise "Casenum is none for the following row: %s" % str(row)

        required_dockeys = ['doc_num', 'pacer_de_seq_num', 'pacer_dm_id']

        for key in required_dockeys:
            if document.get(key) == None:
                raise "Could not find required key %s for document: %s" (key, str(document))

        docket = DocketXML.DocketXML(court, casenum, case_data)
        docket.add_document(document["doc_num"], document["attachment_num"], document)

        dockets.append(docket)

    return dockets


def _open_soup(filebits, court, casenum="unknown", called_from=""):
    try:
        the_soup = BeautifulSoup(filebits, convertEntities="html")
    except TypeError:
        # Catch bug in BeautifulSoup: tries to concat 'str' and 'NoneType'
        #  when unicode coercion fails.
        message = "%s BeautifulSoup error %s.%s" % \
            (called_from, court, casenum)
        logging.warning(message)

        filename = "%s.%s.%s" % (court, casenum, called_from)
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
        filebits = filebits.replace("</font color=red>",
                                    "</font>")
        try:
            the_soup = BeautifulSoup(filebits, convertEntities="html")
        except HTMLParseError, err:

            message = "%s parse error. %s.%s %s line: %s char: %s." % \
                (called_from, court, casenum, err.msg, err.lineno, err.offset)
            logging.warning(message)

            filename = "%s.%s.%s" % (court, casenum, called_from)
            try:
                error_to_file(filebits, filename)
            except NameError:
                pass

            return None
    return the_soup



def _get_case_metadata_from_pacer_receipt_table(the_soup, court):
    # The only real metadata available is the docket_num (officialcasenum)
    case_data = {}

    court_bankruptcy_re = re.compile("b-|b$")

    if court_bankruptcy_re.search(court):
        # we're dealing with a bankruptcy court
        case_code_re = re.compile(r"#: (\d\d-\d*)")
    else:
        case_code_re = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

    case_codes = the_soup.findAll(text = case_code_re)
    if len(case_codes) == 0:
        return {}

    ocn_match = case_code_re.search(case_codes[0])

    if ocn_match:
        case_data["docket_num"] = ocn_match.group(1)

    return case_data



# Finds the first table in the_soup that contains a column labeled "#", and
# returns a list of dicts where each dict represents one row in the table.
# Within those dicts, the items labeled "number," "date," and "text" provide
# the contents of the corresponding cells.

def _parse_dktrpt_document_table(the_soup, court):

    headers = {"#": "number", "Date Filed": "date", "Filing Date": "date",
               "Docket Text":"text"}

    tables = the_soup.findAll('table')

    for table in tables:

        columns = []

        try:
            first_row = table("tr")[0]
        except IndexError:
            # No rows available in this table.
            continue

        for cell in first_row(["td","th"]):
            column_token = None
            for k in headers.keys():
                if cell.string == k:
                    # Fix-up for bankruptcy tables
                    if k == "#":
                        for (attr_key, attr_val) in cell.attrs:
                            if attr_key == "colspan" and attr_val == "2":
                                columns.append("empty")
                    column_token = headers[k]

            columns.append(column_token)

        # We hope that every table we parse will have a "number" column,
        # which contains the docnum and the link to the document, so we use
        # that to identify the "right" table.

        if "number" in columns:
            cell_list = []

            for row in table("tr")[1:]:
                row_values = {}
                cells = row(["td","th"])
                for cell, column in zip(cells, columns):
                    if column:
                        row_values[column] = cell

                cell_list.append(row_values)
            return cell_list, table

    return [], None

def _parse_histdocqry_document_table(the_soup, court):

    # Find the main doc table.
    tables = the_soup.findAll('table')

    doctable = None

    for table in tables:

        headers = table.find("tr").findAll("th")
        try:
            if headers[0].contents[0].strip() == "Doc.":
                doctable = table
                break
        except (TypeError, IndexError):
            continue

    if not doctable:
        return [], None

    # Found the doc table.

    docmeta_list = []

    rows = doctable.findAll("tr", recursive=False)
    for row in rows[1:]:

        docmeta = {}

        columns = row.findAll("td", recursive=False)

        if len(columns) != 3:  # 3 columns: [Doc.No., Dates, Description]
            continue

        # First column: get docnum and docid.

        link = columns[0].find("a")

        if link:
            # Get it from the link to the doc1 page

            docrev3 = re.compile(r"^.*\.(\w*)\.uscourts\.gov\/(.*)\/(\w*)$")
            docrev4 = re.compile(r"^\/cgi-bin\/show_doc\.pl\?(.*)$")
            uri = link['href']

            docmatchv3 = docrev3.match(uri)
            docmatchv4 = docrev4.match(uri)

            try:
                docnum = int(link.contents[0])  # The "link number"
            except ValueError:
                # Link text is not an int.
                continue

            docmeta["doc_num"] = unicode(docnum)
            docmeta["attachment_num"] = 0    # Primary document

            if docmatchv3:

                court = docmatchv3.group(1)        # TK: Unused
                directory = docmatchv3.group(2)    # TK: Unused, usually "doc1"

                docid = coerce_docid(docmatchv3.group(3))
                docmeta["pacer_doc_id"] = docid

            elif docmatchv4:

                args = re.split(r'&', docmatchv4.group(1))

                for s in args:
                    (k,v) = re.split(r'=',s)
                    k = k.encode('utf-8')
                    if(k == 'de_seq_num'):
                        docmeta['pacer_de_seq_num'] = v
                    if(k == 'dm_id'):
                        docmeta['pacer_dm_id'] = v
                    if(k == 'doc_num'):
                        docmeta['doc_num'] = v

        else:
            # No link, just see if there is a docnum.

            docnumseq = columns[0].findAll(text=re.compile(".*"))
            docnumstr = "".join(docnumseq).strip()

            try:
                docnum = int(docnumstr)
            except ValueError:
                # No docnum... skip this row.
                continue
            else:
                docmeta["doc_num"] = unicode(docnum)
                docmeta["attachment_num"] = 0


        # Get Filed and Entered dates
        daterows = columns[1].table.findAll("tr")
        for daterow in daterows:

            datestr = daterow.findAll("td")[1].string
            month, day, year = datestr.split("/")
            datestr = datetime.date(int(year),
                                    int(month),
                                    int(day)).isoformat()

            if daterow.find(text=re.compile("^Filed:")):
                docmeta["date_filed"] = datestr
            elif daterow.find(text=re.compile("^Entered:")):
                docmeta["date_entered"] = datestr
            elif daterow.find(text=re.compile("^Filed.*Entered:")):
                docmeta["date_filed"] = datestr
                docmeta["date_entered"] = datestr

        # Get short description
        short_desc_col = columns[2]

        if len(short_desc_col.contents) == 1:  # No silverball
            short_desc = short_desc_col.string
            if short_desc:
                docmeta["short_desc"] = short_desc.strip()
        else: # Has silverball link
            try:
                short_desc = short_desc_col.findNext('a').nextSibling
            except AttributeError:
                # No nextSibling short description text
                pass
            else:
                try:
                    short_desc = short_desc.strip()
                except AttributeError:
                    # This element is not a string
                    pass
                else:
                    if short_desc: # not empty
                        docmeta["short_desc"] = short_desc

        # Get long description, if available
        long_desc_row = row.findNextSibling("tr")

        if long_desc_row:
            if long_desc_row.find(text=re.compile("Docket Text")):
                long_desc_seq = \
                    long_desc_row.findAll(text=re.compile(".*"))
                docmeta["long_desc"] = \
                    "".join(long_desc_seq[1:]).strip()
        docmeta_list.append(docmeta)

    return docmeta_list, doctable


def _get_case_metadata_from_dktrpt(the_soup, court):

    case_data = {}

    court_bankruptcy_re = re.compile("b-|b$")

    if court_bankruptcy_re.search(court):

        # we're dealing with a bankruptcy court

        case_code_re = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

        case_codes = the_soup.findAll(text = case_code_re)
        if len(case_codes) == 0:
            #Some bankruptcy court cases look different
            case_code_re = re.compile(r"#: ((\d-)?\d\d-\d*)")
            case_codes = the_soup.findAll(text = case_code_re)

            if len(case_codes) == 0:
                return {}

        ocn_match = case_code_re.search(case_codes[0])

        if ocn_match:
            case_data["docket_num"] = ocn_match.group(1)

        # The case name is found after <I><B>Debtor</B></I><BR>
        s = the_soup.find(text=re.compile(r"^\s*Debtor(\s*In Possession)?\s*$"))

        try:
            s = s.parent.parent.nextSibling.nextSibling
        except AttributeError:
            try:
                s = s.parent.parent.parent.parent.nextSibling
            except AttributeError:
                s = None

        if s:
            debtor_text = s.find(text=re.compile(".*"))
            if debtor_text:
                case_data["case_name"] = debtor_text.strip().strip(",")
            else:
                case_data["case_name"] = "Unknown Bankruptcy Case Title"
        else:
            # This is probably a sub docket to a larger case
            lead_bk = the_soup.find(text=re.compile(r"Lead BK Title:"))

            if lead_bk:
                lead_bk_text = lead_bk.next.string.strip()
                if the_soup.find(text=re.compile(r'Adversary Proceeding')):
                    suffix_text = "- Adversary Proceeding"
                else:
                    suffix_text = "- Unknown Proceeding"

                case_data["case_name"] = lead_bk_text + suffix_text
            else:
                if the_soup.find(text=re.compile(r'Adversary Proceeding')):
                    case_data["case_name"] = "Adversary Proceeding - Docket #" + case_data["docket_num"]
                else:
                   case_data["case_name"] = "Unknown Bankruptcy Case Title"

    else:
        # we're dealing with a district court

        case_code_re = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

        case_codes = the_soup.findAll(text = case_code_re)

        if len(case_codes) == 0:
            return {}

        ocn_match = case_code_re.search(case_codes[0])

        if ocn_match:
            case_data["docket_num"] = ocn_match.group(1)

        # A case name is any string of words and white space with the
        # string " v. " in the middle of it.

        case_name_re = re.compile(r"^(.*\:)?([^\:]*\sv\.\s.*)$")
        case_names = the_soup.findAll(text=case_name_re)

        inre_name_re = re.compile(r"^(.*\:)?([^\:]*(\s)?IN\sRE\:\s.*)$",
                                  re.IGNORECASE)
        inre_names = the_soup.findAll(text=inre_name_re)

        if case_names:
            casename_match = case_name_re.search(case_names[0])

            try:
                case_data["case_name"] = casename_match.group(2).strip()
            except AttributeError:
                pass

        elif inre_names:
            # Try a "In re:" name

            inre_match = inre_name_re.search(inre_names[0])

            try:
                case_data["case_name"] = inre_match.group(2).strip()
            except AttributeError:
                pass


    # Dates are listed with a title followed by a MM-DD-YYYY string

    s = the_soup.find(text=re.compile(r"Date [Ff]iled:"))

    if s:

        date_re = re.compile(r"(\d\d)\/(\d\d)\/(\d\d\d\d)")
        date_match = date_re.search(s.string)

        if not date_match:
            d = s.parent.nextSibling
            if d:
                date_match = date_re.search(unicode(d.string))

        if not date_match:
            # this finds date text for bankruptcy courts
            d2 = s.parent.parent.nextSibling
            if d2:
                date_match = date_re.search(unicode(d2.string))

        if not date_match:
            # Some cases are weird
            d3 = s.next
            if d3:
               date_match = date_re.search(unicode(d3))


        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year =  int(date_match.group(3))
            try:
                case_data["date_case_filed"] = \
                    datetime.date(year,month,day).isoformat()
            except ValueError:
                # passed in bad value for datetime, ignore.
                pass
        else:
            # Sometimes pacer uses two digit years
            two_digit_date_re = re.compile(r"(\d\d\/\d\d\/\d\d)")

            if d:
                date_match = two_digit_date_re.search(unicode(d.string))
            if (not date_match) and d2:
                date_match = two_digit_date_re.search(unicode(d2.string))

            if date_match:
                try:
                    case_data["date_case_filed"] = \
                       datetime.datetime.strptime(date_match.group(1), "%m/%d/%y").date().isoformat()
                except ValueError:
                    # give up
                    pass

    s = the_soup.find(text=re.compile(r"Date [Tt]erminated:"))

    if s:

        date_re = re.compile(r"(\d\d)\/(\d\d)\/(\d\d\d\d)")
        date_match = date_re.search(s.string)

        if not date_match:
            d = s.parent.nextSibling
            if d:
                date_match = date_re.search(unicode(d.string))

        if not date_match:
            # this finds date text for bankruptcy courts
            d = s.parent.parent.nextSibling
            if d:
                date_match = date_re.search(unicode(d.string))

        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year =  int(date_match.group(3))
            try:
                case_data["date_case_terminated"] = \
                    datetime.date(year,month,day).isoformat()
            except ValueError:
                # passed in bad value for datetime, ignore.
                pass

    simplemetadict = { "assigned_to" : r"Assigned to: *(.*)$",
                       "referred_to" : r"Referred to: *(.*)$",
                       "case_cause" : r"Cause: *(.*)$",
                       "nature_of_suit" : r"Nature of Suit: *(.*)$",
                       "jury_demand": r"Jury Demand: *(.*)$",
                       "jurisdiction": r"Jurisdiction: *(.*)$",
                       "demand": r"^Demand: *(.*)$"
                     }

    for k,v in simplemetadict.items():
        metadata_entry = _get_simple_metadata_following_regex(the_soup, v)
        if metadata_entry:
            case_data[k] = metadata_entry
#           logging.debug("%s: %s" % (k, case_data[k]))
#       else:
#            logging.debug("Couldn't find %s in %s" % (k, court))


    return case_data

#Try to parse out the individual parties and their attorneys
def _get_parties_info_from_dkrpt(the_soup, court):
    parties = []

    court_bankruptcy_re = re.compile("b-|b$")

    # Bankruptcy courts have slightly different formats, as we will see
    is_bankruptcy = court_bankruptcy_re.search(court)

    # Compiling some regexes that we'll use a few times below
    dash_separator = re.compile(r"^-----*$")
    represented_by = re.compile(r"^represented\sby\s*", re.UNICODE)

    # We use this search to find at least one valid entry from the parties table
    party_set= the_soup.findAll(text = re.compile(r"Defendant|Plaintiff|Petitioner|Respondent|Debtor|Trustee|Mediator|Creditor Committee|Intervenor|Claimant"))

    parties_rows = []
    for entry in party_set:
       if is_bankruptcy:
           valid_party = (entry.parent.name == u"b" and entry.parent.parent.name == u"i")
           is_adversary = False

           if not valid_party:
               # Adversary Proceedings have different party format
               valid_party = (entry.parent.name == u"b" and dash_separator.match(entry.next.next))
               is_adversary = valid_party
       else:
           valid_party = (entry.parent.name == u"u" and entry.parent.parent.name == u"b")
           is_adversary = False

       if valid_party:
           parties_rows = entry.findParent('table').findAll('tr')
           break


    if parties_rows:

        for row in parties_rows:
            party_cols = row.findAll('td')

            if len(party_cols) == 0:
                continue

            if len(party_cols) == 1:
                # Sometimes, PACER has a row with one empty td element
                if not row.find(text=True):
                    continue

            # Rows that contain only "V." don't give us any information, skip to next row
            if ("".join(row.findAll(text=True)).strip() == "V."):
                continue

            if is_adversary:
                new_party_type_row = row.find(text=dash_separator)

                if new_party_type_row:
                    new_party_row = False
                else:
                    if len(party_cols) == 1:
                        new_party_row = True
                    else:
                        # We can identify a new party by the text 'represented by', which appears in the second column
                        if party_cols[1]:
                            new_party_row = party_cols[1].find(text=represented_by)

            else:
                # This is either a district or normal bankruptcy
                if is_bankruptcy:
                    new_party_row = True
                    new_party_type_row = True
                else:
                    if not row.b:
                        # Some california cases put non party information in the same html table element
                        # We can ignore the row if it has no bold text, which would normally signify
                        # the party's name, or the party type
                        continue

                    if len(party_cols) == 1:
                        try:
                            new_party_type_row = row.b.u
                            new_party_row = False
                        except AttributeError:
                            pass

                        if not new_party_type_row:
                            new_party_type_row = False
                            new_party_row = True

                    elif len(party_cols) == 3:
                        new_party_row = party_cols[1].find(text=represented_by)
                        new_party_type_row = False

            if new_party_row:
                party = {}
                party["attorneys"] = []

            if len(party_cols) == 3:
                if is_bankruptcy and not is_adversary:
                    typeTag = party_cols[0].b
                    try:
                        type_string = typeTag.string.strip()
                    except AttributeError: # some adversay cases are more similar to normal bank
                        typeTag = typeTag.findNext('b')
                        type_string = typeTag.contents[0]


                    party["type"]= type_string
                    nameTag = typeTag.findNext('b')

                    if nameTag.string:
                        party["name"] = nameTag.string.strip()
                    elif nameTag.findAll(text=True):
                        party["name"] = "".join(nameTag.findAll(text=True)).strip()

                    party["extra_info"] = "".join(party_cols[0].findAll(text=True)[3:]).strip()
                else:
                    # Adversary Proceeding or district court
                    if new_party_row:
                        party["type"] = party_type
                        party["name"] = unicode(party_cols[0].b.contents[0])
                        party["extra_info"] = "".join(party_cols[0].findAll(text=True)[2:]).strip()

#               print "Party: %s - %s :: %s" % (party["type"], party["name"], party["extra_info"])
#               logging.debug( "Party: %s - %s :: %s" % (party["type"], party["name"], party["extra_info"]))


                # Attorney info - stripping all HTML tags

                if is_bankruptcy:
                    att_info = party_cols[2].font
                else:
                    att_info = party_cols[2]


                if new_party_row:
                    att_list = []

                attdict = {}

                remove_spaces_re = re.compile(r"  +")
                for node in att_info:

                    if(isinstance(node, Tag)):

                        # Save old lawyer to list, get new lawyer name
                        if node.name == 'b':
                            if attdict:
                                att_list.append(attdict)
                                #print "%s blah: " % attdict['attorney_name']

                            attdict = {}
                            if node.string:
                                attdict['attorney_name'] = node.string.strip()
                                # Remove extra spaces in between names
                                attdict["attorney_name"] = remove_spaces_re.sub(r" ", attdict["attorney_name"])

                      # Optional role information
                        elif node.name == 'i':

                            # Sometimes attorney roles are italic AND bold
                            if not node.string:
                                if node.find('b'):
                                    node = node.find('b')
                            try:
                                attdict['attorney_role'] += "\n" + node.string.strip()
                            except KeyError:
                                if node.string and node.string.strip():
                                    attdict['attorney_role'] = node.string.strip()

                    elif(isinstance(node, NavigableString)):
                        if node.string and node.string.strip():
                            try:
                                attdict['contact'] += "\n" + node.string.strip()
                                attdict['contact'] = remove_spaces_re.sub(r" ", attdict["contact"])
                            except KeyError:
                                attdict['contact'] = node.string.strip()

                try:
                    # Append final lawyer
                    if attdict:
                        att_list.append(attdict)

                    party["attorneys"] = att_list
                except NameError:
                    pass

            elif len(party_cols) == 1:

                if new_party_row:
                    party["name"] = unicode(party_cols[0].b.contents[0])

                    try: # When parties are terminated, they sometimes have no type. See txed test case
                        party["type"] = party_type
                    except NameError:
                        party["type"] = ""

                    party["extra_info"] = "".join(party_cols[0].findAll(text=True)[2:]).strip()
                else:
                    party_type = row.b.find(text=True).strip()

            else:
                #logging.debug(" Unexpected number of party columns: %s when %s" % (len(party_cols), party_cols.string))
                continue

            try:
                # Clean up blank entries
                for k, v in party.items():
                    if not v:
                        del party[k]

                if new_party_row:
                    parties.append(party)
            except NameError:
                pass

    return parties


def _get_simple_metadata_following_regex(soup, regex_string):
    metadata_re = re.compile(regex_string)
    s = soup.find(text=metadata_re)

    if not s:
        return None
    if s:
        metadata_match = metadata_re.search(s.string)
        metadata = metadata_match.group(1)

        if (not metadata):
            metadata = s.next.string;
            if not metadata:
               return None

        metadata = metadata.strip()

        return metadata



# Given a string or regexp, finds the first date string in the following DOM tree.

def _get_date_following_label(the_soup, label):

    s = the_soup.find(text=re.compile(label))

    if s:

        date_re = re.compile(r"\s+(\d\d)\/(\d\d)\/(\d\d\d\d)")
        date_fields = s.findAllNext(text=date_re);

        if len(date_fields) > 0 :
            date_match = date_re.search(date_fields[0].string)
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year =  int(date_match.group(3))

            try:
                return datetime.date(year,month,day).isoformat()
            except ValueError:
                # passed in bad value for datetime, ignore.
                pass


    return None

def _get_case_metadata_from_histdocqry(the_soup, court):

    case_data = {}

    court_bankruptcy_re = re.compile("b-|b$")

    if court_bankruptcy_re.search(court):
        # we're dealing with a bankruptcy court

        case_code_re = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

        case_codes = the_soup.findAll(text = case_code_re)
        if len(case_codes) == 0:
            #Some bankruptcy court cases look different
            case_code_re = re.compile(r"#: ((\d-)?\d\d-\d*)")
            case_codes = the_soup.findAll(text = case_code_re)
            if len(case_codes) == 0:
                return {}

        ocn_match = case_code_re.search(case_codes[0])

        if ocn_match:
            case_data["docket_num"] = ocn_match.group(1)

        text_sections = case_codes[0].findAllNext(text=True, limit=10)

        case_name = ''

        success = False

        for t in text_sections:

            if len(t.string)>2:
                case_name = t.strip()
                success = True
                break

        if success:
            case_data["case_name"] = case_name

        d = _get_date_following_label(the_soup, r"Date [Ff]iled:");
        if d:
            case_data["date_case_filed"] = d
            print "Filed", d

        d = _get_date_following_label(the_soup, r"Date [Tt]erminated:");
        if d:
            case_data["date_case_terminated"] = d
            print "Terminated", d

        d = _get_date_following_label(the_soup, r"Date of last filing:");
        if d:
            case_data["date_last_filing"] = d
            print "Filing", d

        return case_data

    else:

        case_name_re = re.compile(r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

        case_names = the_soup.findAll(text = case_name_re)

        if len(case_names) == 0:
            return case_data

        ocn_match = case_name_re.search(case_names[0])

        if not ocn_match:
            return case_data

        case_data["docket_num"] = ocn_match.group(1)

        # A case name is any string of words and white space with the
        # string " v. " in the middle of it.

        case_name_re = re.compile(r"\-\w+\s+\b([^\-]*\sv\.\s.*)$")
        casename_match = case_name_re.search(case_names[0])

        inre_name_re = re.compile(r"^.*IN\sRE\:\s.*$", re.IGNORECASE)
        inre_names = the_soup.findAll(text=inre_name_re)

        if casename_match:
            case_data["case_name"] = casename_match.group(1).strip()
        else:
            s = case_names[0].parent.nextSibling
            if not s:
                s = case_names[0].parent.parent.nextSibling

            if s:
                case_name_re = re.compile(r"(.*\sv\.\s.*)$")
                casename_match = case_name_re.search(s.string)
                try:
                    case_data["case_name"] = casename_match.group(1).strip()
                except AttributeError:
                    pass

        if inre_names and not case_data.has_key("case_name"):
            inre_match = inre_name_re.search(inre_names[0])

            try:
                case_data["case_name"] = inre_match.group(0).strip()
            except AttributeError:
                pass

        # Dates are listed with a title followed by a MM-DD-YYYY string

        s = the_soup.find(text=re.compile(r"Date [Ff]iled:"))

        if s:

            date_re = re.compile(r"\s+(\d\d)\/(\d\d)\/(\d\d\d\d)")
            date_match = date_re.search(s.string)

            if not date_match:
                d = s.parent.nextSibling
                if d:
                    date_match = date_re.search(unicode(d.string))

            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                year =  int(date_match.group(3))
                try:
                    case_data["date_case_filed"] = \
                        datetime.date(year,month,day).isoformat()
                except ValueError:
                    # passed in bad value for datetime, ignore.
                    pass

        s = the_soup.find(text=re.compile(r"Date [Tt]erminated:"))

        if s:

            date_re = re.compile(r"(\d\d)\/(\d\d)\/(\d\d\d\d)")
            date_match = date_re.search(s.string)

            if not date_match:
                d = s.parent.nextSibling
                if d:
                    date_match = date_re.search(unicode(d.string))

            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                year =  int(date_match.group(3))
                try:
                    case_data["date_case_terminated"] = \
                        datetime.date(year,month,day).isoformat()
                except ValueError:
                    # passed in bad value for datetime, ignore.
                    pass

        s = the_soup.find(text=re.compile(r"Date of last filing:"))

        if s:

            date_re = re.compile(r"(\d\d)\/(\d\d)\/(\d\d\d\d)")
            date_match = date_re.search(s.string)

            if not date_match:
                d = s.parent.nextSibling
                if d:
                    date_match = date_re.search(unicode(d.string))

            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                year =  int(date_match.group(3))
                try:
                    case_data["date_last_filing"] = \
                        datetime.date(year,month,day).isoformat()
                except ValueError:
                    # passed in bad value for datetime, ignore.
                    pass

        return case_data

def _parse_dktrpt_table_row(row, casenum):
    ''' Parse URLs of the form:
            https://ecf.laed.uscourts.gov/doc1/08501407159
        In this example, laed is the court code, and 08501407159 is the docid
    '''

    docmeta = {}

    try:
        link = row['number'].find("a")
    except KeyError:
        #logging.warning("_parse_dktrpt_table_row: row has no number link %s" %
        #                row)
        return {}

    if link:
        # Get docnum and docid from link

        docrev3 = re.compile(r"^.*\.(\w*)\.uscourts\.gov\/(.*)\/(\w*)$")
        docrev4 = re.compile(r"^\/cgi-bin\/show_doc\.pl\?(.*)$")
        uri = link['href']

        docmatchv3 = docrev3.match(uri)
        docmatchv4 = docrev4.match(uri)

        if docmatchv3:
            docmeta = {}

            try:
                docnum = unicode(int(link.contents[0]))    # The "link number"
            except IndexError:
                #logging.warning("_parse_dktrpt_table_row: link had no contents"
                #                " %s" % row)
                return {}
            except ValueError:
                #logging.warning("_parse_dktrpt_table_row: docnum not int %s" %
                #                row)
                return {}

            docmeta["doc_num"] = docnum
            docmeta["attachment_num"] = 0    # Primary document

            court = docmatchv3.group(1)        # TK: Unused
            directory = docmatchv3.group(2)    # TK: Unused, usually "doc1"

            docid = coerce_docid(docmatchv3.group(3))
            docmeta["pacer_doc_id"] = docid
        elif docmatchv4:
            args = re.split(r'&', docmatchv4.group(1))

            docmeta = {}
            docmeta["doc_num"] = link.contents[0]
            docmeta["attachment_num"] = 0    # Primary document

            for s in args:
                (k,v) = re.split(r'=',s)
                k = k.encode('utf-8')
                if(k == 'de_seq_num'):
                    docmeta['pacer_de_seq_num'] = v
                if(k == 'dm_id'):
                    docmeta['pacer_dm_id'] = v
                if(k == 'doc_num'):
                    docmeta['doc_num'] = v

    else:
        # No link, just see if there is a docnum.

        docnumseq = row['number'].findAll(text=re.compile(".*"))
        docnumstr = "".join(docnumseq).strip("&nbsp;").strip()

        try:
            docnum = int(docnumstr)
        except ValueError:
            # No docnum... skip this row.
            return {}
        else:
            docmeta["doc_num"] = unicode(docnum)
            docmeta["attachment_num"] = 0

    date_re = re.compile(r"(\d\d)\/(\d\d)\/(\d\d\d\d)")
    try:
        date_match = date_re.search(row['date'].string)
    except (KeyError, TypeError):
        # No 'date' found.
        pass
    else:
        try:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year =  int(date_match.group(3))

            date_filed = datetime.date(year,month,day).isoformat()
            docmeta["date_filed"] = date_filed
        except (AttributeError,ValueError):
            # No date_match or bad values for month/day/year
            pass

    try:
        docket_text = row['text']
        long_desc_seq = \
            docket_text.findAll(text=re.compile(".*"))
        if long_desc_seq:
            docmeta["long_desc"] = \
                "".join(long_desc_seq).strip()

    except (KeyError, AttributeError):
        # No 'text' found.
        pass

    # If we parsed an index first and already added an entry for this
    # document there, we don't want to supercede that entry with
    # one that will be incorrect.

    # TK? add checks for bankruptcy-style doc
    # listing and inserts/updates with docnum, subdocnum
    # (and eventually date filed and docket text)

    return docmeta

def error_to_file(filebits, filename):

    # Open error file for writing
    fullname = "%s/_%s" % (BASE_ERROR_JAR, filename)
    try:
        f = open(fullname, "w")
    except IOError:
        logging.error("error_to_file: could not open file %s" % fullname)
        return

    try:
        f.write(filebits)
    except IOError:
        logging.error("error_to_file: could not write to file %s" % fullname)
        return

    f.close()

if __name__ == "__main__":

    def doc1():
        doc1name = "doc1bug.html"
        filebits = open(doc1name).read()
        docket = parse_doc1(filebits, "cand", 175966, 2)
        print docket.documents

    def histdoc():
        filename = "/var/django/recap_dev/recap-server/uploads/gitmo.html"
        docketbits = open(filename).read()
        docket = parse_histdocqry(docketbits, "scb", 30031)

        print docket.casemeta
        print docket.documents


    def dktrpt():
        filename = "./dockets/soghoian_docket.html"
        docketbits = open(filename).read()
        docket = parse_dktrpt(docketbits, "dcd", 12345)
        print docket.casemeta
        print docket.documents

    dktrpt()

    #histdoc()
    #doc1()

