#
# XML import/export plugin
#
# Description: handle import and exporting from a simple XML format
#
import os, csv, traceback
import gtk.gdk, gobject
from sqlalchemy import *
import bauble
from bauble.i18n import *
import bauble.utils as utils
import bauble.pluginmgr as plugin
import bauble.task
from bauble.utils import xml_safe
from bauble.utils.log import log, debug
import bauble.utils.gtasklet as gtasklet

# <tableset>
# <table name="tablename">
#  <row>
#    <column name='colname'>
#       ...
#    </column>
#  </row>
# </table>
# <table>
# </tablest>


# TODO: single file or one file per table

def ElementFactory(parent, name, **kwargs):
    try:
        text = kwargs.pop('text')
    except KeyError:
        text = None
    el = etree.SubElement(parent, name, **kwargs)
    try:
        if text is not None:
            el.text = unicode(text, 'utf8')
    except (AssertionError, TypeError), e:
        el.text = unicode(str(text), 'utf8')
    return el



class XMLExporter:

    def __init__(self):
        pass


    def start(self, path=None):

        d = gtk.Dialog('Bauble - XML Exporter', bauble.gui.window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                       (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        box = gtk.VBox(spacing=20)
        d.vbox.pack_start(box, padding=10)

        file_chooser = gtk.FileChooserButton(_('Select a directory'))
        file_chooser.set_select_multiple(False)
        file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        box.pack_start(file_chooser)
        check = gtk.CheckButton(_('Save all data in one file'))
        check.set_active(True)
        box.pack_start(check)

        d.connect('response', self.on_dialog_response,
                  file_chooser.get_filename(), check.get_active())
        d.show_all()
        d.run()
        d.hide()


    def on_dialog_response(self, dialog, response, filename, one_file):
        debug('on_dialog_response(%s, %s)' % (filename, one_file))
        if response == gtk.RESPONSE_ACCEPT:
            self.__export_task(filename, one_file)
        dialog.destroy()


    def __export_task(self, path, one_file=True):
        timeout = gtasklet.WaitForTimeout(12)
        ntables = len(bauble.metadata.tables)
        steps_so_far = 0
        if not one_file:
            tableset_el = etree.Element('tableset')

        for table_name, table in tables.iteritems():
            if one_file:
                tableset_el = etree.Element('tableset')
            log.info('exporting %s...' % table_name)
            table_el = ElementFactory(tableset_el, 'table',
                                      attrib={'name': table_name})
            results = table.select().execute().fetchall()
            columns = table.c.keys()
            try:
                for row in results:
                    row_el = ElementFactory(table_el, 'row')
                    for col in columns:
                        ElementFactory(row_el, 'column', attrib={'name': col},
                                       text=row[col])
            except ValueError, e:
                utils.message_details_dialog(utils.xml_safe_utf8(e),
                                             traceback.format_exc(),
                                             gtk.MESSAGE_ERROR)
                return
            else:
                if one_file:
                    tree = etree.ElementTree(tableset_el)
                    filename = os.path.join(path, '%s.xml' % table_name)
                    # TODO: can figure out why this keeps crashing
                    tree.write(filename, encoding='utf8', xml_declaration=True)

        if not one_file:
            tree = etree.ElementTree(tableset_el)
            filename = os.path.join(path, 'bauble.xml')
            tree.write(filename, encoding='utf8', xml_declaration=True)



class XMLExportCommandHandler(plugin.CommandHandler):

    command = 'exxml'

    def __call__(self, arg):
        debug('XMLExportCommandHandler(%s)' % arg)
        exporter = XMLExporter()
        debug('starting')
        exporter.start(arg)
        debug('started')



class XMLExportTool(plugin.Tool):

    category = "Export"
    label = "XML"

    @classmethod
    def start(cls):
        c = XMLExporter()
        c.start()



class XMLImexPlugin(plugin.Plugin):
    tools = [XMLExportTool]
    commands = [XMLExportCommandHandler]


try:
    import lxml.etree as etree
except ImportError:
    utils.message_dialog('The <i>lxml</i> package is required for the '\
                         'XML Import/Exporter plugin')
else:
    plugin = XMLImexPlugin
