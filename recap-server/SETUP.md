#Setup Instructions (accepting documents from clients):
Note that these instructions are for setting up a development environment. If
you run into issues and find that more steps are needed, pull requests are
welcome!

- Install Python2.5 - you can install python from source, or use this PPA if
  you're on ubuntu (https://launchpad.net/~fkrull/+archive/deadsnakes)
  (Steve note, "you'll need python-dev too": `apt-get install python-dev`)
  (Modern note: If you have trouble digging up a copy of Python 2.5, version 2.7
  is expected to work, but no guarantees.)
- Install mysql
	- steve did: `apt-get install mysql-server`
	- steve did `apt-get install libmysqlclient-dev`
- install git
  - `apt-get install git`
- Install python dependencies (you may wish to setup a virtualenv for this, tied to python2.5)
  - Django 0.96.5 - http://www.djangoproject.com/download/0.96.5/tarball/
     - pip install git+https://github.com/django/django@c939b2a1cb22b5035b1ccf90ee7686f334e6049d#egg=django==0.96.5
  - mysql-python
  - lxml
	- steve did: `apt-get install libxml2-dev libxslt-dev`
	- steve did: `apt-get install python-lxml`
- Setup mysql and create a new database for RECAP to use
  - `$ mysql -u root`
  - `CREATE DATABASE recap_dev;`
  - `CREATE USER recap@localhost IDENTIFIED BY 'recapthelaw'`
  - `GRANT ALL ON recap_dev.* TO recap@localhost`
- Copy settings/05-private.py.sample to settings/05-private.py
  - Configuration variables are read from files in settings/*.py, in
    alphabetical order with latter files overriding earlier ones. That means
    that 05-private.py is read first and all of its values are subject to being
    overwritten by 10-public.py (but also are available to by read by that file).
  - Also note that importing the settings module causes the secret_key.py file
    to be populated and written. This is only done once. If you are migrating an
    existing server with an existing SECRET_KEY, it may be necessary to create
    this file by hand. It should look like:
```
  SECRET_KEY='8=p_a92gp9-p-bfgc^&q#99(-ayb9j_e&tj8q32@7f(oz4s7g-7y+y8=k=b5ns52'
```
- Setup the tables the server needs by running `python manage.py syncdb`
- At this point, if you are able to start the server: `python manage.py runserver` and see the message "Well hello, there's nothing to see here" when visiting http://localhost:8000/recap/", then RECAP is working and will accept documents.


# Setup Instructions (uploading documents to the internet archive):

- Running python syncdb should have created a default Uploader row in the db. You'll need to get the 'key' from either the db or initial_data.json and set `UPLOAD_AUTHKEY` to that value.
- Be sure to set the DEV_BUCKET_PREFIX to a good value to namespace your uploads.
- You will also need a temp directory in the directory of the application for
  storing Python pickles. The path should be './picklejar' and it should be
  writable to the user that the server runs as.
