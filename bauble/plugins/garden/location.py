# -*- coding: utf-8 -*-
#
# Copyright 2008-2010 Brett Adams
# Copyright 2015 Mario Frasca <mario@anche.no>.
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
# location.py
#
import os
import traceback
import gtk

from sqlalchemy import Column, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.exc import DBAPIError

from bauble.i18n import _
import bauble
import bauble.db as db
from bauble.editor import GenericModelViewPresenterEditor, GenericEditorView, \
    GenericEditorPresenter, UnicodeOrNoneValidator
import bauble.utils as utils
import bauble.paths as paths
from bauble.view import Action


def edit_callback(locations):
    e = LocationEditor(model=locations[0])
    return e.start() is not None


def add_plants_callback(locations):
    # create a temporary session so that the temporary plant doesn't
    # get added to the accession
    session = db.Session()
    loc = session.merge(locations[0])
    from bauble.plugins.garden.plant import Plant, PlantEditor
    e = PlantEditor(model=Plant(location=loc))
    session.close()
    return e.start() is not None


def remove_callback(locations):
    loc = locations[0]
    s = '%s: %s' % (loc.__class__.__name__, str(loc))
    if len(loc.plants) > 0:
        msg = _('Please remove the plants from <b>%(location)s</b> '
                'before deleting it.') % {'location': loc}
        utils.message_dialog(msg, gtk.MESSAGE_WARNING)
        return
    msg = _("Are you sure you want to remove %s?") % \
        utils.xml_safe_utf8(s)
    if not utils.yes_no_dialog(msg):
        return
    try:
        session = db.Session()
        obj = session.query(Location).get(loc.id)
        session.delete(obj)
        session.commit()
    except Exception, e:
        msg = _('Could not delete.\n\n%s') % utils.xml_safe_utf8(e)
        utils.message_details_dialog(msg, traceback.format_exc(),
                                     type=gtk.MESSAGE_ERROR)
    return True

edit_action = Action('loc_edit', _('_Edit'), callback=edit_callback,
                     accelerator='<ctrl>e')
add_plant_action = Action('loc_add_plant', _('_Add plants'),
                          callback=add_plants_callback, accelerator='<ctrl>k')
remove_action = Action('loc_remove', _('_Delete'), callback=remove_callback,
                       accelerator='<ctrl>Delete', multiselect=True)

loc_context_menu = [edit_action, add_plant_action, remove_action]


def loc_markup_func(location):
    if location.description is not None:
        return utils.xml_safe(str(location)), \
            utils.xml_safe(str(location.description))
    else:
        return utils.xml_safe(str(location))


class Location(db.Base):
    """
    :Table name: location

    :Columns:
        *name*:

        *description*:

    :Relation:
        *plants*:

    """
    __tablename__ = 'location'
    __mapper_args__ = {'order_by': 'name'}

    # columns
    # refers to beds by unique codes
    code = Column(Unicode(10), unique=True, nullable=False)
    name = Column(Unicode(64))
    description = Column(UnicodeText)

    # relations
    plants = relation('Plant', backref=backref('location', uselist=False))

    def __str__(self):
        if self.name:
            return '(%s) %s' % (self.code, self.name)
        else:
            return str(self.code)

    def has_accessions(self):
        '''true if location is linked to at least one accession
        '''

        return False

    def as_dict(self):
        result = dict((col, getattr(self, col))
                      for col in self.__table__.columns.keys()
                      if col not in ['id']
                      and col[0] != '_'
                      and getattr(self, col) is not None
                      and not col.endswith('_id'))
        result['object'] = 'location'
        return result


