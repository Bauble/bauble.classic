#
# this is just a dummy file so i can import on this directory
#

import imp, os, sys, re
import gtk
import bauble


def search_tree_model(rows, data, func=lambda row, data: row[0] == data):
    '''
    got this from the pygtk tutorial
    '''
    if not rows:
	return None
    for row in rows:
	if func(row, data):
	    return row
	result = search_tree_model(row.iterchildren(), func, data)
	if result:
	    return result
    return None


def set_combo_from_value(combo, value, cmp=lambda row, value: row[0] == value):
    '''
    find value in combo model and set it as active, else raise ValueError
    cmp(row, value) is the a function to use for comparison
    NOTE: 
    '''
    model = combo.get_model()
    match = search_tree_model(model, value, cmp)
    if match is None:
	raise ValueError('set_combo_from_value() - could not find value in '\
			 'combo: %s' % value)
    combo.set_active_iter(match.iter)
    

def set_widget_value(glade_xml, widget_name, value, markup=True, default=""):
    '''
    glade_xml: the glade_file to get the widget from
    widget_name: the name of the widget
    value: the value to put in the widget
    markup: whether or not
    default: the default value to put in the widget if the value is None
    '''
#    debug(value)
    w = glade_xml.get_widget(widget_name)
    if value is None: 
        value = default

    if isinstance(w, gtk.Label):
        #w.set_text(str(value))
        # FIXME: some of the enum values that have <not set> as a values
        # will give errors here, but we can't escape the string because
        # if someone does pass something that needs to be marked up
        # then it won't display as intended, maybe BaubleTable.markup()
        # should be responsible for returning a properly escaped values
        if markup: 
            w.set_markup(str(value))
        else:
            w.set_text(str(value))            
    elif isinstance(w, gtk.TextView):
        w.get_buffer().set_text(value)
    elif isinstance(w, gtk.Entry):
	w.set_text(value)
    elif isinstance(w, gtk.ComboBox): # TODO: what about comboentry
	set_combo_from_value(w, value)
	
    else:
	raise TypeError('don\'t know how to handle the widget type %s with '\
			'name %s' % (type(w), widget_name))

# TODO: if i escape the messages that come in then my own markup doesn't 
# work, what really needs to be done is make sure that any exception that
# are going to be passed to one of these dialogs should be escaped before 
# coming through

def message_dialog(msg, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK):
    try: # this might get called before bauble has started
        parent = bauble.app.gui.window
    except:
	parent = None	
    d =gtk.MessageDialog(flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
			 parent=parent,
			 type=type, buttons=buttons)
    d.set_markup(msg)
    r = d.run()
    d.destroy()
    return r
    

def yes_no_dialog(msg):         
    try: # this might get called before bauble has started
	parent = bauble.app.gui.window
    except:
	parent = None
    d =gtk.MessageDialog(flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
			 parent=parent,
			 type=gtk.MESSAGE_QUESTION,
			 buttons = gtk.BUTTONS_YES_NO)            
    d.set_markup(msg)    
    r = d.run()
    d.destroy()
    return r == gtk.RESPONSE_YES


def message_details_dialog(msg, details, type=gtk.MESSAGE_INFO, 
                           buttons=gtk.BUTTONS_OK):    
    try: # this might get called before bauble has started
	parent = bauble.app.gui.window	
    except:	
	parent = None	
    d =gtk.MessageDialog(flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
			  parent=parent,
                          type=type, buttons=buttons)        
    d.set_markup(msg)
    expand = gtk.Expander("Details")    
    text_view = gtk.TextView()
    text_view.set_editable(False)
    text_view.set_wrap_mode(gtk.WRAP_WORD)
    tb = gtk.TextBuffer()
    tb.set_text(details)
    text_view.set_buffer(tb)
    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    sw.add(text_view)    
    expand.add(sw)
    d.vbox.pack_start(expand)
    d.show_all()
    r = d.run()
    d.destroy()
    return r


def startfile(filename):
    if sys.platform == 'win32':
        try:
            os.startfile(filename)
        except WindowsError, e: # probably no file association
            msg = "Could not open pdf file.\n\n%s" % str(e)
            message_dialog(msg)        
    elif sys.platform == 'linux2':
        # FIXME: need to determine if gnome or kde
        os.system("gnome-open " + filename)
    else:
        raise Exception("bauble.utils.startfile(): can't open file:" + filename)
        

def dms_to_decimal(dir, deg, min, sec):
    '''
    convert degrees, minutes, seconds to decimal
    '''
    # TODO: more test cases
    dec = (((sec/60.0) + min) /60.0) + deg
    if dir == 'W' or dir == 'S':
        dec = -dec
    return dec
    
        
def decimal_to_dms(decimal, long_or_lat):
    '''
    long_or_lat: should be either "long" or "lat"
    '''
    # NOTE: if speed is an issue, which i don't think it ever will be
    # this could probably be optimized
    # TODO: more test cases
    dir_map = { 'long': ['E', 'W'],
                'lat':  ['N', 'S']}
    dir = dir_map[long_or_lat][1]
    if decimal < 0:
        dir = dir_map[long_or_lat][0]
        
    dec = abs(decimal)
    d = abs(int(dec))
    m = abs((dec-d)*60)
    s = abs((int(m)-m) * 60)
    return dir, int(d), int(m), int(s)
    
    
def longitude_to_dms(decimal):
    return decimal_to_dms(decimal, 'long')

    
def latitude_to_dms(decimal):
    return decimal_to_dms(decimal, 'lat')
   
    
if __name__ == '__main__':
    '''
    could probably put this in a doctest
    '''
    dec = dms_to_decimal('W', 87, 43, 41)
    dir, deg, min, sec = decimal_to_dms(dec, 'long')
    print dec
    print '%s %d %d %d' % (dir, deg, min, sec)
   
   
