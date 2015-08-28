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

import logging
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

from sqlalchemy.orm import object_session, eagerload

import bauble
from bauble.i18n import _
import bauble.utils as utils
import bauble.pluginmgr as pluginmgr
from bauble.view import SearchView
from bauble.plugins.garden.accession import AccessionEditor, \
    Accession, AccessionInfoBox, AccessionNote, \
    acc_context_menu, acc_markup_func
from bauble.plugins.garden.location import LocationEditor, \
    Location, LocationInfoBox, loc_context_menu, loc_markup_func
from bauble.plugins.garden.plant import PlantEditor, PlantNote, \
    Plant, PlantSearch, PlantInfoBox, plant_context_menu, plant_markup_func, \
    plant_delimiter_key, default_plant_delimiter
from bauble.plugins.garden.source import \
    Source, SourceDetail, SourceDetailInfoBox, source_detail_context_menu, \
    Collection, collection_context_menu, coll_markup_func
from bauble.plugins.garden.institution import \
    Institution, InstitutionCommand, InstitutionTool
#from bauble.plugins.garden.propagation import *
import bauble.search as search
import re

Institution  # fake usage to avoid 'Imported but unused' warning.

# other ideas:
# - cultivation table
# - conservation table


def natsort_kids(kids):
    return lambda(parent): sorted(getattr(parent, kids), key=utils.natsort_key)


class GardenPlugin(pluginmgr.Plugin):

    depends = ["PlantsPlugin"]
    tools = [InstitutionTool]
    commands = [InstitutionCommand]

    @classmethod
    def install(cls, *args, **kwargs):
        pass

    @classmethod
    def init(cls):
        from bauble.plugins.plants import Species
        mapper_search = search.get_strategy('MapperSearch')

        mapper_search.add_meta(('accession', 'acc'), Accession, ['code'])
        SearchView.view_meta[Accession].set(children=natsort_kids("plants"),
                                            infobox=AccessionInfoBox,
                                            context_menu=acc_context_menu,
                                            markup_func=acc_markup_func)

        mapper_search.add_meta(('location', 'loc'), Location, ['name', 'code'])
        SearchView.view_meta[Location].set(children=natsort_kids('plants'),
                                           infobox=LocationInfoBox,
                                           context_menu=loc_context_menu,
                                           markup_func=loc_markup_func)

        mapper_search.add_meta(('plant', 'plants'), Plant, ['code'])
        search.add_strategy(PlantSearch)  # special search value strategy
        #search.add_strategy(SpeciesSearch)  # special search value strategy
        SearchView.view_meta[Plant].set(infobox=PlantInfoBox,
                                        context_menu=plant_context_menu,
                                        markup_func=plant_markup_func)

        mapper_search.add_meta(('contact', 'contacts', 'person', 'org',
                                'source'), SourceDetail, ['name'])

        def sd_kids(detail):
            session = object_session(detail)
            results = session.query(Accession).join(Source).\
                join(SourceDetail).options(eagerload('species')).\
                filter(SourceDetail.id == detail.id).all()
            return results
        sd_markup_func = lambda c: utils.xml_safe(c)
        SearchView.view_meta[SourceDetail].set(
            children=sd_kids,
            infobox=SourceDetailInfoBox,
            markup_func=sd_markup_func,
            context_menu=source_detail_context_menu)

        mapper_search.add_meta(('collection', 'col', 'coll'),
                               Collection, ['locale'])
        coll_kids = lambda coll: sorted(coll.source.accession.plants,
                                        key=utils.natsort_key)
        SearchView.view_meta[Collection].set(
            children=coll_kids,
            infobox=AccessionInfoBox,
            markup_func=coll_markup_func,
            context_menu=collection_context_menu)

        # done here b/c the Species table is not part of this plugin
        SearchView.view_meta[Species].child = "accessions"

        if bauble.gui is not None:
            bauble.gui.add_to_insert_menu(AccessionEditor, _('Accession'))
            bauble.gui.add_to_insert_menu(PlantEditor, _('Plant'))
            bauble.gui.add_to_insert_menu(LocationEditor, _('Location'))
            #bauble.gui.add_to_insert_menu(ContactEditor, _('Contact'))

        # if the plant delimiter isn't in the bauble meta then add the default
        import bauble.meta as meta
        meta.get_default(plant_delimiter_key, default_plant_delimiter)


