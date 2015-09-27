# -*- coding: utf-8 -*-
#
# Copyright (c) 2005,2006,2007,2008,2009 Brett Adams <brett@belizebotanic.org>
# Copyright (c) 2012-2015 Mario Frasca <mario@anche.no>
#
# This file is part of bauble.classic.
#
# bauble.classic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bauble.classic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bauble.classic. If not, see <http://www.gnu.org/licenses/>.
#
# test_bauble.py
#
import datetime
import os
import time

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from sqlalchemy import (
    Column, Integer, Table)

import bauble
import bauble.db as db
from bauble.btypes import Enum
from bauble.test import BaubleTestCase, check_dupids
import bauble.meta as meta

"""
Tests for the main bauble module.
"""


class EnumTests(BaubleTestCase):

    def setUp(self):
        BaubleTestCase.setUp(self)
        self.enum_class = Table(
            'test_enum_type', db.metadata,
            Column('id', Integer, primary_key=True),
            Column('value', Enum(values=['1', '2', '']), default=u''),
            )
        self.enum_class.create(db.engine)

    def tearDown(self):
        BaubleTestCase.tearDown(self)

    def test_insert_low_level(self):
        table = self.enum_class.__table__
        db.engine.execute(table.insert(), {"id": 1})

    def test_insert_zalchemic(self):
        Test = self.enum_class
        t = Test(id=1)
        self.session.add(t)
        self.session.flush()


class BaubleTests(BaubleTestCase):

    def test_date_type(self):
        """
        Test bauble.types.Date
        """
        dt = bauble.btypes.Date()

        bauble.btypes.Date._dayfirst = False
        bauble.btypes.Date._yearfirst = False
        s = '12-30-2008'
        v = dt.process_bind_param(s, None)
        self.assert_(v.month == 12 and v.day == 30 and v.year == 2008,
                     '%s == %s' % (v, s))

        bauble.btypes.Date._dayfirst = True
        bauble.btypes.Date._yearfirst = False
        s = '30-12-2008'
        v = dt.process_bind_param(s, None)
        self.assert_(v.month == 12 and v.day == 30 and v.year == 2008,
                     '%s == %s' % (v, s))

        bauble.btypes.Date._dayfirst = False
        bauble.btypes.Date._yearfirst = True
        s = '2008-12-30'
        v = dt.process_bind_param(s, None)
        self.assert_(v.month == 12 and v.day == 30 and v.year == 2008,
                     '%s == %s' % (v, s))

        # TODO: python-dateutil 1.4.1 has a bug where dayfirst=True,
        # yearfirst=True always parses as dayfirst=False

        # bauble.types.Date._dayfirst = True
        # bauble.types.Date._yearfirst = True
        # debug('--')
        # s = '2008-30-12'
        # #s = '2008-12-30'
        # debug(s)
        # v = dt.process_bind_param(s, None)
        # debug(v)
        # self.assert_(v.month==12 and v.day==30 and v.year==2008,
        #              '%s == %s' % (v, s))

    def test_datetime_type(self):
        """
        Test bauble.types.DateTime
        """
        dt = bauble.btypes.DateTime()

        # TODO: *** this needs to be updated since now we don't do our
        # own date parsing and use the dateutils module instead

        # with negative timezone
        s = '2008-12-1 11:50:01.001-05:00'
        result = '2008-12-01 11:50:01.001000-05:00'
        v = dt.process_bind_param(s, None)
        self.assert_(str(v) == result, '%s == %s' % (v, result))

        # test with positive timezone
        s = '2008-12-1 11:50:01.001+05:00'
        result = '2008-12-01 11:50:01.001000+05:00'
        v = dt.process_bind_param(s, None)
        self.assert_(str(v) == result, '%s == %s' % (v, result))

        # test with no timezone
        s = '2008-12-1 11:50:01.001'
        result = '2008-12-01 11:50:01.001000'
        v = dt.process_bind_param(s, None)
        self.assert_(str(v) == result, '%s == %s' % (v, result))

        # test with no milliseconds
        s = '2008-12-1 11:50:01'
        result = '2008-12-01 11:50:01'
        v = dt.process_bind_param(s, None)
        self.assert_(v.isoformat(' ') == result)

    def test_base_table(self):
        """
        Test db.Base is setup correctly
        """
        m = meta.BaubleMeta(name=u'name', value=u'value')
        self.session.add(m)
        self.session.commit()
        m = self.session.query(meta.BaubleMeta).filter_by(name=u'name').first()

        # test that _created and _last_updated were created correctly
        self.assert_(hasattr(m, '_created')
                     and isinstance(m._created, datetime.datetime))
        self.assert_(hasattr(m, '_last_updated')
                     and isinstance(m._last_updated, datetime.datetime))

        # test that created does not change when the value is updated
        # but that last_updated does
        created = m._created
        last_updated = m._last_updated
        # sleep for one second before committing since the DateTime
        # column only has one second granularity
        time.sleep(1.1)
        m.value = u'value2'
        self.session.commit()
        self.session.expire(m)
        self.assert_(isinstance(m._created, datetime.datetime))
        self.assert_(m._created == created)
        self.assert_(isinstance(m._last_updated, datetime.datetime))
        self.assert_(m._last_updated != last_updated)

    def test_duplicate_ids(self):
        """
        Test for duplicate ids for all .glade files in the bauble module
        """
        import bauble as mod
        import glob
        head, tail = os.path.split(mod.__file__)
        files = glob.glob(os.path.join(head, '*.glade'))
        for f in files:
            try:
                ids = check_dupids(f)
            except:
                print 'error parsing', f
                raise
            self.assert_(ids == [], "%s has duplicate ids: %s" % (f, str(ids)))


