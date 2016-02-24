"""
Higher level conveniences for drawing SVG 2d figures.
"""

import numpy as np
import math
from jp_svg_canvas import canvas
from IPython.display import display

class Cartesian(object):

    # extrema in world coordinates
    min_x = min_y = max_x = max_y = None

    # value defaults
    color = "black"
    event_cb = None
    rotate = None
    style_dict = {}
    other_attributes = {}

    def __init__(self, target_canvas, scaling=1.0, x_scaling=None, y_scaling=None,
        canvas.load_javascipr_support()
        x_offset=0.0, y_offset=0.0):
        self.x_scaling = self.y_scaling = scaling
        if x_scaling is not None:
            self.x_scaling = x_scaling
        if y_scaling is not None:
            self.y_scaling = y_scaling
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.target = target_canvas

    def show(self):
        display(self.target)

    def embed(self):
        self.target.embed()

    def section(self, scaling=1.0, x_scaling=None, y_scaling=None,
        x_offset=0.0, y_offset=0.0):
        """
        A reference to a section of the canvas with separate relative
        origin and scaling.
        """
        not finished

    def override_defaults(self, color, event_cb, style_dict, other_attributes):
        if color is None:
            color = self.color
        if event_cb is None:
            event_cb = self.event_cb
        if style_dict is None:
            style_dict = self.style_dict.copy()
        if other_attributes is None:
            other_attributes = self.other_attributes.copy()
        return (color, event_cb, style_dict, other_attributes)

    def update_extrema(self, x, y):
        "Update extrema in world coordinates (before projection)."
        for (combine, att, value) in [(min, "min_x", x), (max, "max_x", x), (min, "min_y", y), (max, "max_y", y)]:
            extrema = getattr(self, att)
            if extrema is None:
                extrema = value
            else:
                extrema = combine(extrema, value)
            setattr(self, att, extrema)

    def texts(self, names, xs, ys, texts, fills=None, event_cbs=None, 
        rotate=None, style_dicts=None, other_attributes=None, update=False):
        (fills, event_cbs, style_dicts, other_attributes) = self.override_defaults(
            fills, event_cbs, style_dicts, other_attributes)
        (names, xs, ys, texts, fills, event_cbs, style_dicts, other_attributes) = unify_shapes(
            names, xs, ys, texts, fills, event_cbs, style_dicts, other_attributes)
        if update:
            self.update_extrema(xs.max(), ys.max())
            self.update_extrema(xs.min(), ys.min())
        (xs, ys) = self.project(xs, ys)
        target = self.target
        for (i, name) in enumerate(names):
            sd = style_dicts[i].copy()
            oa = other_attributes[i].copy()
            x = xs[i]
            y = ys[i]
            if rotate:
                rotation = "rotate(%s %s %s)" % (rotate, x, y)
                oa["transform"] = rotation
            target.text(name, x, y, texts[i], fills[i], event_cbs[i], 
                sd, **oa)
        target.send_commands()

    text = texts # alias

    def sequence(self, names, xs, ys, colors=None, widths=None,
        event_cbs=None, style_dicts=None, other_attributes=None, update=True):
        (xs, ys) = unify_shapes(xs, ys)
        x1s = xs[:-1]
        y1s = ys[:-1]
        x2s = xs[1:]
        y2s = ys[1:]
        return self.lines(names, x1s, y1s, x2s, y2s, colors, widths,
            event_cbs, style_dicts, other_attributes, update)

    def lines(self, names, x1s, y1s, x2s, y2s, colors=None, widths=None,
        event_cbs=None, style_dicts=None, other_attributes=None, update=True):
        (colors, event_cbs, style_dicts, other_attributes) = self.override_defaults(
            colors, event_cbs, style_dicts, other_attributes)
        (names, x1s, y1s, x2s, y2s, colors, widths, event_cbs, style_dicts, other_attributes) = unify_shapes(
            names, x1s, y1s, x2s, y2s, colors, widths, event_cbs, style_dicts, other_attributes)
        if update:
            for (xs, ys) in ((x1s, y1s), (x2s, y2s)):
                self.update_extrema(xs.max(), ys.max())
                self.update_extrema(xs.min(), ys.min())
        (x1s, y1s) = self.project(x1s, y1s)
        (x2s, y2s) = self.project(x2s, y2s)
        target = self.target
        for (i, name) in enumerate(names):
            target.line(name, x1s[i], y1s[i], x2s[i], y2s[i], colors[i], widths[i],
                event_cbs[i], style_dicts[i], **other_attributes[i])
        target.send_commands()

    line = lines # alias

    def circles(self, names, cxs, cys, rs, fills=None, event_cbs=None, style_dicts=None,
              other_attributes=None, update=True):
        (fills, event_cbs, style_dicts, other_attributes) = self.override_defaults(
            fills, event_cbs, style_dicts, other_attributes)
        (names, cxs, cys, rs, fills, event_cbs, style_dicts, other_attributes) = unify_shapes(
            names, cxs, cys, rs, fills, event_cbs, style_dicts, other_attributes)
        if update:
            self.update_extrema(cxs.max(), cys.max())
            self.update_extrema(cxs.min(), cys.min())
        (cxs, cys) = self.project(cxs, cys)
        # XXXX use x scaling to convert the radii???
        (rs, _) = map(np.abs, self.scale(rs, 0))
        target = self.target
        for (i, name) in enumerate(names):
            target.circle(name, cxs[i], cys[i], rs[i], fills[i], event_cbs[i], style_dicts[i],
                **other_attributes[i])
        target.send_commands()

    circle = circles # alias

    def rects(self, names, xs, ys, widths, heights, fills=None, event_cbs=None, style_dicts=None,
            other_attributes=None, update=True):
        (fills, event_cbs, style_dicts, other_attributes) = self.override_defaults(
            fills, event_cbs, style_dicts, other_attributes)
        (names, xs_w, ys_w, widths_w, heights_w, fills, event_cbs, style_dicts, other_attributes) = unify_shapes(
            names, xs, ys, widths, heights, fills, event_cbs, style_dicts, other_attributes)
        (xs, ys) = self.project(xs_w, ys_w)
        (widths, heights) = map(np.abs, self.scale(widths_w, heights_w))
        if self.y_scaling < 0:
            # invert the height
            ys = ys - heights
        target = self.target
        for (i, name) in enumerate(names):
            if update:
                self.update_extrema(xs_w[i] + widths_w[i], ys_w[i] + heights_w[i])
                self.update_extrema(xs_w[i], ys_w[i])
            target.rect(name, xs[i], ys[i], widths[i], heights[i], fills[i], event_cbs[i], style_dicts[i],
                **other_attributes[i])
        target.send_commands()

    rect = rects # alias

    def project(self, x, y):
        "Convert world space x and y to canvas coordinates"
        (sx, sy) = self.scale(x, y)
        return (sx + self.x_offset, sy + self.y_offset)

    def scale(self, x, y):
        "Scale x and y values."
        # right now only scaling?
        return (x * self.x_scaling, y * self.y_scaling)

    def rscale(self, sx, sy):
        "Inverse x, y scaling."
        return (sx / self.x_scaling, sy / self.y_scaling)

    def fit(self):
        "fit the target to the drawn elements"
        self.target.fit()
        self.target.send_commands()

    # axis defaults
    tick_size = 5
    label_offset = 10
    label_fmt = "%3.2f"
    max_num_tick = 5
    text_options = {}
    line_options = {}

    def axis_defaults(self, tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color):
        if tick_size is None:
            tick_size = self.tick_size
        if label_offset is None:
            label_offset = self.label_offset
        if label_fmt is None:
            label_fmt = self.label_fmt
        if max_num_tick is None:
            max_num_tick = self.max_num_tick
        if text_options is None:
            text_options = self.text_options.copy()
        if line_options is None:
            line_options = self.line_options.copy()
        if color is None:
            color = self.color
        return (tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color)

    def right_axis(self, x, minimum, maximum, 
        tick_size=None, label_offset=None, label_fmt=None, max_num_tick=None, color=None,
        text_options=None, line_options=None):
        return self.left_axis(x, minimum, maximum, 
            tick_size, label_offset, label_fmt, max_num_tick, color,
            text_options, line_options, label_align=+1)

    def left_axis(self, x, minimum, maximum, 
        tick_size=None, label_offset=None, label_fmt=None, max_num_tick=None, color=None,
        text_options=None, line_options=None, label_align=-1):
        (tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color) = self.axis_defaults(
            tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color)
        if label_align < 0:
            text_options["text-anchor"] = "end"
        else:
            text_options["text-anchor"] = "start"
        ticks = tick(minimum, maximum, max_num_tick)
        (tick_shift, _) = self.rscale(tick_size, 0)
        self.lines(None, x, ticks, x + label_align * tick_shift, ticks, color, other_attributes=line_options)
        self.lines(None, [x], minimum, x, maximum, color, other_attributes=line_options)
        if label_fmt:
            (label_shift, _) = self.rscale(label_offset, 0)
            labels = [label_fmt % t for t in ticks]
            self.texts(None, x + label_align * label_shift, ticks, labels, color, other_attributes=text_options)
        return ticks

    def top_axis(self, y, minimum, maximum, 
        tick_size=None, label_offset=None, label_fmt=None, max_num_tick=None, color=None,
        text_options=None, line_options=None):
        return self.bottom_axis(y, minimum, maximum, 
            tick_size, label_offset, label_fmt, max_num_tick, color,
            text_options, line_options, label_align=-1)

    def bottom_axis(self, y, minimum, maximum,
        tick_size=None, label_offset=None, label_fmt=None, max_num_tick=None, color=None,
        text_options=None, line_options=None, label_align=+1):
        (tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color) = self.axis_defaults(
            tick_size, label_offset, label_fmt, max_num_tick, text_options, line_options, color)
        if label_align < 0:
            text_options["text-anchor"] = "end"
        else:
            text_options["text-anchor"] = "start"
        ticks = tick(minimum, maximum, max_num_tick)
        (_, tick_shift) = self.rscale(0, tick_size)
        self.lines(None, ticks, y, ticks, y + label_align * tick_shift, color, other_attributes=line_options)
        self.lines(None, minimum, [y], maximum, y, color, other_attributes=line_options)
        if label_fmt:
            (_, label_shift) = self.rscale(0, label_offset)
            labels = [label_fmt % t for t in ticks]
            self.texts(None, ticks, y + label_align * label_shift, labels, color, rotate=90, other_attributes=text_options)
        return ticks

    def axes(self, x0=0, y0=0):
        "Default axes crossing at x0, y0 using current extrema"
        if self.min_x is not None and self.max_x is not None:
            self.bottom_axis(y0, self.min_x, self.max_x)
        if self.min_y is not None and self.max_y is not None:
            self.left_axis(x0, self.min_y, self.max_y)

    def empty(self):
        self.target.empty()
        self.target.send_commands()

    def default_extrema(self, min_x, min_y, max_x, max_y):
        if min_x is None:
            min_x = self.min_x
        if min_y is None:
            min_y = self.min_y
        if max_x is None:
            max_x = self.max_x
        if max_y is None:
            max_y = self.max_y
        return (min_x, min_y, max_x, max_y)

    def plot_y(self, f_y, min_x=None, max_x=None, dx=None, npoints=200, min_y=None, max_y=None):
        """
        Plot y = f_y(x) between min_x and max_x, skipping exceptions.
        """
        xs = []
        ys = []
        (min_x, min_y, max_x, max_y) = self.default_extrema(min_x, min_y, max_x, max_y)
        if dx is None:
            dx = (max_x - min_x) * 1.0 / npoints
        def emit():
            if xs:
                self.sequence(None, xs, ys)
            xs[:] = []
            ys[:] = []
        x = min_x
        while x < max_x:
            try:
                y = f_y(x)
            except Exception:
                emit()
            else:
                if y > min_y and y < max_y:
                    xs.append(x)
                    ys.append(y)
                else:
                    emit()
            x += dx
        emit()

    def plot_x(self, f_x, min_y=None, max_y=None, dy=None, npoints=200, min_x=None, max_x=None):
        """
        Plot y = f_y(x) between min_x and max_x, skipping exceptions.
        """
        # XXX someday maybe refactor for common functionality
        xs = []
        ys = []
        (min_x, min_y, max_x, max_y) = self.default_extrema(min_x, min_y, max_x, max_y)
        if dy is None:
            dy = (max_y - min_y) * 1.0 / npoints
        def emit():
            if xs:
                self.sequence(None, xs, ys)
            xs[:] = []
            ys[:] = []
        y = min_y
        while y < max_y:
            try:
                x = f_x(y)
            except Exception:
                emit()
            else:
                if x > min_x and x < max_x:
                    xs.append(x)
                    ys.append(y)
                else:
                    emit()
            y += dy
        emit()

    def plot_t(self, f_xy, t0, dt, npoints):
        """
        Parametric plot (x,y) = f_xy(t) for t from t0 incrementing dt npoints times.
        """
        xs = []
        ys = []
        def emit():
            if xs:
                self.sequence(None, xs, ys)
            xs[:] = []
            ys[:] = []
        t = t0
        for i in xrange(npoints):
            try:
                (x, y) = f_xy(t)
            except Exception:
                emit()
            else:
                xs.append(x)
                ys.append(y)
            t += dt
        emit()


