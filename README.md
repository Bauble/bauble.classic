Bauble
======

what is Bauble (classic)
------------------------

At its heart Bauble is a framework for creating database
applications.  In its distributed form Bauble is an application to
manage plant records and specifically living collections.  It is
used among others by Belize Botanic Gardens to manage their live
collections.  Included by default is RBG Kew's Family and Genera
list from Vascular Plant Families and Genera compiled by
R. K. Brummitt and published by the Royal Botanic Gardens, Kew in
1992 used by permission from RBG Kew.

All code contained as part of the Bauble package is licenced under
the GNU GPLv2+.

Terms and Names
---------------

This file describes 'bauble.classic', a standalone
application. 'bauble.classic' was formerly known just as as
'Bauble'. currently 'Bauble' is the name of an organization on github,
enclosing 'bauble.classic', 'bauble.webapp' and 'bauble.api'.

the two new projects 'bauble.webapp' and 'bauble.api' are what you would
fork/download if you want to participate to the development of a web-based
version of 'Bauble'.

'bauble.classic' is what you would install if you want to start using
'Bauble' straight away.

The database structure of both 'bauble.classic' and the pair
'bauble.webapp/bauble.api' is similar so any data you would insert using
'bauble.classic' will be available once you install a running version of
'bauble.webapp/bauble.api'.

Requirements
------------
bauble.classic requires the following packages to run.

* a debug version of Python (>= 2.4, recently tested with 2.7.5)
* SQLAlchemy (>= 0.6.0, recently tested with 0.9.1)
* pygtk (>= 2.12)
* PyGObject (>= 2.11.1)
* lxml (>= 2.0)

each of the following database connectors is optional, but at least one is needed:

* pysqlite >= 2.3.2
* psycopg2 >= 2.0.5 
* mysql-python >= 1.2.1 

To use the formatter plugin you will also need to install an
XSL->PDF renderer. For a free renderer check out Apache FOP
(>=.92beta) at http://xmlgraphics.apache.org/fop/

Further info
------------

The complete documentation for bauble.classic is to be found at
http://bauble.readthedocs.org. It includes detailed and up-to-date
installation procedures for different platforms, troubleshooting,
and a very thorough user manual.

The site for bauble.webapp is http://bauble.io.