class LocationEditorView(GenericEditorView):

    #source_expanded_pref = 'editor.accesssion.source.expanded'
    _tooltips = {
        'loc_name_entry': _('The name that you will use '
                            'later to refer to this location.'),
        'loc_desc_textview': _('Any information that might be relevant to '
                               'the location such as where it is or what\'s '
                               'its purpose')
        }

    def __init__(self, parent=None):
        GenericEditorView.__init__(self, os.path.join(paths.lib_dir(),
                                                      'plugins', 'garden',
                                                      'loc_editor.glade'),
                                   parent=parent)
        self.use_ok_and_add = True
        self.set_accept_buttons_sensitive(False)
        # if the parent isn't the main bauble window then we assume
        # that the LocationEditor was opened from the PlantEditor and
        # so we shouldn't enable adding more plants...this is a bit of
        # a hack but it serves our purposes
        if bauble.gui and parent != bauble.gui.window:
            self.use_ok_and_add = False

    def get_window(self):
        return self.widgets.location_dialog

    def set_accept_buttons_sensitive(self, sensitive):
        self.widgets.loc_ok_button.set_sensitive(sensitive)
        self.widgets.loc_ok_and_add_button.set_sensitive(self.use_ok_and_add
                                                         and sensitive)
        self.widgets.loc_next_button.set_sensitive(sensitive)

    def start(self):
        return self.get_window().run()


class LocationEditorPresenter(GenericEditorPresenter):

    widget_to_field_map = {'loc_name_entry': 'name',
                           'loc_code_entry': 'code',
                           'loc_desc_textview': 'description'}

    def __init__(self, model, view):
        '''
        model: should be an instance of class Accession
        view: should be an instance of AccessionEditorView
        '''
        GenericEditorPresenter.__init__(self, model, view)
        self.session = object_session(model)
        self.__dirty = False

        # initialize widgets
        self.refresh_view()  # put model values in view

        # connect signals
        self.assign_simple_handler('loc_name_entry', 'name',
                                   UnicodeOrNoneValidator())
        self.assign_simple_handler('loc_code_entry', 'code',
                                   UnicodeOrNoneValidator())
        self.assign_simple_handler('loc_desc_textview', 'description',
                                   UnicodeOrNoneValidator())
        self.refresh_sensitivity()
        if self.model not in self.session.new:
            self.view.widgets.loc_ok_and_add_button.set_sensitive(True)

    def refresh_sensitivity(self):
        sensitive = False
        ignore = ('id')
        if self.dirty() and not \
                utils.get_invalid_columns(self.model, ignore_columns=ignore):
            sensitive = True
        self.view.set_accept_buttons_sensitive(sensitive)

    def set_model_attr(self, attr, value, validator=None):
        super(LocationEditorPresenter, self).\
            set_model_attr(attr, value, validator)
        self.__dirty = True
        self.refresh_sensitivity()

    def dirty(self):
        return self.__dirty

    def refresh_view(self):
        for widget, field in self.widget_to_field_map.iteritems():
            value = getattr(self.model, field)
            self.view.set_widget_value(widget, value)

    def start(self):
        r = self.view.start()
        return r