def init_location_comboentry(presenter, combo, on_select, required=True):
    """
    A comboentry that allows the location to be entered requires
    more custom setup than view.attach_completion and
    self.assign_simple_handler can provides.  This method allows us to
    have completions on the location entry based on the location code,
    location name and location string as well as selecting a location
    from a combo drop down.

    :param presenter:
    :param combo:
    :param on_select: a one-parameter function
    """
    PROBLEM = 'UNKNOWN_LOCATION'
    re_code_name_splitter = re.compile('\(([^)]+)\) ?(.*)')

    def cell_data_func(col, cell, model, treeiter, data=None):
        cell.props.text = utils.utf8(model[treeiter][0])

    import gtk
    completion = gtk.EntryCompletion()
    cell = gtk.CellRendererText()  # set up the completion renderer
    completion.pack_start(cell)
    completion.set_cell_data_func(cell, cell_data_func)
    completion.props.popup_set_width = False

    entry = combo.child
    entry.set_completion(completion)

    combo.clear()
    cell = gtk.CellRendererText()
    combo.pack_start(cell)
    combo.set_cell_data_func(cell, cell_data_func)

    model = gtk.ListStore(object)
    locations = sorted(presenter.session.query(Location).all(),
                       key=lambda loc: utils.natsort_key(loc.code))
    map(lambda loc: model.append([loc]), locations)
    combo.set_model(model)
    completion.set_model(model)

    def match_func(completion, key, treeiter, data=None):
        logger.debug('match_func')
        loc = completion.get_model()[treeiter][0]
        return (loc.name and loc.name.lower().startswith(key.lower())) or \
               (loc.code and loc.code.lower().startswith(key.lower()))

    completion.set_match_func(match_func)

    def on_match_select(completion, model, treeiter):
        logger.debug('on_match_select')
        value = model[treeiter][0]
        on_select(value)
        entry.props.text = str(value)
        presenter.remove_problem(PROBLEM, entry)
        presenter.refresh_sensitivity()
        return True

    presenter.view.connect(completion, 'match-selected', on_match_select)

    def on_entry_changed(entry, presenter):
        logger.debug('on_entry_changed(%s, %s)', entry, presenter)
        text = utils.utf8(entry.props.text)

        if not text and not required:
            presenter.remove_problem(PROBLEM, entry)
            on_select(None)
            return
        # see if the text matches a completion string
        comp = entry.get_completion()
        compl_model = comp.get_model()

        def _cmp(row, data):
            return utils.utf8(row[0]) == data

        found = utils.search_tree_model(compl_model, text, _cmp)
        if len(found) == 1:
            comp.emit('match-selected', compl_model, found[0])
            return True
        # if text looks like '(code) name', then split it into the two
        # parts, then see if the text matches exactly a code or name
        match = re_code_name_splitter.match(text)
        if match:
            code, name = match.groups()
        else:
            code = name = text
        codes = presenter.session.query(Location).\
            filter(utils.ilike(Location.code, '%s' % utils.utf8(code)))
        names = presenter.session.query(Location).\
            filter(utils.ilike(Location.name, '%s' % utils.utf8(name)))
        if codes.count() == 1:
            logger.debug('location matches code')
            location = codes.first()
            presenter.remove_problem(PROBLEM, entry)
            on_select(location)
        elif names.count() == 1:
            logger.debug('location matches name')
            location = names.first()
            presenter.remove_problem(PROBLEM, entry)
            on_select(location)
        else:
            logger.debug('location %s does not match anything' % text)
            presenter.add_problem(PROBLEM, entry)
        return True

    presenter.view.connect(entry, 'changed', on_entry_changed, presenter)

    def on_combo_changed(combo, *args):
        model = combo.get_model()
        i = combo.get_active_iter()
        if not i:
            return
        location = combo.get_model()[i][0]
        combo.child.props.text = str(location)
    presenter.view.connect(combo, 'changed', on_combo_changed)


import bauble.db as db

plugin = GardenPlugin

## make names visible to db module
db.Accession = Accession
db.AccessionNote = AccessionNote
db.Plant = Plant
db.PlantNote = PlantNote
db.Location = Location