def doodle(xmin, ymin, xmax, ymax, html_width=500, html_height=None, margin=50, svg=None):
    """
    A utility to get a simple widget target for drawing.
    """
    inner_width = html_width - 2 * margin
    scaling = None
    x_scaling = inner_width * 1.0 / (xmax - xmin)
    x_offset = margin - x_scaling * xmin
    if html_height is None:
        y_scaling = - x_scaling
    else:
        inner_height = html_height - 2 * margin
        y_scaling = inner_height * 1.0 / (ymin - ymax)
    y_offset = margin - y_scaling * ymax
    height = 2 * margin + abs((ymax - ymin) * y_scaling)
    width = 2 * margin + abs((xmax - xmin) * x_scaling)
    viewBox = "%s %s %s %s" % (0, 0, width, height)
    if svg is None:
        svg = canvas.SVGCanvasWidget()
    svg.width = width
    svg.height = height
    svg.viewBox = viewBox
    C = Cartesian(svg, scaling, x_scaling, y_scaling, x_offset, y_offset)
    (C.min_x, C.min_y, C.max_x, C.max_y) = (xmin, ymin, xmax, ymax)
    return C

def sdoodle(xmin, ymin, xmax, ymax, html_width=500, margin=50):
    """
    A static doodle (cannot be used as a widget but will show in nbviewer)
    """
    from jp_svg_canvas import static_svg
    svg = static_svg.StaticCanvas()
    return doodle(xmin, ymin, xmax, ymax, html_width, margin, svg=svg)

