import functools

import math
import numpy as np

from citlab_python_util.geometry.polygon import calc_reg_line_stats
from citlab_python_util.geometry.rectangle import Rectangle


def check_intersection(line_1, line_2):
    """ Checks if two line segments `line1` and `line2` intersect. If they do so, the function returns the intersection
    point as [x,y] coordinate (special case for overlapping ["inf", "inf"]), otherwise `None`.

    :param line_1: list containing the x- and y-coordinates as [[x1,x2],[y1,y2]]
    :param line_2: list containing the x- and y-coordinates as [[x1,x2],[y1,y2]]
    :return: intersection point [x,y] if the line segments intersect, None otherwise
    """
    x_points1, y_points1 = line_1
    x_points2, y_points2 = line_2

    # consider vector form (us + s*vs = u + t*v)
    us = [x_points1[0], y_points1[0]]
    vs = [x_points1[1] - x_points1[0], y_points1[1] - y_points1[0]]

    u = [x_points2[0], y_points2[0]]
    v = [x_points2[1] - x_points2[0], y_points2[1] - y_points2[0]]

    A = np.array([vs, [-v[0], -v[1]]]).transpose()
    b = np.array([u[0] - us[0], u[1] - us[1]])

    rank_A = np.linalg.matrix_rank(A)
    rank_Ab = np.linalg.matrix_rank(np.c_[A, b])

    # no solution => parallel
    if rank_A != rank_Ab:
        return None

    # infinite solutions => one line is the multiple of the other
    if rank_A == rank_Ab == 1:
        # check if there is an overlap
        # us + s*vs = u
        s1 = (u[0] - us[0]) / vs[0]
        s2 = (u[1] - us[1]) / vs[1]
        if s1 == s2:
            if 0 < s1 < 1:
                return ["inf", "inf"]
            elif s1 == 0 or s1 == 1:
                return [us[0] + s1 * vs[0], us[1] + s1 * vs[1]]

        # us + s*vs = v
        s1 = (v[0] - us[0]) / vs[0]
        s2 = (v[1] - us[1]) / vs[1]
        if s1 == s2:
            if 0 < s1 < 1:
                return ["inf", "inf"]
            elif s1 == 0 or s1 == 1:
                return [us[0] + s1 * vs[0], us[1] + s1 * vs[1]]

        # otherwise there is no overlap and no intersection
        return None

    [s, t] = np.linalg.inv(A).dot(b)

    if not (0 <= s <= 1 and 0 <= t <= 1):
        return None

    return [us[0] + s * vs[0], us[1] + s * vs[1]]


