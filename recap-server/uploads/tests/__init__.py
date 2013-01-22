# Run tests by doing 'python manage.py test' in the recapsite directory
# Note that some tests in TestParsePacer take a long time, you may want to comment it
# out from this file while actively developing. Alternatively, refactor those tests
# so they don't take so long.

# TODO: Break up alltests into separate modules
#from alltests import TestParsePacer, TestViews, TestUploadView, TestQueryCasesView, \
#                     TestThirdPartyViews, TestQueryView, TestAddDocMetaView, TestParseOpinions

#from alltests import TestThirdPartyViews

from test_pacer_client import TestPacerClient
from test_opinions_downloader import TestOpinionsDownloader
from test_ia_uploader import TestIAUploader
from test_docket_xml import TestDocketXml
from test_document_manager import TestDocumentManager
