#
# Genera table module
#

import gtk
from sqlobject import *
from bauble.plugins import BaubleTable, tables, editors
from bauble.treevieweditor import TreeViewEditorDialog

# TODO: should be a higher_taxon column that holds values into 
# subgen, subfam, tribes etc, maybe this should be included in Genus

# TODO: since there can be more than one genus with the same name but
# different authors we need to show the Genus author in the result search
# and at least give the Genus it's own infobox, we should also check if
# when entering a plantname with a chosen genus if that genus has an author
# ask the user if they want to use the accepted name and show the author of
# the genus then so they aren't using the wrong version of the Genus,
# e.g. Cananga

#
# Genus table
#
class Genus(BaubleTable):

    class sqlmeta(BaubleTable.sqlmeta):
        defaultOrder = 'genus'
    
    # it is possible that there can be genera with the same name but 
    # different authors and probably means that at different points in literature
    # this name was used but is now a synonym even though it may not be a
    # synonym for the same species,
    # this screws us up b/c you can now enter duplicate genera, somehow
    # NOTE: we should at least warn the user that a duplicate is being entered
    genus = StringCol(length=50)    
            
    '''
    hybrid: indicates whether the name in the Genus Name field refers to an 
    Intergeneric hybrid or an Intergeneric graft chimaera.
    Content of genhyb   Nature of Name in gen
     H        An intergeneric hybrid collective name
     x        An Intergeneric Hybrid
     +        An Intergeneric Graft Hybrid or Graft Chimaera
    '''
    hybrid = EnumCol(enumValues=("H", "x", "+", None), default=None) 
    '''    
    The qualifier field designates the botanical status of the genus.
    Possible values:
        s. lat. - aggregrate family (sensu lato)
        s. str. segregate family (sensu stricto)
    '''
    qualifier = EnumCol(enumValues=('s. lat.', 's. str.', None), default=None)
    author = UnicodeCol(length=255, default=None)
    notes = UnicodeCol(default=None)
    
    # indices
    # we can't do this right now unless we do more work on 
    # the synonyms table, see 
    # {'author': 'Raf.', 'synonymID': 13361, 'familyID': 214, 'genus': 'Trisiola', 'id': 15845}
    # in Genus.txt
    genus_index = DatabaseIndex('genus', 'author', 'family', unique=True)
    
    # foreign keys
    family = ForeignKey('Family', notNull=True, cascade=False)
    
    # joins
    species = MultipleJoin("Species", joinColumn="genus_id")
    synonyms = MultipleJoin('GenusSynonym', joinColumn='genus_id')    


    def __str__(self):
        if self.hybrid:
            return '%s %s' % (self.hybrid, self.genus)
        else:
            return self.genus
        
        
        
class GenusSynonym(BaubleTable):
    
    # deleting either of the genera this synonym refers to makes this 
    # synonym irrelevant
    genus = ForeignKey('Genus', default=None, cascade=True)
    synonym = ForeignKey('Genus', cascade=True)
    
    def __str__(self):
        return self. synonym

    def markup(self):
        return '%s (syn. of %f)' % (self.synonym, self.genus)
    
#
# editor
#
class GenusEditor(TreeViewEditorDialog):

    visible_columns_pref = "editor.genus.columns"
    column_width_pref = "editor.genus.column_width"
    default_visible_list = ['family', 'genus']
    
    label = 'Genus'
    
    def __init__(self, parent=None, select=None, defaults={}, **kwargs):
        TreeViewEditorDialog.__init__(self, tables["Genus"], "Genus Editor", 
                                      parent, select=select, defaults=defaults,
                                      **kwargs)
        titles = {'genus': 'Genus',
                  'author': 'Author',
                  'hybrid': 'Hybrid',
                  'familyID': 'Family',
                  'qualifier': 'Qualifier',
                  'notes': 'Notes',
                  'synonyms': 'Synonyms'}
        self.columns.titles = titles
        self.columns["familyID"].meta.get_completions = self.get_family_completions
        self.columns['synonyms'].meta.editor = editors["GenusSynonymEditor"]


    def get_family_completions(self, text):
        model = gtk.ListStore(str, object)
        sr = tables["Family"].select("family LIKE '"+text+"%'")
        for row in sr:            
            model.append([str(row), row])
        return model


# 
# GenusSynonymEditor
#
class GenusSynonymEditor(TreeViewEditorDialog):

    visible_columns_pref = "editor.genus_syn.columns"
    column_width_pref = "editor.genus_syn.column_width"
    default_visible_list = ['synonym']
    
    standalone = False
    label = 'Genus Synonym'
    
    def __init__(self, parent=None, select=None, defaults={}):
        TreeViewEditorDialog.__init__(self, tables["GenusSynonym"],
                                      "Genus Synonym Editor", 
                                      parent, select=select, defaults=defaults, 
                                      **kwargs)
        titles = {'synonymID': 'Synonym of Genus'}
                  
        # can't be edited as a standalone so the family should only be set by
        # the parent editor
        self.columns.pop('genusID')
        
        self.columns.titles = titles
        self.columns["synonymID"].meta.get_completions = self.get_genus_completions

        
    def get_genus_completions(self, text):
        model = gtk.ListStore(str, object)
        sr = tables["Genus"].select("genus LIKE '"+text+"%'")
        for row in sr:
            model.append([str(row), row])
        return model
        
#
# infobox
#
try:
    from bauble.plugins.searchview.infobox import InfoBox, InfoExpander
except ImportError:
    pass
else:
    class GeneraInfoBox(InfoBox):
        """
        - number of taxon in number of accessions
        - references
        """
        def __init__(self):
            InfoBox.__init__(self)
