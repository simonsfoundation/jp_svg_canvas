from __future__ import print_function # For py 2.7 compat

from IPython.display import display, Javascript
#from IPython.html import widgets
import ipywidgets as widgets
from traitlets import Unicode, Float, List, Dict, HasTraits, Bool
import json
import os
import pprint
import IPython
import time

# XXXX I initially had difficulties directly passing
# complex structures like lists and dicts from the
# Python side to the javascript side.  To work around
# these difficulties the current implementation uses
# JSON encoded string encoding to pass values between
# the two interpreters.  It may be possible to remove
# this approach now or later.

# Other stroke attributes for line styling
STROKE_ATTRIBUTES = """
stroke stroke-width stroke-linecap stroke-dasharray
stroke-linejoin stroke-opacity
""".split()

[STROKE, WIDTH, LINECAP, DASHARRAY, LINEJOIN, OPACITY] = STROKE_ATTRIBUTES


JS_LOADED = [False]

def load_javascript_support(verbose=False, force=False):
    """
    Install javascript support required for this module into the notebook.
    """
    if (not JS_LOADED[0]) or force:
        my_dir = os.path.dirname(__file__)
        js_filename = os.path.join(my_dir, "canvas.js")
        assert os.path.exists(js_filename)
        if verbose:
            print("loading javascript from", repr(js_filename))
        display(Javascript(js_filename))
        JS_LOADED[0] = True
    else:
        if verbose:
            print ("canvas.js javascript support already loaded")


class SVGHelperMixin(HasTraits):
    """
    Common operations between interactive and embedded/noninteractive canvas implementations.
    """

    # XXX note: for some reason the traitlets don't work right with mixins 
    # in the widget protobol, so they are duplicated...
    
    # The javascript view name.
    _view_name = Unicode('SVGCanvasView').tag(sync=True)
    _view_module = Unicode("SVGCanvas").tag(sync=True)
    
    # SVG viewBox
    viewBox = Unicode("0 0 500 500", sync=True)
    view_minx = 0
    view_miny = 0
    view_width = 500
    view_height = 500

    # The bounding box set in response to "fit" command.
    boundingBox = Dict({}, sync=True)
    
    # Canvas width
    svg_width = Float(500, sync=True)
    
    # Canvas height
    svg_height = Float(500, sync=True)
    
    # SVG styling, JSON encoded dictionary
    svg_style = Unicode("{}", sync=True)
    
    # JSON encoded sequence of dictionaries describing actions.
    #commands = Unicode("[]", sync=True)

    # flag that indicates a command is pending for execution
    command_pending = Bool(False, sync=True)
    
    # White separated names of event to watch
    watch_event = Unicode("", sync=True)
    
    # White separated names of event to unwatch
    unwatch_event = Unicode("", sync=True)
    
    # Event captured (sent from js, jason encoded).
    #event = Unicode("{}", sync=True)
    
    # Buffered commands, list of dictionary (or None)
    buffered_commands = None
    
    # use this style dictionary if not provided
    default_style = {}
    
    # Set True to enable localized event callbacks
    # If set False then event callbacks attached to descendent elements to
    # the SVG canvas will not fire -- only the global default callback will fire.
    local_events = True

    # number of times to iterate awaiting pending comments.
    wait_iterations = 100

    # now long to sleep in wait loop
    wait_sleep = 0.1

    def await_pending_commands(self, verbose=False, strict=False):
        "Wait for javascript side to execute commands."
        if self.command_pending:
            ip = IPython.get_ipython()
            for i in range(self.wait_iterations):
                if verbose:
                    print ("awaiting pending commands " + str(i))
                time.sleep(self.wait_sleep)
                ip.kernel.do_one_iteration()
                if not self.command_pending:
                    break
        if strict and self.command_pending:
            self.command_pending = False
            raise RuntimeError("timeout awaiting pending commands.")
        self.command_pending = False


    def get_style(self):
        "Get the current SVG style."
        return json.loads(self.svg_style)
    
    def set_style(self, style_dict):
        "Set the current SVG style."
        self.svg_style = json.dumps(style_dict)
        
    def add_style(self, key, value):
        "Add an entry to the SVG style."
        style_dict = self.get_style()
        style_dict[key] = value
        self.set_style(style_dict)

    def set_view_box(self, minx, miny, width, height):
        "Change the SVG view box."
        assert width != 0
        assert height != 0
        self.view_minx = minx
        self.view_miny = miny
        self.view_width = width
        self.view_height = height
        self.viewBox = "%s %s %s %s" % (minx, miny, width, height)
        
    def text(self, name, x, y, text, fill="black", event_cb= None, style_dict=None, **other_attributes):
        "Add command to create a text element to the command buffer."
        tag = "text"
        atts = other_attributes.copy()
        atts["fill"] = fill
        atts["x"] = x
        atts["y"] = y
        self.add_element(name, tag, atts, style_dict, text=text, event_callback=event_cb)

    def line(self, name, x1, y1, x2, y2, color="black", width=None, 
             event_cb=None, style_dict=None, **other_attributes):
        "Add a command to create a line element ot the command buffer."
        tag = "line"
        atts = other_attributes.copy()
        atts["x1"] = x1
        atts["y1"] = y1
        atts["x2"] = x2
        atts["y2"] = y2
        if width:
            atts["stroke-width"] = width
        atts["stroke"] = color
        # use stroke attributes specified if provided.
        for att_name in STROKE_ATTRIBUTES:
            if att_name in other_attributes:
                atts[att_name] = other_attributes[att_name]
        self.add_element(name, tag, atts, style_dict, event_callback=event_cb)
        
    def circle(self, name, cx, cy, r, fill="black", event_cb=None, style_dict=None,
              **other_attributes):
        "Add a command to create a circle element to the command buffer."
        tag = "circle"
        atts = other_attributes.copy()
        atts["cx"] = cx
        atts["cy"] = cy
        atts["r"] = r
        atts["fill"] = fill
        self.add_element(name, tag, atts, style_dict, event_callback=event_cb)

    def rect(self, name, x, y, width, height, fill="black", event_cb=None, style_dict=None,
            **other_attributes):
        "Add a command to create a rectangle element to the command buffer."
        tag = "rect"
        atts = other_attributes.copy()
        atts["x"] = x
        atts["y"] = y
        atts["width"] = width
        atts["height"] = height
        atts["fill"] = fill
        self.add_element(name, tag, atts, style_dict, event_callback=event_cb)

    def polygon(self, name, points, fill=None, stroke=None, stroke_width=None, style_dict=None, 
            event_callback=None, **other_attributes):
        if style_dict is None:
            style_dict = {}
        style_dict = style_dict.copy()
        if fill is not None:
            style_dict["fill"] = fill
        if stroke is not None:
            style_dict["stroke"] = stroke
        if stroke_width is not None:
            style_dict["fill"] = fill
        points_fmt = " ".join("%s,%s" % tuple(pair) for pair in points)
        tag = "polygon"
        atts = other_attributes.copy()
        atts["points"] = points_fmt
        self.add_element(name, tag, atts, style_dict, event_callback=event_callback)


