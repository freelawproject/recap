# Upgrade notes

These notes should be reviewed whenever you get fresh code. Any manual tweaks
or configurations that are needed will be documented here.


# 2015-04-08

Adds the team_name feature to the backend, which requires a new field be added
to the database.

Thus:

1. Before pulling, shut down your server to avoid errors.
1. Pull
1. Add the field to the database with:

        ALTER TABLE "uploads_document" ADD "team_name" varchar(40) NULL;
    
1. Restart your server


# 2015-04-04

In order to fix #59, the BUCKET_PREFIX variable was renamed DEV_BUCKET_PREFIX.

If you have this variable defined a configuration that is not included in the
repository (e.g. a private.py file), you will need to update the name of this
variable in that file.


# 2015-03-28
## Upgrading to the new settings system

Recently, this app has adopted a new settings system for configuring everything
from database urls to Internet Archive keys. Formerly, these settings where in
`uploads/recap_config.py` and `settings.py` and were accessed by code using
different systems.

This guide will help with the steps required to upgrade from the old system to
the new. The basic steps are:

0. Shut down running server, but *do not* `git pull` yet.
0. Create `settings/05-private.py` and `settings/20-private.py`
0. Copy any modified settings from settings.py to `settings/20-private.py`.
0. Copy any settings from `recap_config.py` to `settings/05-private.py`.

### Shut down running server, but *do not* `git pull` yet.

This should be self explanatory. If you try to git pull and you have modified
settings in `settings.py`, you will likely get some kind of merge conflict. If
you try to `git stash` and then `git pull`, your stash will not apply cleanly to
the new version.

### Create `settings/05-private.py` and `settings/20-private.py`

These files can start out empty. The file `05-private.py` contains settings that
aren't specified in `10-public.py` and could be overridden, or at the least
utilized, by that file. The other file, `20-private.py` contains overrides to
the public settings.

### Copy any modified settings from settings.py to `settings/20-private.py`.

You should be able to do a `git diff` and see what lines have changed. Any such
line should be copied into `20-private.py`. The standard set of settings from
the previous incarnation of `settings.py` have been copied into
`settings/10-public.py` and it is necessary to copy your overrides into
`20-private.py` in order to get them picked up. The format of `20-private.py` is
a standard python file, with variable declarations in
`THIS_VARIABLE = 'format'`, which matches the format of the old `settings.py`.

### Copy any settings from `recap_config.py` to `settings/05-private.py`.

The file `recap_config.py` formerly contained additional private details of the
server like `DATABASE_USER` and `DATABASE_PASSWORD`. The format of this file was
a python source file which contained a single dictionary declared as `config`:
```
config = {"DATABASE_NAME": "recap_dev",
          "BUCKET_PREFIX": "dev",
          "SERVER_HOSTNAME": "http://dev.recapextension.org/",
          "SERVER_BASEDIR": "recap/",
          ...
}
```

The settings system has been designed so that all entries in this file can be
instead stored in `settings/05-private.py`. You will see an example of this file
in the settings directory, which also serves to document all of the variable
parameters that certain aspects of the system require to operate.

To convert your `recap_config.py` to a `05-private.py`, simply convert every key
of the `config` dict into a variable, and set it equal to the value it had
in the `config` dict. For the example above:
```
DATABASE_NAME = "recap_dev"
BUCKET_PREFIX = "dev"
SERVER_HOSTNAME = "http://dev.recapextension.org/"
SERVER_BASEDIR = "recap/"
```

*Important note:* be sure that there are no quotes around the key names, they
are just bare variables in the new setup. Also make sure that there are no
commas trailing the values, which might happen if you copied and pasted. This
would cause the values to turn into tuples, which we do not want.

### Cleaning up

Now that you've copied the new files into place, you should copy your old
`settings.py` to `settings.py.bak` and then `git checkout settings.py`. Now you
can `git pull` to get the latest version. Ensure that everything is operating
properly, and at some point in the future you can delete `recap_config.py` and
`settings.py.bak`.
