"""
Interactive widget for the house location problem.

This is not polished code.  It is a quick proof of concept for demonstration purposes.
"""

import traitlets
from IPython.display import display
import ipywidgets as widgets
from jp_svg_canvas import cartesian_svg
import threading
import time
import jp_svg_canvas.transforms2d as tr

import numpy as np
import sympy as s
import math

#ip = get_ipython()

(x, y) = s.symbols("x y")

def pp(x,y):
    return np.array([x,y])

def dist2(x0,y0,x1,y1):
    "distance between (x0,y0) and (x1,y1) squared"
    return (x0-x1)**2 + (y0-y1)**2

def distance(x0,y0,x1,y1):
    "distance between (x0,y0) and (x1,y1)"
    return np.sqrt(dist2(x0,y0,x1,y1))

(x_c, y_c, r) = s.symbols("x_c y_c r")

def circle_stats(equation):
    """
    Assuming equation describes a circle, find center and radius.
    """
    circle = s.Eq((x - x_c)**2 + (y - y_c) ** 2 - r**2, 0)
    (a1, b1, c1, d1) = circle_coefficients(circle)
    (a2, b2, c2, d2) = circle_coefficients(equation)
    ae = s.Eq(a1, a2)
    be = s.Eq(b1, b2)
    ce = s.Eq(c1, c2)
    de = s.Eq(d1, d2)
    for soln in s.solve([ae, be, ce, de], x_c, y_c, r):
        (xc, yc, rr) = map(float, soln)
        if rr >= 0:
            return (xc, yc, rr)
    raise ValueError, "no valid solution found."

def circle_stats1(x_1, y_1, x_2, y_2, ratio):
    r2 = ratio**2
    A = float(-r2 + 1)
    B = 2*r2*x_2 - 2*x_1
    C = 2*r2*y_2 - 2*y_1
    D = -r2 * x_2**2 - r2 * y_2**2 + x_1**2 + y_1**2
    #print "ABCD", A, B, C, D
    b = B/A
    c = C/A
    d = D/A
    #print "bcd", b, c, d
    x_c = -b/2.0
    y_c = -c/2.0
    radius = float(np.sqrt(b**2 + c**2 - 4*d))/2.0
    result = (x_c, y_c, radius)
    #print "result", result
    return result

def circle_coefficients(equation):
    ezero = equation.lhs - equation.rhs
    x_poly = s.Poly(ezero, x)
    y_poly = s.Poly(ezero, y)
    x_coeffs = x_poly.all_coeffs()
    y_coeffs = y_poly.all_coeffs()
    (cx2, cx1, cx0) = x_coeffs
    (cy2, cy1, cy0) = y_coeffs
    # remove the xs and ys from the constant terms
    cx0y = cx0 - y * cy1
    cy0x = cy0 - x * cx1
    lc = float(cx2)
    assert lc == float(cy2)
    return (cx1/lc, cx0y/lc, cy1/lc, cy0x/lc)

