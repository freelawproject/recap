
from django.db import models


class Document(models.Model):
    court = models.CharField(maxlength=10)
    casenum = models.CharField(maxlength=30)
    docnum = models.CharField(maxlength=30)
    subdocnum = models.CharField(maxlength=30)
    docid = models.CharField(maxlength=32, null=True, blank=True, db_index=True)
    de_seq_num = models.PositiveIntegerField(null=True, blank=True)
    dm_id = models.PositiveIntegerField(null=True, blank=True)
    sha1 = models.CharField(maxlength=40, null=True, blank=True)
    available = models.BooleanField(default=0)
    lastdate = models.DateTimeField(null=True, blank=True, db_index=True)
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, db_index=True)
    free_import = models.BooleanField(default=0, db_index=True)

    class Meta:
        unique_together = (("court", "casenum", "docnum", "subdocnum"),)


class PickledPut(models.Model):
    filename = models.CharField(maxlength=128, primary_key=True)
    docket = models.BooleanField(default=0)
    ready = models.BooleanField(default=0)
    processing = models.BooleanField(default=0)


class BucketLock(models.Model):
    court = models.CharField(maxlength=10)
    casenum = models.CharField(maxlength=30)
    uploaderid = models.IntegerField()
    nonce = models.CharField(maxlength=6)
    ready = models.BooleanField(default=0)
    processing = models.BooleanField(default=0)
    locktime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("court", "casenum"),)

    def __str__(self):
        return str(self.court) + "." + str(self.casenum)


class Uploader(models.Model):
    # implicit 'id' IntegerField being used.
    key = models.CharField(maxlength=8)
    name = models.CharField(maxlength=64)
