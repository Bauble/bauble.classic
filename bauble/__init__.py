#
# bauble module
#

import imp, os, sys

# major, minor, revision 
# should be updated for each release of bauble

# this is from the python docs, we should probably have something similar
# for bauble so we can do release candidate and beta releases
# version_info 
# A tuple containing the five components of the version number: 
# major, minor, micro, releaselevel, and serial. All values except 
# releaselevel are integers; the release level is 'alpha', 'beta', 
# 'candidate', or 'final'. The version_info value corresponding to the Python 
# version 2.0 is (2, 0, 0, 'final', 0). New in version 2.0. 
version = (0,5,3)
version_str = '%s.%s.%s' % (version[0], version[1], version[2])

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") or # old py2exe
           imp.is_frozen("__main__")) # tools/freeze

import pygtk
if not main_is_frozen():
   pygtk.require("2.0")     
else: # main is frozen
   # put library.zip first in the path when using py2exe so libxml2 gets 
   # imported correctly, 
   zipfile = sys.path[-1]
   sys.path.insert(0,zipfile)

import gtk
import bauble.utils as utils
import bauble.paths as paths
sys.path.append(paths.lib_dir())

# create the user directory
if not os.path.exists(paths.user_dir()):
    os.makedirs(paths.user_dir())

# meta information about the bauble database
from sqlobject import SQLObject, StringCol
    
class BaubleMetaTable(SQLObject):
    
    class sqlmeta:        
        table = "bauble"
    
    name = StringCol(length=64)
    value = StringCol(length=128)
    
    # some keys for the standard information
    version = 'version' # a string tuple of (major, minor, revision)
    created = 'created' # a string in datetime.now() format

    #date_format = 'date'
    


class BaubleError(Exception):
     def __init__(self, msg):
         self.msg = msg
     def __str__(self):
         return self.msg    
        
try:
    from sqlobject import *
except ImportError:
    msg = "SQLObject not installed. Please install SQLObject from "\
          "http://www.sqlobject.org"
    utils.message_dialog(msg, gtk.MESSAGE_ERROR)    
    raise

from bauble._app import BaubleApp
app = BaubleApp()


