import functools

import math
import numpy as np

from citlab_python_util.geometry.polygon import calc_reg_line_stats, Polygon, norm_poly_dists
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
    all_polygons = []
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

        all_polygons.append(poly)

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
    final_polygons = all_polygons.copy()
    if len(all_polygons) > 1:
        for poly in all_polygons:
            tmp_polys = all_polygons.copy()
            tmp_polys.remove(poly)
            # Only need to check if one point of the polygon is contained in another polygon
            # (By construction, the entire polygon is contained then)
            if point_in_polys(tmp_polys, poly[0]):
                final_polygons.remove(poly)

    return final_polygons


def smooth_surrounding_polygon(polygons, poly_norm_dist=10, or_dims=(400, 800, 600, 400)):
    """
    Takes a list of "crooked" polygons and smooths them, by approximating vertical and horizontal edges.

    1.) The polygon gets normalized, where the resulting vertices are at most `poly_norm_dist` pixels apart.

    2.) For each vertex of the original polygon an orientation is determined:

    2.1) Four rectangles (North, East, South, West) are generated, with the dimensions given by `or_dims`
    (width_vertical, height_vertical, width_horizontal, height_horizontal), i.e. North and South rectangles
    have dimensions width_v x height_v, whereas East and West rectangles have dimensions width_h x height_h.

    2.2) Each rectangle counts the number of contained points from the normalized polygon

    2.3) The top two rectangle counts determine the orientation of the vertex: vertical, horizontal or one
    of the four possible corner types.

    3.) Vertices with a differing orientation to its agreeing neighbours are assumed to be mislabeled and
    get its orientation converted to its neighbours.

    4.) Corner clusters of the same type need to be shrunken down to one corner, with the rest being converted
    to verticals. (TODO or horizontals)

    5.) Clusters between corners (corner-V/H-...-V/H-corner) get smoothed if they contain at least five points,
    by taking the average over the y-coordinates for horizontal edges and the average over the x-coordinates for
    vertical edges.

    :param polygons: list of (not necessarily closed) polygons, where a polygon is represented as a list of tuples (x,y)
    :param poly_norm_dist: int, distance between pixels in normalized polygon
    :param or_dims: tuple (width_v, height_v, width_h, height_h), the dimensions of the orientation rectangles
    :return: dict (keys = article_id, values = smoothed polygons)
    """
    # Smooth each polygon separately
    for polygon in polygons:
        # Normalize polygon points over surrounding polygon
        surrounding_polygon = polygon.copy()
        if surrounding_polygon[0] != surrounding_polygon[-1]:
            surrounding_polygon.append(polygon[0])
        poly_xs, poly_ys = zip(*surrounding_polygon)
        poly = Polygon(list(poly_xs), list(poly_ys), len(poly_xs))
        poly_norm = norm_poly_dists([poly], des_dist=poly_norm_dist)[0]

        # Determine orientation for every vertex of the (original) polygon
        oriented_points = []
        for pt in polygon:
            # Build up 4 rectangles in each direction (N, E, S, W)
            width_v, height_v, width_h, height_h, = or_dims[0], or_dims[1], or_dims[2], or_dims[3]
            pt_x = pt[0]
            pt_y = pt[1]
            rect_n = Rectangle(pt_x - width_v // 2, pt_y - height_v, width_v, height_v)
            rect_s = Rectangle(pt_x - width_v // 2, pt_y, width_v, height_v)
            rect_e = Rectangle(pt_x, pt_y - height_h // 2, width_h, height_h)
            rect_w = Rectangle(pt_x - width_h, pt_y - height_h // 2, width_h, height_h)
            o_rects = {'n': rect_n, 'e': rect_e, 's': rect_s, 'w': rect_w}

            # Count the number of contained points from the normalized polygon in each rectangle
            rect_counts = {'n': 0, 'e': 0, 's': 0, 'w': 0}
            for r in o_rects:
                for pn in zip(poly_norm.x_points, poly_norm.y_points):
                    if o_rects[r].contains_point(pn):
                        rect_counts[r] += 1

            # Get orientation of vertex by top two rectangle counts
            sorted_counts = sorted(rect_counts.items(), key=lambda kv: kv[1], reverse=True)
            top_two = list(zip(*sorted_counts))[0][:2]
            if 'n' in top_two and 's' in top_two:
                pt_o = 'vertical'
            elif 'e' in top_two and 'w' in top_two:
                pt_o = 'horizontal'
            elif 'e' in top_two and 's' in top_two:
                pt_o = 'corner_ul'
            elif 'w' in top_two and 's' in top_two:
                pt_o = 'corner_ur'
            elif 'w' in top_two and 'n' in top_two:
                pt_o = 'corner_dr'
            else:
                pt_o = 'corner_dl'
            # Append point and its orientation as a tuple
            oriented_points.append((pt, pt_o))

        # Fix wrongly classified points between two same classified ones
        for i in range(len(oriented_points)):
            if oriented_points[i - 1][1] != oriented_points[i][1] \
                    and oriented_points[i - 1][1] == oriented_points[(i + 1) % len(oriented_points)][1]:
                oriented_points[i] = (oriented_points[i][0], oriented_points[i - 1][1])

        # Search for corner clusters of the same type and keep only one corner
        # TODO: Do we need to rearrange the list to start with a corner here already?
        # TODO: E.g. what if one of the clusters wraps around?
        for i in range(len(oriented_points)):
            # Found a corner
            if 'corner' in oriented_points[i][1]:
                # Get cluster (and IDs) with same corner type
                corner_cluster = [(i, oriented_points[i])]
                j = (i + 1) % len(oriented_points)
                while oriented_points[i][1] == oriented_points[j][1]:
                    corner_cluster.append((j, oriented_points[j]))
                    j = (j + 1) % len(oriented_points)
                if len(corner_cluster) > 1:
                    # Keep corner based on type and y-coordinate
                    corner_cluster_by_y = sorted(corner_cluster, key=lambda entry: entry[1][0][1])
                    # TODO: Is this robust enough?
                    # Keep corner with min y-coordinate for upper corners
                    if 'u' in oriented_points[i][1]:
                        cluster_to_remove = corner_cluster_by_y[1:]
                    # Keep corner with max y-coordinate for down corners
                    else:
                        cluster_to_remove = corner_cluster_by_y[:-1]
                    # Convert cluster to verticals
                    # TODO: What about horizontals?
                    for c in cluster_to_remove:
                        idx = c[0]
                        oriented_points[idx] = (oriented_points[idx][0], 'vertical')

        # Rearrange oriented_points list to start with a corner and wrap it around
        corner_idx = 0
        for i, op in enumerate(oriented_points):
            if 'corner' in op[1]:
                corner_idx = i
                break
        oriented_points = oriented_points[corner_idx:] + oriented_points[:corner_idx]
        oriented_points.append(oriented_points[0])

        # Go through the polygon and and get all corners
        corner_ids = []
        for i, op in enumerate(oriented_points):
            if 'corner' in op[1]:
                corner_ids.append(i)

        # Look at point clusters between neighboring corners
        # Build up list of alternating x- and y-coordinates (representing rays) and build up the polygon afterwards
        smoothed_edges = []
        # Check if we start with a horizontal edge
        # In this case, take the corresponding y-coordinate as the line/edge (otherwise x-coordinate)
        o_1 = oriented_points[corner_ids[0]][1]
        o_2 = oriented_points[corner_ids[1]][1]
        # Two upper corners or two lower corners
        if ('u' in o_1 and 'u' in o_2) or ('d' in o_1 and 'd' in o_2):
            is_horizontal = True
        # Two left or two right corners
        elif ('r' in o_1 and 'r' in o_2) or ('l' in o_1 and 'l' in o_2):
            is_horizontal = False
        # Mixed corners
        # Bigger y-gap than x-gap
        elif math.fabs(oriented_points[corner_ids[0]][0][0] - oriented_points[corner_ids[1]][0][0]) \
                < math.fabs(oriented_points[corner_ids[0]][0][1] - oriented_points[corner_ids[1]][0][1]):
            is_horizontal = False
        # Bigger x-gap than y-gap
        else:
            is_horizontal = True

        # j is the index for the x- or y-coordinate (horizontal = y, vertical = x)
        j = int(is_horizontal)
        for i in range(len(corner_ids) - 1):
            cluster = oriented_points[corner_ids[i]:corner_ids[i + 1] + 1]
            # Approximate edges with at least 5 points (including corners)
            if len(cluster) > 4:
                mean = 0
                for pt in cluster:
                    mean += pt[0][j]
                mean = round(float(mean) / len(cluster))
                smoothed_edges.append(mean)
                # Switch from x- to y-coordinate and vice versa
                j = int(not j)
            # Keep the rest as is, alternating between x- and y-coordinate for vertical / horizontal edges
            else:
                # Exclude last point so we don't overlap in the next cluster
                for pt in cluster[:-1]:
                    smoothed_edges.append(pt[0][j])
                    j = int(not j)

        # Go over list of x-y values and build up the polygon by taking the intersection of the rays as vertices
        smoothed_polygons = []
        for i in range(len(smoothed_edges)):
            if is_horizontal:
                smoothed_polygons.append((smoothed_edges[(i + 1) % len(smoothed_edges)], smoothed_edges[i]))
                is_horizontal = int(not is_horizontal)
            else:
                smoothed_polygons.append((smoothed_edges[i], smoothed_edges[(i + 1) % len(smoothed_edges)]))
                is_horizontal = int(not is_horizontal)

        return smoothed_polygons


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


def downscale_points(points, scale):
    """ Take as input a list of points `points` in (x,y) coordinates and scale them according to the rescaling factor
     `scale`.

    :param points: list of points in (x,y) coordinates
    :type points: list of Tuple(int, int)
    :param scale: scaling factor
    :type scale: float
    :return: list of downscaled (x,y) points
    """
    return [(int(x * scale), int(y * scale)) for (x, y) in points]


if __name__ == '__main__':
    points = [(3, 4), (1, 2)]
    scale = 0.5
    print(downscale_points(points, scale))
