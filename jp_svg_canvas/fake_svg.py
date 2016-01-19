"""
A substitute for jp_svg_canvas.canvas.SVGCanvasWidget
which allows for write-once non-interactive embedding
of an HTML5 canvas representation of SVGCanvasWidget
draw operations, in order to support conversion of visualizations
to high quality image formats and for static embedding in
Notebooks.
"""

# XXXX At the moment this code provides features used
# by the other modules of the package and does not support
# an exhaustive set of features.

from IPython.display import display, HTML

EMBEDDING_COUNT = [0]

class FakeCanvasWidget(object):

    def __init__(self, viewBox, filename="diagram.png", format="image/png"):
        self.viewBox = viewBox
        self.canvas_commands = []
        self.font = "Arial"  # default
        self.font_size = 10
        self.filename = filename
        self.format = format

    def _add(self, command, *args):
        self.canvas_commands.append(self._call(command, *args))

    def _call(self, command, *args):
        arglist = ", ".join(repr(arg) for arg in args)
        fmt = "%s(%s);" % (command, arglist)
        return fmt

    def _assign(self, lhs, rhs):
        self.canvas_commands.append(self._assignment(lhs, rhs))

    def _assignment(self, lhs, rhs):
        return "%s = %s;" % (lhs, repr(rhs))

    def set_event_callback(self, *args):
        raise NotImplementedError

    def send_commands(self):
        # do nothing
        pass

    def change_element(self, *args, **kw):
        raise NotImplementedError
    def empty(self, *args, **kw):
        raise NotImplementedError
    def delete_names(self, *args, **kw):
        raise NotImplementedError
    def fit(self, *args, **kw):
        raise NotImplementedError
    def get_style(self, *args, **kw):
        raise NotImplementedError
    def set_style(self, *args, **kw):
        raise NotImplementedError
    def add_style(self, *args, **kw):
        raise NotImplementedError
    def set_view_box(self, *args, **kw):
        raise NotImplementedError
        
    def text(self, name, x, y, text, fill="black", event_cb= None, style_dict=None, **other_attributes):
        if not style_dict:
            style_dict = {}
        f = self.font = style_dict.get("font", self.font)
        s = self.font_size = style_dict.get("font_size", self.font_size)
        self._assign("ctx.font", "%spx %s" % (s, f))
        self._assign("ctx.fillStyle", fill)
        ta = style_dict.get("text-anchor", "start")
        if ta == "middle":
            ta = "center"
        self._assign("ctx.textAlign", ta)
        self._add("ctx.fillText", text, x, y)

    def line(self, name, x1, y1, x2, y2, color="black", width=1, 
             event_cb=None, style_dict=None, **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("ctx.beginPath")
        self._assign("ctx.strokeStyle", color)
        self._assign("ctx.lineWidth", width)
        self._add("ctx.moveTo", x1, y1)
        self._add("ctx.lineTo", x2, y2)
        self._add("ctx.stroke")

    def circle(self, name, cx, cy, r, fill="black", event_cb=None, style_dict=None,
              **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("ctx.beginPath")
        self._assign("ctx.fillStyle", fill)
        self._add("ctx.arc", cx, cy, r, 0, symb("Math.PI * 2"))
        self._add("ctx.fill")

    def rect(self, name, x, y, width, height, fill="black", event_cb=None, style_dict=None,
            **other_attributes):
        if not style_dict:
            style_dict = {}
        self._add("ctx.beginPath")
        self._assign("ctx.fillStyle", fill)
        self._add("ctx.rect", x, y, width, height)
        self._add("ctx.fill")

    def embedding(self):
        c = EMBEDDING_COUNT[0] = EMBEDDING_COUNT[0] + 1
        identifier = "jp_svg_canvas_fake_svg_" + str(c)
        [x0, y0, width, height] = map(int, self.viewBox.split())
        translation = self._call("ctx.translate", -x0, -y0)
        commands = "\n    ".join([translation] + self.canvas_commands)
        return EMBED_TEMPLATE.format(
            identifier=identifier, 
            width=width, 
            height=height, 
            commands=commands,
            format=self.format,
            filename=self.filename)

    def embed(self):
        display(HTML(self.embedding()))

class symb:
    "unquoted symbolic javascript fragment"

    def __init__(self, rep):
        self.rep = rep

    def __repr__(self):
        return self.rep

EMBED_TEMPLATE = """
<canvas id="{identifier}" width="{width}" height="{height}" style="border:1px solid #d3d3d3;">
Your browser does not support the HTML5 canvas tag.</canvas>
<script>
(function () {{
    var c = document.getElementById("{identifier}");
    var ctx = c.getContext("2d");
    // format the canvas
    {commands}
    // append the download link
    var data_url = c.toDataURL("{format}");
    var link = document.createElement("a");
    link.download = "{filename}";
    link.href = data_url;
    $(link).html("Download as {format}: {filename}");
    $(c).after(link);
    $(c).after("<br>")
}})();
</script>
"""