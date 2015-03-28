"""Settings are derived by compiling any files ending in .py in the settings directory, in alphabetical order.

This results in the following concept:
 - default settings are in 10-public.py (this should contain most settings)
 - custom settings are in 05-private.py (an example of this file is here for you)
 - any overrides to public settings can go in 20-private.py (you'll need to create this)
"""

import os
import glob
import sys

def _generate_secret_key(file_path):
  import random
  chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
  def random_char():
    return chars[int(len(chars)*random.random())]
  rand_str = ''.join(random_char() for i in range(64))
  with open(file_path, 'w') as f:
    f.write('SECRET_KEY=%s\n' % repr(rand_str))

ROOT_PATH = os.path.dirname(__file__)

# Try importing the SECRET_KEY from the file secret_key.py. If it doesn't exist,
# there is an import error, and the key is generated and written to the file.
try:
    from secret_key import SECRET_KEY
except ImportError:
    _generate_secret_key(os.path.join(ROOT_PATH, 'secret_key.py'))
    from secret_key import *

# Load the conf files.
conf_files = glob.glob(os.path.join(
    os.path.dirname(__file__), 'settings', '*.py'))
conf_files.sort()
for f in conf_files:
    execfile(os.path.abspath(f))
