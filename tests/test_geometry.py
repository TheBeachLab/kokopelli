import numpy as np

from koko.c.interval import Interval
from koko.c.vec3f import Vec3f
from koko.fab.path import Path
from koko.fab.tree import MathTree
from koko.lib.shapes2d import circle


def test_native_tree_parses_and_prints():
    shape = circle(0, 0, 1)

    assert shape.node_count == 8
    assert str(shape) == "(sqrt((pow(X, 2)+pow(Y, 2)))-1)"
    assert shape.bounds == [-1, 1, -1, 1, None, None]


def test_python3_true_division_operators():
    tree = MathTree(6) / 2
    interval = Interval(4, 8) / 2
    vector = Vec3f(2, 4, 6) / 2

    assert tree.math == "/f6f2"
    assert (interval.lower, interval.upper) == (2, 4)
    assert tuple(vector) == (1, 2, 3)


def test_path_sort_works_with_current_numpy():
    outer = Path(np.array([[0, 0, 0], [10, 10, 0]], dtype=float))
    inner = Path(np.array([[2, 2, 0], [3, 3, 0]], dtype=float))

    assert Path.sort([outer, inner]) == [inner, outer]