def ortho_connect(rectangles):
    """
    2D Orthogonal Connect-The-Dots, see
    http://cs.smith.edu/~jorourke/Papers/OrthoConnect.pdf

    :param rectangles: list of Rectangle objects
    :return: list of surrounding polygons over rectangles
    """
    assert type(rectangles) == list
    assert all([isinstance(rect, Rectangle) for rect in rectangles])

    # Go over vertices of each rectangle and only keep shared vertices
    # if they are shared by an odd number of rectangles
    points = set()
    for rect in rectangles:
        for pt in rect.get_vertices():
            if pt in points:
                points.remove(pt)
            else:
                points.add(pt)
    points = list(points)

    def y_then_x(a, b):
        if a[1] < b[1] or (a[1] == b[1] and a[0] < b[0]):
            return -1
        elif a == b:
            return 0
        else:
            return 1

    # print(points)
    # print(sorted(points))
    # print(sorted(points, key=lambda x: x[1]))
    # print(sorted(sorted(points, key=lambda x: x[0]), key=lambda x: x[1]))
    # print(sorted(points, key=functools.cmp_to_key(y_then_x)))

    sort_x = sorted(points)
    sort_y = sorted(points, key=functools.cmp_to_key(y_then_x))

    edges_h = {}
    edges_v = {}

    # go over rows (same y-coordinate) and draw edges between vertices 2i and 2i+1
    i = 0
    while i < len(points):
        curr_y = sort_y[i][1]
        while i < len(points) and sort_y[i][1] == curr_y:
            edges_h[sort_y[i]] = sort_y[i + 1]
            edges_h[sort_y[i + 1]] = sort_y[i]
            i += 2

    # go over columns (same x-coordinate) and draw edges between vertices 2i and 2i+1
    i = 0
    while i < len(points):
        curr_x = sort_x[i][0]
        while i < len(points) and sort_x[i][0] == curr_x:
            edges_v[sort_x[i]] = sort_x[i + 1]
            edges_v[sort_x[i + 1]] = sort_x[i]
            i += 2

    # Get all the polygons
    p = []
    while edges_h:
        # We can start with any point
        polygon = [(edges_h.popitem()[0], 0)]
        while True:
            curr, e = polygon[-1]
            if e == 0:
                next_vertex = edges_v.pop(curr)
                polygon.append((next_vertex, 1))
            else:
                next_vertex = edges_h.pop(curr)
                polygon.append((next_vertex, 0))
            if polygon[-1] == polygon[0]:
                # Closed polygon
                polygon.pop()
                break
        # Remove implementation-markers from the polygon
        poly = [point for point, _ in polygon]
        for vertex in poly:
            if vertex in edges_h:
                edges_h.pop(vertex)
            if vertex in edges_v:
                edges_v.pop(vertex)

        p.append(poly)

    def point_in_poly(poly, point):
        """
        Check if point is contained in polygon.
        Run a semi-infinite ray horizontally (increasing x, fixed y) out from the test point,
        and count how many edges it crosses. At each crossing, the ray switches between inside and outside.
        This is called the Jordan curve theorem.
        :param poly: list of points, represented as tuples with x- and y-coordinates
        :param point: tuple with x- and y-coordinates
        :return: bool, whether or not the point is contained in the polygon
        """
        # TODO: Do boundary check beforehand? (Does this improve performance?)
        is_inside = False
        point_x = point[0]
        point_y = point[1]
        for i in range(len(poly)):
            if (poly[i][1] > point_y) is not (poly[i - 1][1] > point_y):
                if point_x < (poly[i - 1][0] - poly[i][0]) * (point_y - poly[i][1]) / (poly[i - 1][1] - poly[i][1]) + \
                        poly[i][0]:
                    is_inside = not is_inside
        return is_inside

    def point_in_polys(polys, point):
        """
        Check if point is contained in a list of polygons
        :param polys: list of polygons (where a polygon is a list of points, i.e. list of tuples)
        :param point: tuple with x- and y-coordinates
        :return: bool, whether or not the point is contained in any of the polygons
        """
        for poly in polys:
            if point_in_poly(poly, point):
                return True
        return False

    # Remove polygons contained in other polygons
    final_polygons = p.copy()
    if len(p) > 1:
        for poly in p:
            tmp_polys = p.copy()
            tmp_polys.remove(poly)
            # Only need to check if one point of the polygon is contained in another polygon
            # (By construction, the entire polygon is contained then)
            if point_in_polys(tmp_polys, poly[0]):
                final_polygons.remove(poly)

    return final_polygons


def get_dist_fast(point, bb):
    """ Calculate the distance between a ``point`` and a bounding box ``bb`` by adding up the x- and y-distance.

    :param point: a point given by [x, y]
    :param bb: the bounding box of a baseline polygon
    :type point: list of float
    :type bb: Rectangle
    :return: the distance of the point to the bounding box
    """
    dist = 0.0

    if point[0] < bb.x:
        dist += bb.x - point[0]
    if point[0] > bb.x + bb.width:
        dist += point[0] - bb.x - bb.width
    if point[1] < bb.y:
        dist += bb.y - point[1]
    if point[1] > bb.y + bb.height:
        dist += point[1] - bb.y - bb.height

    return dist


def get_in_dist(p1, p2, or_vec_x, or_vec_y):
    """ Calculate the inline distance of the points ``p1`` and ``p2`` according to the orientation vector with
    x-coordinate ``or_vec_x`` and y-coordinate ``or_vec_y``.

    :param p1: first point
    :param p2: second point
    :param or_vec_x: x-coordinate of the orientation vector
    :param or_vec_y: y-coordinate of the orientation vector
    :return: the inline distance of the points p1 and p2 according to the given orientation vector
    """
    diff_x = p1[0] - p2[0]
    diff_y = -p1[1] + p2[1]

    # Parallel component of (diff_x, diff_y) is lambda * (or_vec_x, or_vec_y) with lambda:
    return diff_x * or_vec_x + diff_y * or_vec_y


