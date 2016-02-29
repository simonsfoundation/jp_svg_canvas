"""
Interactive widget for the house location problem.
"""

import traitlets

from jp_svg_canvas import cartesian_svg

import numpy as np
import sympy as s

(x, y) = s.symbols("x y")

def pp(x,y):
    return np.array([x,y])

def dist2(x0,y0,x1,y1):
    "distance between (x0,y0) and (x1,y1) squared"
    return (x0-x1)**2 + (y0-y1)**2

def distance(x0,y0,x1,y1):
    "distance between (x0,y0) and (x1,y1)"
    return np.sqrt(dist2(x0,y0,x1,y1))

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
        super(Locations, self).__init__(*pargs, **kwargs)
        self.diagram = D = cartesian_svg.doodle(-3, -6, 6, 2, html_width=700)
        self.moving = None
        D.show()
        D.axes(-2.5, -5.5)
        # rotate text -55 degrees
        D.rotate = -55
        D.enable_events("click mousemove", self.event_callback)
        self.redraw()
    def redraw(self):
        self.draw_dots()
        self.draw_KB()
        self.draw_JN()
        self.draw_locations()
        self.diagram.flush()
    def event_callback(self, info):
        #import pprint
        #pprint.pprint(info)
        name = info.get("group_name", "")
        ty = info.get("type")
        moving = self.moving
        if (ty == "click"):
            if moving:
                self.moving = None
                self.redraw()
            else:
                if name in "KBJN":
                    self.moving = name
        if self.moving:
            name = self.moving
            (px, py) = info["point"]
            setattr(self, name, pp(px, py))
            self.redraw()
    def draw_locations(self):
        D = self.diagram
        locations = s.solve([self.KB_Shape, self.JN_Shape], x, y)
        D.delete(["location"])
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
        self.KB_Shape = self.draw_distance_constraint(self.K, self.B, self.a, "KB")
    def draw_JN(self):
        self.JN_Shape = self.draw_distance_constraint(self.J, self.N, self.b, "JN")
    def draw_distance_constraint(self, p1, p2, ratio, name):
        (x1, y1) = p1
        (x2, y2) = p2
        sd1 = dist2(x, y, x1, y1)
        sd2 = dist2(x, y, x2, y2)
        eqn = s.Eq(sd1, sd2 * ratio**2)
        solutions = s.solve(eqn, y)
        D = self.diagram
        D.delete([name])
        for solution in solutions:
            yfunction = s.lambdify(x, solution)
            D.color = "green"
            D.plot_y(yfunction, name=name)
        return eqn
    def draw_dots(self):
        D = self.diagram
        for (pos, name, abbr) in [(self.K, "Kim", "K"), (self.B, "Bob", "B"), (self.J, "Jack", "J"), (self.N, "Janet", "N")]:
            D.color = "red"
            D.delete([abbr, name])
            D.circle(abbr, pos[0], pos[1], 0.1)
            D.text(name, pos[0] + 0.1, pos[1] - 0.1, name)
