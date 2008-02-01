#
# Description: Download all other Bauble dependencies that aren't GTK/pygtk
# related
#
# Author: brett@belizebotanic.org
#
# License: GPL
#

# TODO:
# - let the user choose a mirror
# - *-dev versions of files?
# - check MD5
# - do an import MYSQL-python and check the version to see if we need to
# install the .exe files

import sys

if sys.platform != 'win32':
    print "Error: This script is only for Win32"
    sys.exit(1)

import os
import urllib
import zipfile
import _winreg
from optparse import OptionParser
parser = OptionParser()
parser.add_option('-r', '--redl', action='store_true', dest='redl',
                  default=False, help="redownload existing files")
#parser.add_option('-g', '--gtk-only', action='store_true', dest='gtk_only',
#                 default=False, help='only download the GTK+ files, not PyGTK')
#parser.add_option('-i', '--install_path', dest="install_path", metavar="DIR",
#                  help="directory to install GTK+, default is c:\GTK")
parser.add_option('-d', '--download_path', dest="download_path", metavar="DIR",
                  help="directory to download files, default is .\install_deps")
(options, args) = parser.parse_args()


ALL_FILES = []

PYTHON_24_FILES = [
    'http://initd.org/pub/software/pysqlite/releases/2.4/2.4.0/pysqlite-2.4.0.win32-py2.4.exe',
    'http://www.stickpeople.com/projects/python/win-psycopg/psycopg2-2.0.6.win32-py2.4-pg8.2.4-release.exe']

PYTHON_25_FILES = [
    'http://initd.org/pub/software/pysqlite/releases/2.4/2.4.0/pysqlite-2.4.0.win32-py2.5.exe',
    'http://www.stickpeople.com/projects/python/win-psycopg/psycopg2-2.0.6.win32-py2.5-pg8.2.4-release.exe']

EZ_SETUP_PATH = 'http://peak.telecommunity.com/dist/ez_setup.py'


# TODO: what about fop? its too big, maybe we should ask the user
#
# TODO: check for easy_install, if not installed then download and install
# ez_setup.py

eggs_install = {'lxml': '==1.3.6',
                'MySQL-python': '==1.2.2',
                'simplejson': '==1.7.1', # 1.73 is the latest but doesn't have a compile win32 version on PPI
                'SQLAlchemy': '>=0.4.2p3',
                'py2exe': '==0.6.6'}



def get_subkey_names(reg_key):
    index = 0
    L = []
    while True:
        try:
            name = _winreg.EnumKey(reg_key, index)
        except EnvironmentError:
            break
        index += 1
        L.append(name)
    return L


def get_python_versions():
    """
    Return a list with info about installed versions of Python.

    Each version in the list is represented as a tuple with 3 items:

    0   A long integer giving when the key for this version was last
          modified as 100's of nanoseconds since Jan 1, 1600.
    1   A string with major and minor version number e.g '2.4'.
    2   A string of the absolute path to the installation directory.
    """
    python_path = r'software\python\pythoncore'
    versions = {}
    for reg_hive in (_winreg.HKEY_LOCAL_MACHINE,
                      _winreg.HKEY_CURRENT_USER):
        try:
            python_key = _winreg.OpenKey(reg_hive, python_path)
        except EnvironmentError:
            continue
        for version_name in get_subkey_names(python_key):
            key = _winreg.OpenKey(python_key, version_name)
            modification_date = _winreg.QueryInfoKey(key)[2]
            try:
                install_path = _winreg.QueryValue(key, 'installpath')
                versions[version_name] = install_path
            except:
                pass
    return versions

PYTHON_HOME = None
PYTHON_EXE = None

# detect python version and download pygtk installers

python_versions = get_python_versions()
available_versions = {}
for version, path in python_versions.iteritems():
    if os.path.exists(path) and os.path.exists(os.path.join(path,'python.exe')):
        print 'Python %s seems to be installed correctly' % version
        available_versions[version] = path
    else:
        print 'Python %s NOT installed correctly' % version

if len(available_versions.keys()) == 0:
    print "Error: Install Python first"

if len(available_versions.keys()) > 1:
    # TODO: make a decision if more than one version
    print 'More than one Python version installed'
    sys.exit(1)

chosen_version, chosen_path = available_versions.popitem()

print 'Using Python %s' % chosen_version
PYTHON_HOME = chosen_path
PYTHON_EXE = os.path.join(PYTHON_HOME, 'python.exe')
if chosen_version == '2.4':
    ALL_FILES.extend(PYTHON_24_FILES)
elif chosen_version == '2.5':
    ALL_FILES.extend(PYTHON_25_FILES)
else:
    print 'Error: Python %s is not supported' % choosen_version

if options.download_path:
    DL_PATH = options.download_path
else:
    DL_PATH = os.path.join(os.getcwd(), 'install_deps')

print 'using download path: %s' % DL_PATH
if not os.path.exists(DL_PATH):
    os.makedirs(DL_PATH)

# download all the files
#for url in ['%s/%s' % (SERVER_ROOT, FILE) for FILE in ALL_FILES]:
for url in ALL_FILES:
    filename = url.split('/')[-1]
    dest_file = os.path.join(DL_PATH, filename)
    if os.path.exists(dest_file) and not options.redl:
        continue
    print 'downloading %s...' % filename
    urllib.urlretrieve(url, os.path.join(DL_PATH, filename))


# for all the files that we downloaded (or would have downloaded) then
# either unzip or execute them
for filename in [f.split('/')[-1] for f in ALL_FILES]:
    fullname = '"%s"' % os.path.join(DL_PATH, filename)
    os.system(fullname)


# make sure that setuptools is installed
EASY_INSTALL_EXE = os.path.join(PYTHON_HOME, 'scripts','easy_install.exe')
if not os.path.exists(EASY_INSTALL_EXE):
    EZ_SETUP_DL_PATH = os.path.join(DL_PATH, 'ez_setup.py')
    if not os.path.exists(EZ_SETUP_DL_PATH):
        urllib.urlretrieve(EZ_SETUP_PATH, EZ_SETUP_DL_PATH)
    cmd = '%s "%s"' % (PYTHON_EXE, EZ_SETUP_DL_PATH)
#    print cmd
    os.system(cmd)

# install the eggs
for egg, version in eggs_install.iteritems():
    cmd = '%s -Z "%s%s"' % (EASY_INSTALL_EXE, egg, version)
    #print cmd
    os.system(cmd)

print 'done.'