# utilities
def unify_shapes(*args):
    arrays = [np.array(x, np.object) for x in args]
    max_shape = ()
    for a in arrays:
        s = a.shape
        if len(s) > len(max_shape):
            max_shape = s
    # maks sure we don't have only zero-d arrays
    if len(max_shape) == 0:
        max_shape = (1,)
    result = []
    for a in arrays:
        z = np.zeros(max_shape, dtype=object)
        z[:] = a
        result.append(z)
    return result

def tick(x, y, maxlen=10):
    "Compute axis tick locations."
    assert x < y
    assert maxlen > 1
    d = y - x
    logd = math.log10(d)
    ticklog = math.ceil(logd - 1)
    tickwidth = 10 ** ticklog
    if tickwidth * 4 > d:
        tickwidth = tickwidth / 5
    elif tickwidth * 5 > d:
        tickwidth = tickwidth / 4
    ticknumber = int(d/tickwidth) + 2
    tickmin = int(x/tickwidth) * tickwidth
    result = [tickmin + i * tickwidth for i in range(ticknumber)]
    if result[0] < x:
        del result[0]
    if result[-1] > y:
        del result[-1]
    lresult = len(result)
    if lresult > maxlen:
        skip = int(lresult/maxlen) + 1
        start = int(skip/2)
        result = [result[i] for i in range(start, lresult, skip)]
    return result