class LocationEditor(GenericModelViewPresenterEditor):

    # these have to correspond to the response values in the view
    RESPONSE_OK_AND_ADD = 11
    RESPONSE_NEXT = 22
    ok_responses = (RESPONSE_OK_AND_ADD, RESPONSE_NEXT)

    def __init__(self, model=None, parent=None):
        '''
        :param model: Location instance or None
        :param parent: the parent widget or None
        '''
        # view and presenter are created in self.start()
        self.view = None
        self.presenter = None
        if model is None:
            model = Location()
        super(LocationEditor, self).__init__(model, parent)
        if not parent and bauble.gui:
            parent = bauble.gui.window
        self.parent = parent
        self._committed = []

        view = LocationEditorView(parent=self.parent)
        self.presenter = LocationEditorPresenter(self.model, view)

        # add quick response keys
        self.attach_response(view.get_window(), gtk.RESPONSE_OK, 'Return',
                             gtk.gdk.CONTROL_MASK)
        self.attach_response(view.get_window(), self.RESPONSE_OK_AND_ADD, 'k',
                             gtk.gdk.CONTROL_MASK)
        self.attach_response(view.get_window(), self.RESPONSE_NEXT, 'n',
                             gtk.gdk.CONTROL_MASK)

    def handle_response(self, response):
        '''
        handle the response from self.presenter.start() in self.start()
        '''
        not_ok_msg = 'Are you sure you want to lose your changes?'
        if response == gtk.RESPONSE_OK or response in self.ok_responses:
            try:
                if self.presenter.dirty():
                    self.commit_changes()
                self._committed.append(self.model)
            except DBAPIError, e:
                msg = _('Error committing changes.\n\n%s') % \
                    utils.xml_safe_utf8(e.orig)
                utils.message_details_dialog(msg, str(e), gtk.MESSAGE_ERROR)
                self.session.rollback()
                return False
            except Exception, e:
                msg = _('Unknown error when committing changes. See the '
                        'details for more information.\n\n%s') % \
                    utils.xml_safe_utf8(e)
                utils.message_details_dialog(msg, traceback.format_exc(),
                                             gtk.MESSAGE_ERROR)
                self.session.rollback()
                return False
        elif self.presenter.dirty() \
                and utils.yes_no_dialog(not_ok_msg) \
                or not self.presenter.dirty():
            self.session.rollback()
            return True
        else:
            return False

        # respond to responses
        more_committed = None
        if response == self.RESPONSE_NEXT:
            self.presenter.cleanup()
            e = LocationEditor(parent=self.parent)
            more_committed = e.start()
        elif response == self.RESPONSE_OK_AND_ADD:
            from bauble.plugins.garden.plant import PlantEditor, Plant
            e = PlantEditor(Plant(location=self.model), self.parent)
            more_committed = e.start()
        if more_committed is not None:
            if isinstance(more_committed, list):
                self._committed.extend(more_committed)
            else:
                self._committed.append(more_committed)

        return True

    def start(self):
        """
        Started the LocationEditor and return the committed Location objects.
        """
        while True:
            response = self.presenter.start()
            self.presenter.view.save_state()
            if self.handle_response(response):
                break
        self.session.close()
        self.presenter.cleanup()
        return self._committed


from bauble.view import InfoBox, InfoExpander, PropertiesExpander


class GeneralLocationExpander(InfoExpander):
    """
    general expander for the PlantInfoBox
    """

    def __init__(self, widgets):
        '''
        '''
        InfoExpander.__init__(self, _("General"), widgets)
        general_box = self.widgets.loc_gen_box
        self.widgets.remove_parent(general_box)
        self.vbox.pack_start(general_box)

    def update(self, row):
        '''
        '''
        from bauble.plugins.garden.plant import Plant
        self.set_widget_value('loc_name_data',
                              '<big>%s</big>' % utils.xml_safe(str(row)),
                              markup=True)
        session = object_session(row)
        nplants = session.query(Plant).filter_by(location_id=row.id).count()
        self.set_widget_value('loc_nplants_data', nplants)


class DescriptionExpander(InfoExpander):
    """
    The location description
    """

    def __init__(self, widgets):
        InfoExpander.__init__(self, _("Description"), widgets)
        descr_box = self.widgets.loc_descr_box
        self.widgets.remove_parent(descr_box)
        self.vbox.pack_start(descr_box)

    def update(self, row):
        '''
        '''
        if row.description is None:
            self.set_expanded(False)
            self.set_sensitive(False)
        else:
            self.set_expanded(True)
            self.set_sensitive(True)
            self.set_widget_value('loc_descr_data', str(row.description))


class LocationInfoBox(InfoBox):
    """
    an InfoBox for a Location table row
    """

    def __init__(self):
        '''
        '''
        InfoBox.__init__(self)
        filename = os.path.join(paths.lib_dir(), "plugins", "garden",
                                "loc_infobox.glade")
        self.widgets = utils.load_widgets(filename)
        self.general = GeneralLocationExpander(self.widgets)
        self.add_expander(self.general)
        self.description = DescriptionExpander(self.widgets)
        self.add_expander(self.description)
        self.props = PropertiesExpander()
        self.add_expander(self.props)

    def update(self, row):
        '''
        '''
        self.general.update(row)
        self.description.update(row)
        self.props.update(row)
