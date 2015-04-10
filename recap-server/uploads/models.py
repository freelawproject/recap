
from django.db import models


class Document(models.Model):
    """Note that a number of fields have indexes in the database despite
    lacking them here:

    mysql> show index from uploads_document;
        +------------------+-----------------+-------------+-------------+
        | Table            | Key_name        | Column_name | Cardinality |
        +------------------+-----------------+-------------+-------------+
        | uploads_document | PRIMARY         | id          |    26652929 |
        | uploads_document | court           | court       |         206 |
        | uploads_document | court           | casenum     |     1025112 |
        | uploads_document | court           | docnum      |    26652929 |
        | uploads_document | court           | subdocnum   |    26652929 |
        | uploads_document | docid_idx       | docid       |    26652929 |
        | uploads_document | document_free_i | free_import |           2 |
        | uploads_document | lastdateindex   | lastdate    |    26652929 |
        | uploads_document | modifiedindex   | modified    |     6663232 |
        +------------------+-----------------+-------------+-------------+

    (https://dev.mysql.com/doc/refman/5.0/en/show-index.html)

    """
    court = models.CharField(
        max_length=10,
    )
    casenum = models.CharField(
        max_length=30,
    )
    docnum = models.CharField(
        max_length=30,
    )
    subdocnum = models.CharField(
        max_length=30,
    )
    docid = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    de_seq_num = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    dm_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    sha1 = models.CharField(
        max_length=40,
        null=True,
        blank=True,
    )
    available = models.BooleanField(
        default=0,
    )
    lastdate = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )
    modified = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True,
        db_index=True,
    )
    free_import = models.BooleanField(
        default=0,
        db_index=True,
    )
    team_name = models.CharField(
        maxlength=40,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = (
            (
                "court",
                "casenum",
                "docnum",
                "subdocnum",
            ),
        )


class PickledPut(models.Model):
    filename = models.CharField(
        max_length=128,
        primary_key=True,
    )
    docket = models.BooleanField(
        default=0,
    )
    ready = models.BooleanField(
        default=0,
    )
    processing = models.BooleanField(
        default=0,
    )


class BucketLock(models.Model):
    court = models.CharField(
        max_length=10,
    )
    casenum = models.CharField(
        max_length=30,
    )
    uploaderid = models.IntegerField()
    nonce = models.CharField(
        max_length=6,
    )
    ready = models.BooleanField(
        default=0,
    )
    processing = models.BooleanField(
        default=0,
    )
    locktime = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        unique_together = (
            (
                "court",
                "casenum",
            ),
        )

    def __unicode__(self):
        return str(self.court) + "." + str(self.casenum)


class Uploader(models.Model):
    # implicit 'id' IntegerField being used.
    key = models.CharField(
        max_length=8,
    )
    name = models.CharField(
        max_length=64,
    )
