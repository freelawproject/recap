from __future__ import with_statement
#################### DJANGO CONFIG ####################
import sys, os
sys.path.extend(('..', '.'))

#######################################################
import pika
import tempfile
import logging
import cPickle as pickle
from datetime import date
from datetime import datetime

from django.conf import settings as config
from pacer_client import PacerClient, PacerPageNotAvailableException
import ParsePacer as PP

logger = logging.getLogger('opinions_downloader')    

class OpinionsDownloader():
    # TK: Add a param to set where to download files to?
    def __init__(self, username, password) :
        self.pacer_client = PacerClient(username, password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                   'localhost'))
        self.channel = self.connection.channel()

        # set up the queue for later
        self.channel.queue_declare(queue='dockets')

    def reinit_pacer_client(self, username, password): 
        # we have to log into each new court separately
        self.pacer_client = PacerClient(username, password)


    def get_opinions(self, court, start_date, end_date):
        html = self.pacer_client.get_opinions_html(court,
                                                   start_date,
                                                   end_date)

        dockets = PP.parse_opinions(html, court)
        logger.info(' Downloaded %d dockets for court %s between %s and %s', len(dockets), 
                                                                       court,
                                                                       start_date,
                                                                       end_date)
        #if len(dockets) == 0:
        #    logger.debug(' 0 dockets downloaded. HTML response: %s', html)
        return dockets
    
    def get_document(self, court, casenum, de_seq_num, dm_id, doc_num):
        return self.pacer_client.get_pdf_show_doc(court, casenum, de_seq_num, dm_id, doc_num)

    def enqueue_opinions(self, court, start_date, end_date):
        for docket in self.get_opinions(court, start_date, end_date):
            docmap = {}
            for key, doc in docket.documents.items():
                logger.info('    Downloading document %s.%s.%s.0', court, 
                                                              docket.get_casenum(), 
                                                              doc['doc_num']), 
                pdfbits = self.get_document(court, 
                                            docket.get_casenum(), 
                                            doc['pacer_de_seq_num'], 
                                            doc['pacer_dm_id'], 
                                            doc['doc_num'])
                logger.info('    Downloaded document %s.%s.%s.0', court, 
                                                              docket.get_casenum(), 
                                                              doc['doc_num']), 
                # pickle the document into a file
                # map the docnum-subdocnum to the filename
                docmap[key] = _pickle_object(pdfbits)
               
            # pickle file
            filename = _pickle_object(docket)
            # create message
            upload_message = {'docket_filename': filename,
                              'docnums_to_filename': docmap,
                              'court': docket.get_court(),
                              'casenum': docket.get_casenum()}
            # energize!
            self.channel.basic_publish(exchange='',
                                  routing_key='dockets',
                                  body=pickle.dumps(upload_message))
            logger.info('  Sent upload message for %s.%s', court, docket.get_casenum()) 

def _pickle_object(obj):
    # we can easily switch to using S3 here if we want
    # mkstemp doesn't delete the file, so we are responsible for it
    fd, filename = tempfile.mkstemp()
    f = os.fdopen(fd, 'w')
    pickle.dump(obj, f)
    f.close()
    # Alternately, if we upgraded to python2.6, we could use:
    #with tempfile.NamedTemporaryFile(delete=False) as f:

    return filename

def run_downloader(courts=['nysd'], start_date=date(2011, 06, 17), end_date=date(2011, 06, 17)):
    # TK: do something smart here to make sure days aren't missed?
    logger.info('Starting opinion download for courts %s, date: %s to %s', courts, 
                                                                           start_date,
                                                                           end_date)
    downloader = OpinionsDownloader(config.PACER_USERNAME,
                                    config.PACER_PASSWORD)

    failed_courts = []

    for court in courts:
        downloader.reinit_pacer_client(config.PACER_USERNAME, 
                                       config.PACER_PASSWORD)
        logger.info('Starting opinion download for court %s, date: %s to %s', court, 
                                                                           start_date,
                                                                           end_date)
        try:
            downloader.enqueue_opinions(court, start_date, end_date)
        except PacerPageNotAvailableException, e:
            logger.info('Court %s does not seem to have a written opinions report. Message: %s ', court, str(e))
        except Exception, e:
            # Doing a broad exception so that failures on one court don't affect others
            logger.exception('Court %s failed to download for dates %s to %s. Message: %s',
                                court, start_date, end_date, str(e))
        else:
            logger.info('Successfully finished download for court %s', court)


if __name__ == "__main__":
    logging.info('Starting opinion script')
    if len(sys.argv) < 4:
        logging.error('Incorrect usage(%s) exiting' % sys.argv)
        sys.exit('Usage: python %s court[,court2,court3...] start_date end_date\n'   
                 '        date format should be YYYY-MM-DD' % sys.argv[0])

    courts= sys.argv[1].split(',')
    courts = [c for c in courts if c != ''] # filter out trailing comma
    start_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    end_date = datetime.strptime(sys.argv[3], '%Y-%m-%d')
    run_downloader(courts, start_date, end_date)

