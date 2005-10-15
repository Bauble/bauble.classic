
#from accession import *
#from cultivation import *

# TODO: there is going to be problem with the accessions MultipleJoin
# in plantnames, plants should really have to depend on garden unless
# plants is contained within garden, but what about herbaria, they would
# also need to depend on plants, what we could do is have another class
# with the same name as the other table that defines new columns/joins
# for that class or probably not add new columns but add new joins 
# dynamically

# TODO: should create the table the first time this plugin is loaded, if a new 
# database is created there should be a way to recreate everything from scratch

import os
import bauble.utils as utils
import bauble.paths as paths
from bauble.plugins import BaublePlugin, plugins
from family import Family, FamilyEditor
from genus import Genus, GenusEditor
from plantname import Plantname, PlantMeta, PlantnameEditor, PlantnameInfoBox
from vernacularname import VernacularName


class PlantsPlugin(BaublePlugin):
    tables = [Family, Genus, Plantname, PlantMeta, VernacularName]
    editors = [FamilyEditor, GenusEditor, PlantnameEditor]
    
    @classmethod
    def init(cls):                
        #if plugins.has_plugin("SearchViewPlugin"):
        if "SearchViewPlugin" in plugins:
            from bauble.plugins.searchview.search import SearchMeta
            from bauble.plugins.searchview.search import ResultsMeta
            from bauble.plugins.searchview.search import SearchView
            
            search_meta = SearchMeta("Family", ["family"], "family")
            SearchView.register_search_meta("family", search_meta)
            SearchView.register_search_meta("fam", search_meta)            
            SearchView.view_meta["Family"].set("genera", FamilyEditor)

            
            search_meta = SearchMeta("Genus", ["genus"], "genus")
            SearchView.register_search_meta("genus", search_meta)
            SearchView.register_search_meta("gen", search_meta)
            SearchView.view_meta["Genus"].set("plantnames", GenusEditor)
            
            search_meta = SearchMeta("Plantname", ["sp", "isp"], "sp")
            SearchView.register_search_meta("name", search_meta)
            SearchView.register_search_meta("sp", search_meta)
            
            SearchView.view_meta["Plantname"].set(editor=PlantnameEditor, 
                                                  infobox=PlantnameInfoBox)
            
    @classmethod
    def create_tables(cls):
        super(PlantsPlugin, cls).create_tables()
        from bauble.plugins.imex_csv import CSVImporter
        csv = CSVImporter()    
#        path = os.path.dirname(__file__) + os.sep + 'default'
        path = os.path.join(paths.lib_dir(), "plugins", "plants", "default")
        files = ['Family.txt']#,'Genus.txt', 'Plantname.txt']
        csv.start([path+os.sep+f for f in files])
        
        # genera and plantnames take along time so ask the user if
        # they want to import them
        if utils.yes_no_dialog("Would you like to import the Genera?"):            
            if csv.start([path + os.sep + "Genus.txt"]):
                if utils.yes_no_dialog("Would you like to import the Plantnames?"):
                    csv.start([path + os.sep + "Plantname.txt"])

    
    def install(cls):
        """
        do any setup and configuration required bt this plugin like
        creating tables, etc...
        """
        cls.create_tables()
        
plugin = PlantsPlugin
