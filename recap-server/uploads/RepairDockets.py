import sys
import DocumentManager 
import UploadHandler

def read_in_cases_to_repair(filename):
    f = open(filename, 'r')
    case_list = []

    for line in f:
       court, casenum = line.split(" ")
       case_list.append((court.strip(), casenum.strip()))

    return case_list

if __name__ == '__main__':
  ''' Be sure to set the appropriate environment variables for django!
      export PYTHONPATH=/var/django/recap_prod:/var/django/recap_prod/recapsite
      export DJANGO_SETTINGS_MODULE=recapsite.settings
  '''

  if len(sys.argv) != 2:
    sys.stderr.write("Usage: %s <filename_containing_cases_to_repair>\n " % sys.argv[0])
    sys.stderr.write("      The contents of filename should have a single case per line, each identified by 'court casenum'\n " )
    sys.exit(1) 

  cases_to_repair = read_in_cases_to_repair(sys.argv[1])

  for case in cases_to_repair:
    court = case[0]
    casenum = case[1]

    print "Repairing case %s.%s...." % (court, casenum)

    docket = DocumentManager.create_docket_from_local_documents(court, casenum)

    if docket:
	# this will merge our docket with existing one on IA
        UploadHandler.do_me_up(docket) 
    else:
        print " Could not create docket from local documents for %s %s" % (court, casenum)



#  for each case, create docket fromlocal

#  call do_me_up(docket)
#  download ia_docket
#
#  merge ia docket and local docket
#
#  if there is a difference, schedule the docket for upload (created a pickled put?)
