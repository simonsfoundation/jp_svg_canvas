"""
A substitute for jp_svg_canvas.canvas.SVGCanvasWidget
which allows for write-once non-interactive embedding
of an SVG canvas representation of SVGCanvasWidget.
This is intended to allow embeddings that will be visible
under nbviewer which supports all non-interactive features
of SVGCanvasWidget.
"""

from IPython.display import display, HTML
from jp_svg_canvas import canvas
import json

COUNTER = [0]

# XXX not sure styles are handled consistently

class StaticCanvas(canvas.SVGHelperMixin):

    def __init__(self, viewBox="0 0 500 500", *pargs, **kwargs):
        super(StaticCanvas, self).__init__(*pargs, **kwargs)
        self.viewBox = viewBox
        self.command_list = []

    def set_event_callback(self, callback):
        # doesn't maks sense: ignore???
        pass

    def send_commands(self):
        pass

    def add_element(self, name, tagname, attribute_dict, style_dict=None, text=None, event_callback=None):
        return self.add_js_command("add_element", [name, tagname, attribute_dict, style_dict, text])

    def change_element(self, name, attribute_dict, style_dict=None, text=None):
        return self.add_js_command("change_element", [name, attribute_dict, style_dict, text])

    def empty(self):
        return self.add_js_command("empty", [])

    def fit(self):
        return self.add_js_command("fit", [])

    def delete_names(self, names):
        return self.add_js_command("delete_names", [names])

    def add_js_command(self, function_name, args):
        args_json = [json.dumps(x) for x in args]
        arg_string = ", ".join(args_json)
        cmd = "%s(%s)" % (function_name, arg_string)
        self.command_list.append(cmd)

    def new_div_name(self):
        COUNTER[0] += 1
        return "jp_svb_canvas_static_" + str(COUNTER[0])

    def embedding(self):
        identifier = self.new_div_name()
        commands_string = ";\n    ".join(self.command_list)
        return JS_TEMPLATE.format(
            viewBox=self.viewBox,
            identifier=identifier,
            commands=commands_string,
            )

    def embed(self):
        display(HTML(self.embedding()))

JS_TEMPLATE = """
<div id="{identifier}"/>

<script>
(function () {{
    var $div = $("#{identifier}");
    var svg_elt = function(kind) {{
            return document.createElementNS('http://www.w3.org/2000/svg', kind);
        }};
    var svg = svg_elt("svg");
    var $svg = $(svg);
    $div.append(svg);
    $div.named_elements = {{}};
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("viewBox", "{viewBox}");
    var add_element = function (name, tagname, attribute_dict, style_dict, text) {{
        var element = svg_elt(tagname);
        var $element = $(element);
        update_element($element, attribute_dict, style_dict, text);
        $div.named_elements[name] = $element;
        $svg.append($element);
    }};
    var change_element = function (name, attribute_dict, style_dict, text) {{
        var $element = $div.named_elements[name];
        if ($element) {{
            update_element($element, attribute_dict, style_dict, text);
        }}
    }};
    var update_element = function ($element, atts, style, text) {{
        var element = $element[0];
        if (atts) {{
            for (var att in atts) {{
                element.setAttribute(att, atts[att]);
            }}
        }}
        if (style) {{
            for (var styling in style) {{
                element.style[styling] = style[styling];
            }}
        }}
        if (text) {{
            $element.empty();
            var node = document.createTextNode(text);
            $element.append(node);
        }}
    }};
    var empty = function () {{
        $div.named_elements = {{}};
        $svg.empty();
    }};
    var delete_names = function (names) {{
        for (var i=0; i<names.length; i++) {{
            var name = names[i];
            var $element = $div.named_elements[name];
            if ($element) {{
                $element.remove();
                delete that.named_elements[name];
            }}
        }}
    }};
    var fit = function() {{
            // fit viewport to bounding box.
            var bbox = svg.getBBox();
            var vbox = "" + bbox.x + " " + bbox.y + " " + bbox.width + " " + bbox.height;
            svg.setAttribute("viewBox", vbox);
        }};
    {commands};
}})();
</script>
"""
