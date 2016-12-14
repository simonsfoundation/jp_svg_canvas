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

    def __init__(self, viewBox, filename="diagram.png", format="image/png", dimension=800):
        """
        Fake SVG canvas which writes to an HTML5 canvas.
        This object is "write once" and does not support updates or interactions.
        The implementation is primarily intended to support image conversion
        for visualizations and static embedding of diagrams in IPython notebooks.

        Parameters
        ----------

        viewBox: str
            The SVG viewBox parameter to emulate.

        filename: str
            The filename to use for image download link.

        format: str
            The MIME type for image conversion.

        dimension: int 
            The size of the largest dimension for the image.
        """
        self.dimension = dimension
        self.viewBox = viewBox
        self.canvas_commands = []
        self.font = "Arial"  # default
        self.font_size = 10
        self.font_weight = "normal"
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
        if type(rhs) is unicode:
            rhs = str(rhs)
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
        style_dict = style_dict.copy()
        style_dict.update(other_attributes)
        f = self.font = style_dict.get("font", self.font)
        w = self.font_weight = style_dict.get("font-weight", self.font_weight)
        s = self.font_size = style_dict.get("font-size", self.font_size)
        self._assign("ctx.font", "%s %spx %s" % (w, s, f))
        self._assign("ctx.fillStyle", fill)
        ta = style_dict.get("text-anchor", "start")
        if ta == "middle":
            ta = "center"
        self._assign("ctx.textAlign", ta)
        self._add("ctx.fillText", text, x, y)
        stroke = style_dict.get("stroke")
        stroke_width = style_dict.get("stroke-width")
        if stroke and stroke_width:
            self._assign("ctx.lineWidth", stroke_width)
            self._assign("ctx.strokeStyle", stroke)
            self._add("ctx.strokeText", text, x, y)

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

    def embedding(self, preview=True):
        c = EMBEDDING_COUNT[0] = EMBEDDING_COUNT[0] + 1
        identifier = "jp_svg_canvas_fake_svg_" + str(c)
        [x0, y0, width, height] = map(float, self.viewBox.split())
        dimension = self.dimension
        minside = min(width, height)
        scale = dimension * 1.0/minside
        swidth = scale * width
        sheight = scale * height
        scaling = self._call("ctx.scale", scale, scale)
        translation = self._call("ctx.translate", -x0, -y0)
        commands = "\n    ".join([scaling, translation] + self.canvas_commands)
        visible = "true"
        if not preview:
            visible = "false"
        return EMBED_TEMPLATE.format(
            identifier=identifier, 
            width=swidth, 
            height=sheight, 
            commands=commands,
            format=self.format,
            filename=self.filename,
            visible=visible)

    def embed(self, preview=True):
        display(HTML(self.embedding(preview=preview)))

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
    var visible = {visible};
    var showhide = function () {{
        if (visible) {{
            $(c).show();
        }} else {{
            $(c).hide();
        }}
    }};
    var toggle_visibility = function() {{
        visible = !visible;
        showhide();
    }};
    showhide();
    // format the canvas
    {commands}
    // append the download link
    var data_url = c.toDataURL("{format}");
    var link = document.createElement("a");
    link.download = "{filename}";
    link.href = data_url;
    $(link).html("Download as {format}: {filename}");
    $(c).before(link);
    $(c).before("<br/>");
    $(c).before("<em>Download link may fail for large and complex images. If so capture preview.&nbsp;</em>");
    var vlink = $("<button>show/hide {filename} preview</button>").click(toggle_visibility);
    $(c).before(vlink);
    $(c).before("<br/>");
    link.scrollIntoView();
}})();
</script>
"""