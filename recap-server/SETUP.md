#Setup Instructions (accepting documents from clients): 
Note that these instructions are for setting up a development environment. If you run into issues and find that more steps are needed, pull requests are welcome!

- Install Python2.5 - you can install python from source, or use this PPA if you're on ubuntu (https://launchpad.net/~fkrull/+archive/deadsnakes)
   (Steve note, "you'll need python-dev too": apt-get install python-dev)
- Install mysql
	- steve did: apt-get install mysql-server
	- steve did apt-get install libmysqlclient-dev
- install git
- Install python dependencies (you may wish to setup a virtualenv for this, tied to python2.5)
   * Django 0.96.5 - http://www.djangoproject.com/download/0.96.5/tarball/ 
   * mysql-python
   * lxml
	- steve did: apt-get install libxml2-dev libxslt-dev
	- steve did: apt-get install python-lxml
- Setup mysql and create a new database for RECAP to use 
- Edit the parameters in settings.py to match your own setup. At a minimum, you'll probably want to edit the DATABASE_* variables for django to be able to access your local db
- add a file uploads/config.py that contains something like:
config = {"DATABASE_NAME": "recap_dev",
          "BUCKET_PREFIX": "",
          "SERVER_HOSTNAME": "http://localhost:8000",
          "SERVER_BASEDIR": "recap/",
          "UPLOAD_AUTHKEY": "",
          "IA_STORAGE_URL": "http://s3.us.archive.org",
          "DJANGO_DEBUG": False,
          "DJANGO_ADMIN": ("Recap Bugs", "youremail@example.com"),
          "DUMP_DOCKETS": False,
          "DUMP_DOCKETS_COURT_REGEX": "b-|b$",
          "MAX_NUM_DUMP_DOCKETS": "100"
}
- Setup the tables the server needs by running `python manage.py syncdb`
- At this point, if you are able to start the server: `python manage.py runserver` and see the message "Well hello, there's nothing to see here" when visiting http://localhost:8000/recap/", then RECAP is working and will accept documents.


#Setup Instructions(uploading documents to the internet archive):

- Running python syncdb should have created a default Uploader row in the db. You'll need to get the 'key' from either the db or initial_data.json and set `UPLOAD_AUTHKEY` to that value.
