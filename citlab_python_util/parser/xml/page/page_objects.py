# -*- coding: utf-8 -*-
import numpy as np

from citlab_python_util.geometry.polygon import Polygon


def polygon_to_points(poly):
    """Convert a Polygon object ``poly`` to a Points object."""
    x, y = poly.x_points, poly.y_points

    return Points(list(zip(x, y)))


def string_to_points(s):
    """Convert a PageXml valid string to a list of (x,y) values."""

    l_s = s.split(' ')
    l_xy = list()
    for s_pair in l_s:  # s_pair = 'x,y'
        try:
            (sx, sy) = s_pair.split(',')
            l_xy.append((int(sx), int(sy)))
        except ValueError:
            print("Can't convert string '{}' to a point.".format(s_pair))
            exit(1)

    return l_xy


class Points:
    def __init__(self, points_list):
        self.points_list = points_list

    def to_string(self):
        """Convert self.points_list to a PageXml valid format:
        'x1,y1 x2,y2 ... xN,yN'.

        :return: PageXml valid string format of coordinates.
        """
        s = ""
        for pt in self.points_list:
            if s:
                s += " "
            s += "%s,%s" % (pt[0], pt[1])
        return s

    def to_polygon(self):
        x, y = np.transpose(self.points_list)

        return Polygon(x.tolist(), y.tolist(), n_points=len(x))


class Region:
    def __init__(self, _id, custom, points):
        self.id = _id
        self.custom = custom
        self.points = Points(points)


class TextRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class ImageRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class LineDrawingRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class GraphicRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class TableRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class ChartRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class SeparatorRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class MathsRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class ChemRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class MusicRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class AdvertRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class NoiseRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class UnknownRegion(Region):
    def __init__(self, _id, custom, points):
        super().__init__(_id, custom, points)


class TextLine:
    def __init__(self, _id, custom=None, text=None, baseline=None, surr_p=None):
        self.id = _id  # unique id of textline (str)
        # dictionary of dictionaries, e.g. {'readingOrder':{ 'index':'4' },'structure':{'type':'catch-word'}}
        self.custom = custom  # custom attr holding information like article id (dict of dicts)
        self.baseline = Points(baseline) if baseline else None  # baseline of textline (Points object)
        self.text = text  # text present in the textline
        self.surr_p = Points(surr_p) if surr_p else None  # surrounding polygon of textline (Points object)

    def get_reading_order(self):
        try:
            return self.custom["readingOrder"]["index"]
        except KeyError:
            # print("Reading order index missing.")
            return None

    def get_article_id(self):
        try:
            return self.custom["structure"]["id"] if self.custom["structure"]["type"] == "article" else None
        except KeyError:
            # print("Article ID missing.")
            return None

    def set_reading_order(self, reading_order):
        if reading_order:
            try:
                self.custom["readingOrder"]["index"] = str(reading_order)
            except KeyError:
                self.custom["readingOrder"] = {}
                self.custom["readingOrder"]["index"] = str(reading_order)
        else:
            try:
                self.custom.pop("readingOrder")
            except KeyError:
                pass

    def set_article_id(self, article_id=None):
        if article_id:
            try:
                self.custom["structure"]["id"] = str(article_id)
            except KeyError:
                self.custom["structure"] = {}
                self.custom["structure"]["id"] = str(article_id)
            self.custom["structure"]["type"] = "article"
        else:
            try:
                self.custom.pop("structure")
            except KeyError:
                pass


if __name__ == '__main__':
    points = [(1, 2), (3, 4), (5, 6)]
    points = Points(points)
    print(points.to_string())
    poly = points.to_polygon()
    print(poly.x_points, poly.y_points, poly.n_points)
    points_copy = polygon_to_points(poly)
    print(points_copy.to_string())