def get_off_dist(p1, p2, or_vec_x, or_vec_y):
    """ Calculate the offline distance of the points ``p1`` and ``p2`` according to the orientation vector with
    x-coordinate ``or_vec_x`` and y-coordinate ``or_vec_y``.

    :param p1: first point
    :param p2: second point
    :param or_vec_x: x-coordinate of the orientation vector
    :param or_vec_y: y-coordinate of the orientation vector
    :return: the offline distance of the points p1 and p2 according to the given orientation vector
    """
    diff_x = p1[0] - p2[0]
    diff_y = -p1[1] + p2[1]

    return diff_x * or_vec_y - diff_y * or_vec_x


def calc_tols(polys_truth, tick_dist=5, max_d=250, rel_tol=0.25):
    """ Calculate tolerance values for every GT baseline according to https://arxiv.org/pdf/1705.03311.pdf.

    :param polys_truth: groundtruth baseline polygons (normalized)
    :param tick_dist: desired distance of points of the baseline polygon (default: 5)
    :param max_d: max distance of pixels of a baseline polygon to any other baseline polygon (distance in terms of the
    x- and y-distance of the point to a bounding box of another polygon - see get_dist_fast) (default: 250)
    :param rel_tol: relative tolerance value (default: 0.25)
    :type polys_truth: list of Polygon
    :return: tolerance values of the GT baselines
    """
    tols = []

    for poly_a in polys_truth:
        # Calculate the angle of the linear regression line representing the baseline polygon poly_a
        angle = calc_reg_line_stats(poly_a)[0]
        # Orientation vector (given by angle) of length 1
        or_vec_y, or_vec_x = math.sin(angle), math.cos(angle)
        dist = max_d
        # first and last point of polygon
        pt_a1 = [poly_a.x_points[0], poly_a.y_points[0]]
        pt_a2 = [poly_a.x_points[-1], poly_a.y_points[-1]]

        # iterate over pixels of the current GT baseline polygon
        for x_a, y_a in zip(poly_a.x_points, poly_a.y_points):
            p_a = [x_a, y_a]
            # iterate over all other polygons (to calculate X_G)
            for poly_b in polys_truth:
                if poly_b != poly_a:
                    # if polygon poly_b is too far away from pixel p_a, skip
                    if get_dist_fast(p_a, poly_b.get_bounding_box()) > dist:
                        continue

                    # get first and last pixel of baseline polygon poly_b
                    pt_b1 = poly_b.x_points[0], poly_b.y_points[0]
                    pt_b2 = poly_b.x_points[-1], poly_b.y_points[-1]

                    # calculate the inline distance of the points
                    in_dist1 = get_in_dist(pt_a1, pt_b1, or_vec_x, or_vec_y)
                    in_dist2 = get_in_dist(pt_a1, pt_b2, or_vec_x, or_vec_y)
                    in_dist3 = get_in_dist(pt_a2, pt_b1, or_vec_x, or_vec_y)
                    in_dist4 = get_in_dist(pt_a2, pt_b2, or_vec_x, or_vec_y)
                    if (in_dist1 < 0 and in_dist2 < 0 and in_dist3 < 0 and in_dist4 < 0) or (
                            in_dist1 > 0 and in_dist2 > 0 and in_dist3 > 0 and in_dist4 > 0):
                        continue

                    for p_b in zip(poly_b.x_points, poly_b.y_points):
                        if abs(get_in_dist(p_a, p_b, or_vec_x, or_vec_y)) <= 2 * tick_dist:
                            dist = min(dist, abs(get_off_dist(p_a, p_b, or_vec_x, or_vec_y)))
        if dist < max_d:
            tols.append(dist)
        else:
            tols.append(0)

    sum_tols = 0.0
    num_tols = 0
    for tol in tols:
        if tol != 0:
            sum_tols += tol
            num_tols += 1

    mean_tols = max_d
    if num_tols:
        mean_tols = sum_tols / num_tols

    for i, tol in enumerate(tols):
        if tol == 0:
            tols[i] = mean_tols
        tols[i] = min(tols[i], mean_tols)
        tols[i] *= rel_tol

    return tols