class Locations(traitlets.HasTraits):

    a = traitlets.Any(3)

    b = traitlets.Any(4)

    K = traitlets.Any(pp(4,0))

    B = traitlets.Any(pp(0,0))

    J = traitlets.Any(pp(-2,-4))

    N = traitlets.Any(pp(-2, -1))

    KB_Shape = traitlets.Any()

    JN_Shape = traitlets.Any()

    intersection_points = traitlets.Any([])

    def __init__(self, *pargs, **kwargs):
        self.drawing = True
        self.last_draw_time = 0
        self.draw_lock = threading.Lock()
        super(Locations, self).__init__(*pargs, **kwargs)
        self.diagram = D = cartesian_svg.doodle(-3, -6, 6, 2, html_width=700)
        self.moving = None
        a_slider = widgets.FloatSlider(value=3.0, min=0.2, max=10.0, step=0.2,
            width="150px", description="Kim/Bob")
        b_slider = widgets.FloatSlider(value=4.0, min=0.2, max=10.0, step=0.2,
            width="150px", description="Jack/Janet")
        traitlets.directional_link((a_slider, "value"), (self, "a"))
        traitlets.directional_link((b_slider, "value"), (self, "b"))
        self.on_trait_change(self.redraw, "a")
        self.on_trait_change(self.redraw, "b")
        assembly = widgets.VBox(children = [a_slider, b_slider, D.target])
        display(assembly)
        #D.show()
        D.enable_events("click mousemove", self.event_callback)
        self.redraw()
    def redraw(self):
        if time.time() - self.last_draw_time < 0.2:
            return
        #if not self.draw_lock.acquire(False):
        #    # some other thread is drawing... give up.
        #    print "not drawing because lock is taken"
        #    return
        #print "draw lock aquired"
        try:
            self.last_draw_time = time.time()
            D = self.diagram
            D.empty()
            #self.draw_dots()
            D.color = "black"
            D.rotate = None
            D.axes(-2.5, -5.5)
            # rotate text -55 degrees
            D.rotate = -55
            self.draw_KB()
            self.draw_JN()
            self.draw_locations()
            self.draw_dots()
            self.diagram.flush()
            self.drawing = False
            #ip = get_ipython()
            #ip.kernel.do_one_iteration()
            # sleep to allow browser to catch up
            time.sleep(0.1)
        finally:
            #self.draw_lock.release()
            pass
            #print "draw_lock release"
    def redraw_in_thread(self):
        # disable threading for now
        return self.redraw()
        if self.drawing:
            # don't keep drawing
            return
        self.drawing = True
        t = threading.Thread(target=self.redraw)
        t.start()
    def event_callback(self, info):
        #import pprint
        #pprint.pprint(info)
        name = info.get("group_name", "")
        ty = info.get("type")
        if self.moving:
            name = self.moving
            (px, py) = info["point"]
            setattr(self, name, pp(px, py))
            self.redraw_in_thread()
        moving = self.moving
        if (ty == "click"):
            #print "click"
            #import pprint
            #pprint.pprint(info)
            if moving:
                self.moving = None
                self.redraw_in_thread()
            else:
                if name in "KBJN":
                    self.moving = name
    def locations1(self):
        "brute force method to finding circle intersections using sympy."
        return s.solve([self.KB_Shape, self.JN_Shape], x, y)
    def locations2(self):
        "calculate location positions directly"
        K = self.K
        B = self.B
        J = self.J
        N = self.N
        (P1x, P1y, r1) = circle_stats1(K[0], K[1], B[0], B[1], self.a)
        (P2x, P2y, r2) = circle_stats1(J[0], J[1], N[0], N[1], self.b)
        r = r1/r2
        xp = distance(P1x, P1y, P2x, P2y)/r2
        try:
            cost = (-r*r + xp*xp + 1)/(2*xp)
            sint = math.sqrt(1 - cost*cost)
        except ValueError:
            return []
        trans = tr.translate(P2x, P2y)
        rot = tr.direction_rotate(P1x-P2x, P1y-P2y)
        scl = tr.scale(r2)
        denormalize = tr.compose(scl, tr.compose(rot, trans))
        return  [tr.tapply(denormalize, cost, sint), tr.tapply(denormalize, cost, -sint)]
    def draw_locations(self):
        D = self.diagram
        locations = self.locations2()
        #D.delete(["location"])
        for location in locations:
            try:
                (lx, ly) = map(float, location)
            except TypeError:
                pass
            else:
                p = pp(lx, ly)
                D.color = "blue"
                D.circle("location", lx, ly, 0.1)
                for (p2, name) in [(self.K, "Kim"), (self.B, "Bob"), (self.J, "Jack"), (self.N, "Janet")]:
                    D.line("location", lx, ly, p2[0], p2[1])
    def draw_KB(self):
        #self.KB_Shape = self.draw_distance_constraint(self.K, self.B, self.a, "KB")
        self.KB_Shape = self.distance_disc(self.K, self.B, self.a, "KB")
    def draw_JN(self):
        #self.JN_Shape = self.draw_distance_constraint(self.J, self.N, self.b, "JN")
        self.JN_Shape = self.distance_disc(self.J, self.N, self.b, "JN")
    def distance_disc(self, p1, p2, ratio, name):
        eqn = self.distance_constraint(p1, p2, ratio)
        #(cx, cy, rr) = circle_stats(eqn)
        try:
            (cx, cy, rr) = circle_stats1(p1[0], p1[1], p2[0], p2[1], ratio)
        except Exception as e:
            print("exception from circle_stats1 " + repr(e))
            raise
        D = self.diagram
        #D.delete([name])
        D.color = "green"
        atts = {"fill-opacity": "0.4"}
        D.circle(name, cx, cy, rr, other_attributes=atts)
        return eqn
    def distance_constraint(self, p1, p2, ratio):
        (x1, y1) = p1
        (x2, y2) = p2
        sd1 = dist2(x, y, x1, y1)
        sd2 = dist2(x, y, x2, y2)
        return s.Eq(sd1, sd2 * ratio**2)
    def draw_distance_constraint(self, p1, p2, ratio, name):
        eqn = self.distance_constraint(p1, p2, ratio)
        solutions = s.solve(eqn, y)
        D = self.diagram
        #D.delete([name])
        for solution in solutions:
            yfunction = s.lambdify(x, solution)
            D.color = "green"
            D.plot_y(yfunction, name=name, npoints=40)
        return eqn
    def draw_dots(self):
        D = self.diagram
        for (pos, name, abbr) in [(self.K, "Kim", "K"), (self.B, "Bob", "B"), (self.J, "Jack", "J"), (self.N, "Janet", "N")]:
            D.color = "red"
            #D.delete([abbr, name])
            D.circle(abbr, pos[0], pos[1], 0.1)
            D.text(name, pos[0] + 0.1, pos[1] - 0.1, name)
