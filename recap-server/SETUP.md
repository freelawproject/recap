#Setup Instructions (accepting documents from clients): 
Note that these instructions are for setting up a development environment. If you run into issues and find that more steps are needed, pull requests are welcome!

- Install Python2.5 - you can install python from source, or use this PPA if you're on ubuntu (https://launchpad.net/~fkrull/+archive/deadsnakes)
- Install python dependencies (you may wish to setup a virtualenv for this, tied to python2.5)
   * Django 0.96.5 - http://www.djangoproject.com/download/0.96.5/tarball/ 
   * mysql-python
   * lxml
- Setup mysql and create a new database for RECAP to use 
- Edit the parameters in settings.py to match your own setup. At a minimum, you'll probably want to edit the DATABASE_* variables for django to be able to access your local db
- Setup the tables the server needs by running `python manage.py syncdb`
- At this point, if you are able to start the server: `python manage.py runserver` and see the message "Well hello, there's nothing to see here" when visiting http://localhost:8000/recap/", then RECAP is working and will accept documents.


#Setup Instructions(uploading documents to the internet archive):
These will come soon - developers will need credentials to upload to the archive.
