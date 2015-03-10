#
# i18n.py
#
# internationalization support
#

"""
The i18n module defines the _() function for creating translatable strings.

_() is added to the Python builtins so there is no reason to import
this module more than once in an application.  It is usually imported
in :mod:`bauble`
"""

import sys
import os
import locale
import gettext
import bauble.paths as paths
from bauble import version_tuple

__all__ = ["_"]

TEXT_DOMAIN = 'bauble-%s' % '.'.join(version_tuple[0:2])

#
# most of the following code was adapted from:
# http://www.learningpython.com/2006/12/03/\
# translating-your-pythonpygtk-application/

langs = []
#Check the default locale
lang_code, encoding = locale.getdefaultlocale()
if lang_code:
    # If we have a default, it's the first in the list
    langs = [lang_code]
# Now lets get all of the supported languages on the system
language = os.environ.get('LANGUAGE', None)
if language:
    # langage comes back something like en_CA:en_US:en_GB:en on linuxy
    # systems, on Win32 it's nothing, so we need to split it up into a
    # list
    langs += language.split(":")
# add on to the back of the list the translations that we know that we
# have, our defaults"""
langs += ["en"]

# langs is a list of all of the languages that we are going to try to
# use.  First we check the default, then what the system told us, and
# finally the 'known' list

gettext.bindtextdomain(TEXT_DOMAIN, paths.locale_dir())
gettext.textdomain(TEXT_DOMAIN)
# Get the language to use
lang = gettext.translation(TEXT_DOMAIN, paths.locale_dir(), languages=langs,
                           fallback=True)
# install the language, map _() (which we marked our strings to
# translate with) to self.lang.gettext() which will translate them.
_ = lang.gettext

# register the gettext function for the whole interpreter as "_"
import __builtin__
__builtin__._ = gettext.gettext

import bauble
