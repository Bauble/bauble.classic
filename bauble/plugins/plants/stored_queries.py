# -*- coding: utf-8 -*-
#
# Copyright 2016 Mario Frasca <mario@anche.no>.
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

import gtk

import logging
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

from bauble import db, meta, editor, paths, pluginmgr
from bauble.i18n import _
import os.path


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        return instance


class StoredQueriesModel(object):
    def __init__(self):
        self.__label = [''] * 11
        self.__tooltip = [''] * 11
        self.__query = [''] * 11
        ssn = db.Session()
        q = ssn.query(meta.BaubleMeta)
        stqrq = q.filter(meta.BaubleMeta.name.startswith(u'stqr_'))
        for item in stqrq:
            index = int(item.name[5:])
            self[index] = item.value
        ssn.close()
        self.page = 1

    def __repr__(self):
        return '[p:%d; l:%s; t:%s; q:%s' % (
            self.page, self.__label[1:], self.__tooltip[1:], self.__query[1:])

    def save(self):
        ssn = db.Session()
        for index in range(1, 11):
            obj = get_or_create(ssn, meta.BaubleMeta,
                                name=u'stqr_%02d' % index)
            if self.__label[index] == '':
                ssn.delete(obj)
            obj.value = self[index]
        ssn.commit()
        ssn.close()

    def __getitem__(self, index):
        return u'%s:%s:%s' % (self.__label[index],
                              self.__tooltip[index],
                              self.__query[index])

    def __setitem__(self, index, value):
        self.page = index
        self.label, self.tooltip, self.query = value.split(':', 2)

    def __iter__(self):
        self.__index = 0
        return self

    def next(self):
        if self.__index == 10:
            raise StopIteration
        else:
            self.__index += 1
            return self[self.__index]

    @property
    def label(self):
        return self.__label[self.page]

    @label.setter
    def label(self, value):
        self.__label[self.page] = value

    @property
    def tooltip(self):
        return self.__tooltip[self.page]

    @tooltip.setter
    def tooltip(self, value):
        self.__tooltip[self.page] = value

    @property
    def query(self):
        return self.__query[self.page]

    @query.setter
    def query(self, value):
        self.__query[self.page] = value


class StoredQueriesPresenter(editor.GenericEditorPresenter):

    widget_to_field_map = {
        'stqr_label_entry': 'label',
        'stqr_tooltip_entry': 'tooltip',
        'stqr_query_textbuffer': 'query'}

    view_accept_buttons = ['stqr_ok_button', ]

    def on_tag_desc_textbuffer_changed(self, widget, value=None):
        return super(StoredQueriesPresenter, self).on_textbuffer_changed(
            widget, value, attr='query')

    def refresh_toggles(self):
        for i in range(1, 11):
            iter_name = 'stqr_%02d_button' % i
            iter_widget = getattr(self.view.widgets, iter_name)
            iter_widget.set_active(i == self.model.page)

    def refresh_view(self):
        super(StoredQueriesPresenter, self).refresh_view()
        self.refresh_toggles()

    def on_button_clicked(self, widget, *args):
        if widget.get_active() is False:
            return
        widget_name = gtk.Buildable.get_name(widget)
        self.model.page = int(widget_name[5:7])
        self.refresh_view()

    def on_stqr_query_textbuffer_changed(self, widget, value=None, attr=None):
        return self.on_textbuffer_changed(widget, value, attr='query')


def edit_callback():
    session = db.Session()
    view = editor.GenericEditorView(
        os.path.join(paths.lib_dir(),
                     'plugins', 'plants', 'stored_queries.glade'),
        parent=None,
        root_widget_name='stqr_dialog')
    stored_queries = StoredQueriesModel()
    presenter = StoredQueriesPresenter(
        stored_queries, view, session=session, refresh_view=True)
    error_state = presenter.start()
    if error_state > 0:
        stored_queries.save()
    session.close()
    return error_state


class StoredQueryEditorTool(pluginmgr.Tool):
    label = _('Edit stored queries')

    @classmethod
    def start(self):
        edit_callback()
