
import logging 

from MySQLdb import IntegrityError

from uploads.models import BucketLock

import DocketXML

def get_lock(court, casenum, uploaderid, one_per_uploader=0):
    
    nonce = DocketXML.generate_new_nonce()

    lock = BucketLock(court=court, casenum=casenum, 
                      uploaderid=uploaderid, nonce=nonce)        
    try:
        lock.save()
    except IntegrityError:
        # Fail, lock already exists.

        lockquery = BucketLock.objects.filter(court=court) \
                                      .filter(casenum=casenum)
        try:
            lock = lockquery[0]
        except IndexError:
            # No lock exists anymore-- must have just missed it.
            return None, "Locked."
        else:
            # Lock already exists

	    # This prevents two cron jobs from requesting the same lock
	    if lock.uploaderid == uploaderid and one_per_uploader:
	        return None, "You already own this lock (Another cron job?)"
            if lock.uploaderid == uploaderid and not lock.ready:
                return lock.nonce, ""
            if lock.uploaderid == uploaderid and lock.ready and not lock.processing:
                # If we're not currently processing the case, let the same 
                # uploader modify it
                lock.ready = 0
                lock.save()
                return lock.nonce, ""
            else:
                return None, "Locked by another user."
    else:
        # Success.
        return nonce, ""

def drop_lock(court, casenum, uploaderid, modified=1, 
              nolocaldb=0, ignore_nonce=0):

    lockquery = BucketLock.objects.filter(court=court) \
                                  .filter(casenum=casenum)
    
    # Try to drop the lock
    try:
        lock = lockquery[0]
    except IndexError:
        # Already dropped.
        return True, ""
    else:
        if lock.uploaderid != uploaderid or lock.ready:
            # Not this user's lock
            return False, "Locked by another user."
        elif not modified:
            # No modifications, just drop the lock.
            lock.delete()
            return True, ""
        elif nolocaldb:
            # Don't update the local DB, just drop the lock.
            lock.delete()
            return True, ""
        else:
            # Modified and ready to fetch updates.
            lock.ready = 1
            if ignore_nonce:
                lock.nonce = ""
            lock.save()
            return True, ""

def lock_exists(court, casenum):
    lockquery = BucketLock.objects.filter(court=court) \
		    	  	  .filter(casenum=casenum)
    try:
	lock = lockquery[0]
    except IndexError:
	# Lock does not exist
	return False
    else:
	return True

def query_locks(uploaderid):

    # Find all the locks for the user

    lockquery = BucketLock.objects.filter(uploaderid=uploaderid)\
                                  .filter(ready=0)

    triples = []
    for lock in lockquery:
        triples.append((lock.court, lock.casenum, lock.nonce))

    return triples

def mark_ready_for_processing(timeout_cutoff):

    # Get all ready locks that aren't expired.
    lockquery = BucketLock.objects.filter(ready=1, processing=0,
                                          locktime__gte=timeout_cutoff)

    locklist = []
    # Set all ready locks to processing state
    for lock in lockquery:
        lock.processing = 1
        try:
            lock.save()
        except IntegrityError:
            logging.error("mark_ready_for_processing: could not save %s %s" %
                          (lock.court, unicode(lock.casenum)))
        else:
            locklist.append(lock)

    return locklist

def mark_expired_for_processing(timeout_cutoff):

    # Get all expired entries regardless of readiness.
    expiredquery = BucketLock.objects.filter(processing=0,
                                             locktime__lt=timeout_cutoff)

    locklist = []
    # Set all expired entries to the processing state
    for expiredlock in expiredquery:
        expiredlock.ready = 1
        expiredlock.processing = 1
        expiredlock.nonce = ""
        try:
            expiredlock.save()
        except IntegrityError:
            logging.error("mark_expired_for_processing: could not save %s %s" %
                          (expiredlock.court, unicode(expiredlock.casenum)))
        else:
            locklist.append(expiredlock)

    return locklist


def try_lock_later(lock):

    lock.processing = 0
    
    try:
        lock.save()
    except IntegrityError:
        logging.warning("try_lock_later: could not save %s %s" %
                        (lock.court, unicode(lock.casenum)))
    
    