class HistoryTests(BaubleTestCase):

    def test(self):
        """
        Test the HistoryMapperExtension
        """
        from bauble.plugins.plants import Family
        f = Family(family=u'Family')
        self.session.add(f)
        self.session.commit()
        history = self.session.query(db.History).\
            order_by(db.History.timestamp.desc()).first()
        assert history.table_name == 'family' and history.operation == 'insert'

        f.family = u'Family2'
        self.session.commit()
        history = self.session.query(db.History).\
            order_by(db.History.timestamp.desc()).first()
        assert history.table_name == 'family' and history.operation == 'update'

        self.session.delete(f)
        self.session.commit()
        history = self.session.query(db.History).\
            order_by(db.History.timestamp.desc()).first()
        assert history.table_name == 'family' and history.operation == 'delete'


class MVPTests(BaubleTestCase):

    def test_can_programmatically_connect_signals(self):
        from bauble.editor import (
            GenericEditorPresenter, GenericEditorView)

        class HandlerDefiningPresenter(GenericEditorPresenter):
            def on_tag_desc_textbuffer_changed(self, *args):
                pass

        model = db.History()
        import tempfile
        ntf = tempfile.NamedTemporaryFile()
        ntf.write('''\
<interface>
  <requires lib="gtk+" version="2.24"/>
  <!-- interface-naming-policy toplevel-contextual -->
  <object class="GtkTextBuffer" id="tag_desc_textbuffer">
    <signal name="changed" handler="on_tag_desc_textbuffer_changed" \
swapped="no"/>
  </object>
</interface>
''')
        ntf.flush()
        fn = ntf.name
        view = GenericEditorView(fn)
        presenter = HandlerDefiningPresenter(model, view)
        self.assertEquals(
            len(presenter.view._GenericEditorView__attached_signals), 1)
        presenter.on_tag_desc_textbuffer_changed()  # avoid uncounted line!


class GlobalFunctionsTests(BaubleTestCase):
    def test_newer_version_on_github(self):
        import StringIO
        from bauble import newer_version_on_github
        stream = StringIO.StringIO('version = "1.0.0"  # comment')
        self.assertFalse(newer_version_on_github(stream) and True or False)
        stream = StringIO.StringIO('version = "1.0.99999"  # comment')
        self.assertTrue(newer_version_on_github(stream) and True or False)
        stream = StringIO.StringIO('version = "1.0.99999"  # comment')
        self.assertEquals(newer_version_on_github(stream), '1.0.99999')
        stream = StringIO.StringIO('version = "1.099999"  # comment')
        self.assertFalse(newer_version_on_github(stream) and True or False)
        stream = StringIO.StringIO('version = "1.0.99999-dev"  # comment')
        self.assertFalse(newer_version_on_github(stream) and True or False)
