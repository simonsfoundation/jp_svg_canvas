
"""
Matrix math for supporting 2d affine transformations.
"""

import numpy as np
import math

#  https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform

def transform_matrix(a=1, c=0, e=0, b=0, d=1, f=0):
    return np.array([
        [a, c, e],
        [b, d, f],
        [0, 0, 1]
        ], np.float)

def translate(x, y):
    "Translate by scalars."
    return transform_matrix(e=x, f=y)

def vtranslate(v):
    "Translate by 2d vector."
    return translate(v[0], v[1])

def scale(x, y=None):
    if y is None:
        y = x
    return transform_matrix(a=x, d=y)

def direction_rotate(dx, dy):
    n = math.sqrt(dx*dx + dy*dy) * 1.0
    cosa = dx/n
    sina = dy/n
    return transform_matrix(a=cosa, b=sina, c=-sina, d=cosa)

def vrotate(v):
    return direction_rotate(v[0], v[1])

def rotate(radians):
    cosa = math.cos(radians)
    sina = math.sin(radians)
    return transform_matrix(a=cosa, b=sina, c=-sina, d=cosa)

def rotate_degrees(degrees):
    return rotate(degrees * math.pi/180.0)

def skewX(radians):
    return transform_matrix(c=math.tan(radians))

def skewY(radians):
    return transform_matrix(b=math.tan(radians))

def tapply(transform, x, y, epsilon=1e-10):
    v3 = np.array([x, y, 1], np.float)
    vout = transform.dot(v3)
    assert abs(1 - vout[2]) < epsilon
    return vout[:2]

def inverse(transform):
    return np.linalg.inv(transform)

def compose(t1, t2):
    "Return transform for: first do transform t1 then do transform t2."
    return t2.dot(t1)

def vapply(transform, v):
    return tapply(transform, v[0], v[1])

def vector2d(x, y):
    return np.array([x, y], np.float)

def test(verbose=False):
    def assert_very_close(v1, v2, epsilon=1e-10):
        assert np.linalg.norm(v1 - v2) < epsilon, repr((v1, v2)) + " not close enough."
    P = vector2d(1.3, 5.5)
    Pn = vapply(scale(-1, -1), P)
    assert_very_close(-P, Pn), repr(())
    P1 = vector2d(10.1, 3.3)
    Pt = vapply(vtranslate(P1), P)
    assert_very_close(Pt, P1 + P)
    t1 = compose(translate(-3, -2), compose(rotate_degrees(90), translate(3,2)))
    t2 = compose(rotate_degrees(90), translate(5, -1))
    assert_very_close(vapply(t1, P1), vapply(t2, P1))
    if verbose:
        print "tests pass"

if __name__ == "__main__":
    test(True)