class SVGCanvasWidget(widgets.DOMWidget, SVGHelperMixin):
    """
    Jupyter notebook widget which presents an SVG canvas.
    """

    # The javascript view name.
    _view_name = Unicode('SVGCanvasView').tag(sync=True)
    _view_module = Unicode("SVGCanvas").tag(sync=True)
    
    # SVG viewBox
    viewBox = Unicode("0 0 500 500", sync=True)
    view_minx = 0
    view_miny = 0
    view_width = 500
    view_height = 500

    # The bounding box set in response to "fit" command.
    boundingBox = Dict({}, sync=True)
    
    # Canvas width
    svg_width = Float(500, sync=True)
    
    # Canvas height
    svg_height = Float(500, sync=True)
    
    # SVG styling, JSON encoded dictionary
    svg_style = Unicode("{}", sync=True)
    
    # JSON encoded sequence of dictionaries describing actions.
    #commands = Unicode("[]", sync=True)
    
    # White separated names of event to watch
    watch_event = Unicode("", sync=True)
    
    # White separated names of event to unwatch
    unwatch_event = Unicode("", sync=True)
    
    # Event captured (sent from js, jason encoded).
    #event = Unicode("{}", sync=True)

    # Set by JS after render is complete
    rendered = Bool(False, sync=True)
    
    # Buffered commands, list of dictionary (or None)
    buffered_commands = None
    
    # use this style dictionary if not provided
    default_style = {}
    
    # Set True to enable localized event callbacks
    # If set False then event callbacks attached to descendent elements to
    # the SVG canvas will not fire -- only the global default callback will fire.
    local_events = True


    def __init__(self, *pargs, **kwargs):
        super(SVGCanvasWidget, self).__init__(*pargs, **kwargs)
        #self.on_trait_change(self.handle_event_change, "event")
        self.on_trait_change(self.send_commands, "rendered")
        self.on_msg(self.handle_custom_message)
        self.name_counter = 0
        self.verbose = False
        self.default_event_callback = None
        self.name_to_callback = {}
        self._last_message_data = None
        self._status = "initialized"
        self._exception = None
        self.last_svg_text = None
        self.svg_text_callback = None

    def handle_custom_message(self, widget, data, *etcetera):
        self._last_message_data = data
        self._status = "got custom message"
        indicator = data["indicator"]
        payload = data["payload"]
        if indicator == "event":
            self._status = "handling event"
            self.handle_event(payload)
        elif indicator == "SVG_text":
            self.status = "handling SVG text"
            self.handle_svg(payload)
        else:
            self._status = "unknown message indicator " + repr(indicator)

    def handle_svg(self, svg_text):
        self.last_svg_text = svg_text
        callback = self.svg_text_callback
        if callback is not None:
            callback(svg_text)
        # only use the callback once
        self.svg_text_callback = None
        
    def set_event_callback(self, callback):
        "Set the default callback to use if not handled by local callback."
        self.default_event_callback = callback
        
    def handle_event(self, info):
        "Dispatch an event sent from javascript to a registered callback."
        try:
            if info:
                #info = json.loads(new)
                name = info.get("name")
                if self.verbose:
                    self._status = "event from " + repr(name)
                callback = self.default_event_callback
                if self.local_events:
                    callback = self.name_to_callback.get(name, callback)
                if callback is not None:
                    self._status = "event callback " + repr(callback)
                    callback(info)
        except Exception as e:
            self._status = "exception in event handling: " + repr(e)
            self._exception = e
    
    def add_command(self, dictionary):
        "Append a command to the command buffer."
        if self.buffered_commands is None:
            self.buffered_commands = []
        self.buffered_commands.append(dictionary)

    command_counter = 0
        
    def send_commands(self):
        "Send all commands in the command buffer to the JS interpreter."
        if not self.rendered:
            if self.verbose:
                print ("not sending commands because render has not happened yet.")
            return
        #self.await_pending_commands()
        # Update the counter so every command sequence is distinct
        self.command_counter += 1
        bc = self.buffered_commands
        if bc:
            command_pair = [self.command_counter, bc]
            self.command_pending = True
            #self.commands = json.dumps(command_pair)
            self.send(command_pair)
        self.buffered_commands = None
        
    def add_element(self, name, tagname, attribute_dict, style_dict=None, text=None, event_callback=None):
        "Add an 'add_element' to the command buffer."
        if name is None:
            # Invent a name if None given.
            self.name_counter += 1
            name = str(tagname) + "_" + str(self.name_counter)
        if style_dict is None:
            style_dict = self.default_style
        command = {
            "command": "add_element",
            "name": name,
            "tag": tagname,
            "atts": attribute_dict,
            "style": style_dict,
            "text": text,
        }
        self.add_command(command)
        if event_callback:
            self.name_to_callback[name] = event_callback
        
    def change_element(self, name, attribute_dict, style_dict=None, text=None):
        "Add a 'change_element' to the command buffer for a named object."
        if style_dict is None:
            style_dict = self.default_style
        command = {
            "command": "change_element",
            "name": name,
            "atts": attribute_dict,
            "style": style_dict,
            "text": text,
        }
        self.add_command(command)
        
    def empty(self):
        "Add a command to empty the canvas to the command buffer."
        command = {"command": "empty"}
        self.add_command(command)
        self.name_to_callback = {}
        
    def delete_names(self, names):
        "Add a command to remove named objects to the command buffer."
        command = {"command": "delete", "names": names}
        self.add_command(command)
        n2c = self.name_to_callback
        for name in names:
            if name in n2c:
                del n2c[name]

    def fit(self, changeView=True):
        "add a 'fit' command to the command buffer (fit to bounding box)"
        command = {"command": "fit", "changeView": changeView}
        self.add_command(command)

    def get_SVG_text(self, callback=None):
        "get the SVG text asynchronously"
        self.svg_text_callback = callback
        command = {"command": "get_SVG_text"}
        self.add_command(command)
        self.send_commands()

    def save_as_SVG_file(self, path="Diagram.svg"):
        print ("Saving as " + repr(path) + " asynchronously.") 
        start = u'<svg preserveAspectRatio="none" viewBox="%s" width="%s" height="%s">' %(
            self.viewBox, self.svg_width, self.svg_height
        )
        f = open(path, "w")
        def callback(text):
            L = [start, text, u"</svg>"]
            for x in L:
                f.write(x)
                f.write(u"\n")
            f.close()
        self.get_SVG_text(callback)

    def get_style(self):
        "Get the current SVG style."
        return json.loads(self.svg_style)
