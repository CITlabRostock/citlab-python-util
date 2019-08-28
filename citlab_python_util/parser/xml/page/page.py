# -*- coding: utf-8 -*-
import os
import datetime
import logging

import cssutils
from lxml import etree
from argparse import ArgumentParser

from citlab_python_util.parser.xml.page.page_objects import *

# Make sure that the css parser for the custom attribute doesn't spam "WARNING Property: Unknown Property name."
cssutils.log.setLevel(logging.ERROR)

logging.basicConfig(filename="docs/Page.log",
                    format="%(asctime)s:%(levelname)s:%(message)s", filemode="w")  # add filemode="w" to overwrite file


class PageXmlException(Exception):
    pass


class Page:
    """
    Various utilities to deal with PageXml format
    """
    # Creators name
    sCREATOR = "CITlab"

    # Namespace for PageXml
    NS_PAGE_XML = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"

    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XSILOCATION = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 " \
                  "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd"

    # Schema for Transkribus PageXml
    XSL_SCHEMA_FILENAME = "pagecontent_transkribus.xsd"

    # XML schema loaded once for all
    cachedValidationContext = None

    sMETADATA_ELT = "Metadata"
    sCREATOR_ELT = "Creator"
    sCREATED_ELT = "Created"
    sLAST_CHANGE_ELT = "LastChange"
    sCOMMENTS_ELT = "Comments"
    sTranskribusMetadata_ELT = "TranskribusMetadata"
    sPRINT_SPACE = "PrintSpace"
    sCUSTOM_ATTR = "custom"
    sTEXTLINE = "TextLine"
    sBASELINE = "Baseline"
    sCOORDS = "Coords"

    sPOINTS_ATTR = "points"

    sREGIONS = {"TextRegion": TextRegion, "ImageRegion": ImageRegion, "LineDrawingRegion": LineDrawingRegion,
                "GraphicRegion": GraphicRegion, "TableRegion": TableRegion, "ChartRegion": ChartRegion,
                "SeparatorRegion": SeparatorRegion, "MathsRegion": MathsRegion, "ChemRegion": ChemRegion,
                "MusicRegion": MusicRegion, "AdvertRegion": AdvertRegion, "NoiseRegion": NoiseRegion,
                "UnknownRegion": UnknownRegion}

    sEXT = ".xml"

    def __init__(self, path_to_xml=None, creator_name=sCREATOR, img_filename=None, img_w=None, img_h=None):
        self.page_doc = self.load_page_xml(path_to_xml) if path_to_xml is not None else self.create_page_xml_document(
            creator_name, img_filename, img_w, img_h)
        if len(self.page_doc.getroot().getchildren()) != 2:
            elts = self.page_doc.getroot().getchildren()
            # if Metadata node is missing, add it
            if self.sMETADATA_ELT not in [elt.tag for elt in elts]:
                self.create_metadata(self.sCREATOR, comments="Metadata entry was missing, added..")

        if not self.validate(self.page_doc):
            logging.warning("File given by {} is not a valid PageXml file.".format(path_to_xml))
            # exit(1)
        self.metadata = self.get_metadata()
        self.textlines = self.get_textlines()

    # =========== SCHEMA ===========

    def validate(self, doc):
        """
        Validate against the PageXml schema used by Transkribus

        Return True or False
        """
        if not self.cachedValidationContext:
            schema_filename_ = self.get_schema_filename()
            xmlschema_doc = etree.parse(schema_filename_)
            self.cachedValidationContext = etree.XMLSchema(xmlschema_doc)

        b_valid = self.cachedValidationContext.validate(doc)
        log = self.cachedValidationContext.error_log

        if not b_valid:
            logging.warning(log)
        return b_valid

    @classmethod
    def get_schema_filename(cls):
        """
        Return the path to the schema, built from the path of this module.
        """
        filename = os.path.join(os.path.dirname(__file__), cls.XSL_SCHEMA_FILENAME)
        return filename

    # =========== METADATA ===========
    """
    <complexType name="MetadataType">
        <sequence>
            <element name="Creator" type="string"></element>
            <element name="Created" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="LastChange" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="Comments" type="string" minOccurs="0"
                maxOccurs="1"></element>
        </sequence>
    </complexType>
    """

    def get_metadata(self):
        """
        Parse the metadata of the PageXml DOM or of the given Metadata node
        return a Metadata object
        """
        _, nd_creator, nd_created, nd_last_change, nd_comments = self._get_metadata_nodes()
        return Metadata(nd_creator.text
                        , nd_created.text
                        , nd_last_change.text
                        , nd_comments.text if nd_comments is not None else None)

    def set_metadata(self, creator, comments=None):
        """
        Pass EITHER a DOM or a Metadata DOM node!! (and pass None for the other)
        Set the metadata of the PageXml DOM or of the given Metadata node

        Update the Created and LastChange fields.
        Either update the comments fields or delete it.

        You MUST indicate the creator (a string)
        You MAY give a comments (a string)
        The Created field is kept unchanged
        The LastChange field is automatically set.
        The comments field is either updated or deleted.
        return the Metadata DOM node
        """
        nd_metadata, nd_creator, nd_created, nd_last_change, nd_comments = self._get_metadata_nodes()
        if nd_creator.text and nd_creator.text != creator:
            nd_creator.text += ", modified by " + creator
        # The schema seems to call for GMT date&time  (IMU)
        # ISO 8601 says:  "If the time is in UTC, add a Z directly after the time without a space. Z is the zone
        # designator for the zero UTC offset."
        # Python seems to break the standard unless one specifies properly a timezone by sub-classing tzinfo.
        # But too complex stuff so, I simply add a 'Z'
        nd_last_change.text = datetime.datetime.utcnow().isoformat() + "Z"
        if comments is not None:
            if not nd_comments:  # we need to add one!
                nd_comments = etree.SubElement(nd_metadata, self.sCOMMENTS_ELT)
            nd_comments.text = comments
        return nd_metadata

    def create_metadata(self, creator_name=sCREATOR, comments=None):
        xml_page_root = self.page_doc.getroot()

        metadata = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sMETADATA_ELT))
        xml_page_root.insert(0, metadata)
        creator = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sCREATOR_ELT))
        creator.text = creator_name
        created = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sCREATED_ELT))
        created.text = datetime.datetime.utcnow().isoformat() + "Z"
        last_change = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sLAST_CHANGE_ELT))
        last_change.text = datetime.datetime.utcnow().isoformat() + "Z"
        comments_nd = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sCOMMENTS_ELT))
        comments_nd.text = comments

        metadata.append(creator)
        metadata.append(created)
        metadata.append(last_change)
        metadata.append(comments_nd)

        return metadata

    def _get_metadata_nodes(self):
        """
        Parse the metadata of the PageXml DOM or of the given Metadata node
        return a 4-tuple:
            DOM nodes of Metadata, Creator, Created, Last_Change, Comments (or None if no comments)
        """
        l_nd = self.get_child_by_name(self.page_doc, self.sMETADATA_ELT)
        if len(l_nd) != 1:
            raise ValueError(
                "PageXml should have exactly one %s node but found %s" % (self.sMETADATA_ELT, str(len(l_nd))))
        dom_nd = l_nd[0]
        assert etree.QName(dom_nd.tag).localname == self.sMETADATA_ELT
        nd1 = dom_nd[0]

        if etree.QName(nd1.tag).localname != self.sCREATOR_ELT:
            raise ValueError("PageXMl mal-formed Metadata: Creator element must be 1st element")

        nd2 = nd1.getnext()
        if etree.QName(nd2.tag).localname != self.sCREATED_ELT:
            raise ValueError("PageXMl mal-formed Metadata: Created element must be 2nd element")

        nd3 = nd2.getnext()
        if etree.QName(nd3.tag).localname != self.sLAST_CHANGE_ELT:
            raise ValueError("PageXMl mal-formed Metadata: LastChange element must be 3rd element")

        nd4 = nd3.getnext()
        if nd4 is not None:
            if etree.QName(nd4.tag).localname not in [self.sCOMMENTS_ELT, self.sTranskribusMetadata_ELT]:
                raise ValueError("PageXMl mal-formed Metadata: Comments element must be 4th element")
        return dom_nd, nd1, nd2, nd3, nd4

    # =========== XML STUFF ===========
    @classmethod
    def get_child_by_name(cls, elt, s_child_name):
        """
        look for all child elements having that name in PageXml namespace!!!
            Example: lNd = PageXMl.get_child_by_name(elt, "Baseline")
        return a DOM node
        """
        # return elt.findall(".//{%s}:%s"%(cls.NS_PAGE_XML,s_child_name))
        return elt.xpath(".//pc:%s" % s_child_name, namespaces={"pc": cls.NS_PAGE_XML})

    def get_ancestor_by_name(self, elt, s_name):
        return elt.xpath("ancestor::pc:%s" % s_name, namespaces={"pc": self.NS_PAGE_XML})

    @classmethod
    def get_child_by_id(cls, elt, _id):
        """
        look for all child elements having that id
            Example: lNd = PageXMl.get_child_by_id(elt, "tl_2")
        return a DOM node
        """
        return elt.xpath(".//*[@id='%s']" % _id)

    @classmethod
    def get_ancestor_by_id(cls, elt, _id):
        """
        look for all ancestor elements having that id
            Example: lNd = PageXMl.get_ancestor_by_name(elt, "tl_2")
        return a DOM node
        """
        return elt.xpath("ancestor::*[@id='%s']" % _id)

    def get_custom_attr(self, nd, s_attr_name, s_sub_attr_name=None):
        """
        Read the custom attribute, parse it, and extract the 1st or 1st and 2nd key value
        e.g. get_custom_attr(nd, "structure", "type")     -->  "catch-word"
        e.g. get_custom_attr(nd, "structure")             -->  {'type':'catch-word', "toto", "tutu"}
        return a dictionary if no 2nd key provided, or a string if 1st and 2nd key provided
        Raise KeyError if one of the attribute does not exist
        """
        c_node = nd.get(self.sCUSTOM_ATTR)
        if c_node is None:
            return None
        ddic = self.parse_custom_attr(c_node)

        # First key

    def set_custom_attr_from_dict(self, nd, custom_dict):
        nd.set(self.sCUSTOM_ATTR, self.format_custom_attr(custom_dict))
        return nd

    def set_custom_attr(self, nd, s_attr_name, s_sub_attr_name, s_val):
        """
        Change the custom attribute by setting the value of the 1st+2nd key in the DOM
        return the value
        Raise KeyError if one of the attributes does not exist
        """
        ddic = self.parse_custom_attr(nd.get(self.sCUSTOM_ATTR))
        try:
            ddic[s_attr_name][s_sub_attr_name] = str(s_val)
        except KeyError:
            ddic[s_attr_name] = dict()
            ddic[s_attr_name][s_sub_attr_name] = str(s_val)

        sddic = self.format_custom_attr(ddic)
        nd.set(self.sCUSTOM_ATTR, sddic)
        return s_val

    def remove_custom_attr(self, nd, s_attr_name, s_sub_attr_name):
        ddic = self.parse_custom_attr(nd.get(self.sCUSTOM_ATTR))
        if s_attr_name in ddic and s_sub_attr_name in ddic[s_attr_name]:
            ddic[s_attr_name].pop(s_sub_attr_name)
        else:
            print("Can't remove {} from {} in {}.".format(s_sub_attr_name, s_attr_name, ddic))

    @staticmethod
    def parse_custom_attr(s):
        """
        The custom attribute contains data in a CSS style syntax.
        We parse this syntax here and return a dictionary of dictionaries

        Example:
        parse_custom_attr( "readingOrder {index:4;} structure {type:catch-word;}" )
            --> { 'readingOrder': { 'index':'4' }, 'structure':{'type':'catch-word'} }
        """
        if not s:
            return {}
        custom_dict = {}
        sheet = cssutils.parseString(s)
        for rule in sheet:
            selector = rule.selectorText
            prop_dict = {}
            for prop in rule.style:
                prop_dict[prop.name] = prop.value
            custom_dict[selector] = prop_dict

        return custom_dict

    @staticmethod
    def format_custom_attr(ddic):
        """
        Format a dictionary of dictionaries in string format in the "custom attribute" syntax
        e.g. custom="readingOrder {index:1;} structure {type:heading;}"
        """
        s = ""
        for k1, d2 in ddic.items():
            if s:
                s += " "
            s += "%s" % k1
            s2 = ""
            for k2, v2 in d2.items():
                if s2:
                    s2 += " "
                s2 += "%s:%s;" % (k2, v2)
            s += " {%s}" % s2
        return s

    @classmethod
    def get_text_equiv(cls, nd):
        textequiv = cls.get_child_by_name(nd, "TextEquiv")
        if not textequiv:
            return ''
        # TODO: Maybe replace by getting the first entry of just one hierarchy below,
        #  e.g.for TextLine ignoring the Word data
        text = cls.get_child_by_name(textequiv[-1], "Unicode")
        if not text:
            return ''
        return text[0].text

    @staticmethod
    def make_text(nd):
        """
        build the text of a sub-tree by considering that textual nodes are tokens to be concatenated, with a space as separator
        NO! (JLM 2018)return None if no textual node found

        return empty string if no text node found
        """
        return " ".join(nd.itertext())

    # =========== GEOMETRY ===========
    @staticmethod
    def get_point_list(data):
        """
        get either an XML node of a PageXml object
              , or the content of a points attribute, e.g.
                1340,240 1696,240 1696,304 1340,304
        return the list of (x,y) of the polygon of the object - ( it is a list of int tuples)
        """
        try:
            ls_pair = data.split(' ')
        except AttributeError:
            lnd_points = data.xpath("(.//@points)[1]")
            s_points = lnd_points[0]
            ls_pair = s_points.split(' ')
        try:
            l_xy = list()
            for s_pair in ls_pair:  # s_pair = 'x,y'
                (sx, sy) = s_pair.split(',')
                l_xy.append((int(sx), int(sy)))
        except ValueError:
            return None
        return l_xy

    @staticmethod
    def set_points(nd, l_xy):
        """
        set the points attribute of that node to reflect the l_xy values
        if nd is None, only returns the string that should be set to the @points attribute
        return the content of the @points attribute
        """
        s_pairs = " ".join(["%d,%d" % (int(x), int(y)) for x, y in l_xy])
        if nd is not None:
            nd.set("points", s_pairs)
        return s_pairs

    # ======== ARTICLE STUFF =========

    def get_article_dict(self):
        article_dict = {}
        for tl in self.textlines:
            a_id = tl.get_article_id()
            if a_id in article_dict:
                article_dict[a_id].append(tl)
            else:
                article_dict[a_id] = [tl]

        return article_dict

    def get_image_resolution(self):
        page_nd = self.get_child_by_name(self.page_doc, "Page")[0]
        img_width = int(page_nd.get("imageWidth"))
        img_height = int(page_nd.get("imageHeight"))

        return img_width, img_height

    def get_print_space_coords(self):
        ps_nd = self.get_child_by_name(self.page_doc, self.sPRINT_SPACE)

        if len(ps_nd) != 1:
            print(f"Expected exactly one {self.sPRINT_SPACE} node, but got {len(ps_nd)}.")
            # exit(1)
            print(f"Fallback to image size.")
            img_width, img_height = self.get_image_resolution()

            ps_coords = [(0, 0), (img_width, 0), (img_width, img_height), (0, img_height)]

        else:
            ps_nd = ps_nd[0]

            # we assume that the PrintSpace is given as a rectangle, thus having four coordinates
            ps_coords = self.get_point_list(self.get_child_by_name(ps_nd, self.sCOORDS)[0].get(self.sPOINTS_ATTR))
            for i, (x, y) in enumerate(ps_coords):
                if x < 0:
                    x_new = 0
                else:
                    x_new = x
                if y < 0:
                    y_new = 0
                else:
                    y_new = y
                ps_coords[i] = (x_new, y_new)

            if len(ps_coords) != 4:
                print(f"Expected exactly four rectangle coordinates, but got {len(ps_coords)}.")
                exit(1)

        return ps_coords

    def get_regions(self):
        res = {}
        for r_name in self.sREGIONS.keys():
            r_nds = self.get_child_by_name(self.page_doc, r_name)
            if len(r_nds) > 0:
                r_class = self.sREGIONS[r_name]
                res[r_name] = [r_class(reg.get("id"), self.parse_custom_attr(reg.get(self.sCUSTOM_ATTR)),
                                       self.get_point_list(
                                           self.get_child_by_name(reg, self.sCOORDS)[0].get(self.sPOINTS_ATTR)))
                               for reg in r_nds]
        return res

    def get_textlines(self):
        tl_nds = self.get_child_by_name(self.page_doc, self.sTEXTLINE)

        res = []
        for tl in tl_nds:
            tl_id = tl.get("id")
            tl_custom_attr = self.parse_custom_attr(tl.get(self.sCUSTOM_ATTR))
            tl_text = self.get_text_equiv(tl)
            tl_bl_nd = self.get_child_by_name(tl, self.sBASELINE)
            tl_bl = self.get_point_list(tl_bl_nd[0]) if tl_bl_nd else None
            tl_surr_p = self.get_point_list(tl)
            res.append(TextLine(tl_id, tl_custom_attr, tl_text, tl_bl, tl_surr_p))

        # return [TextLine(tl.get("id"), self.parse_custom_attr(tl.get(self.sCUSTOM_ATTR)), self.get_text_equiv(tl),
        #                  self.get_point_list(self.get_child_by_name(tl, self.sBASELINE)[0]), self.get_point_list(tl))
        #         for tl in tl_nds]

        return res

    def set_textline_attr(self, textlines):
        """

        :param textlines: list of TextLine objects
        :type textlines: list of TextLine
        :return: None
        """
        for tl in textlines:
            tl_nd = self.get_child_by_id(self.page_doc, tl.id)[0]
            self.set_custom_attr_from_dict(tl_nd, tl.custom)
            # for k, d in tl.custom.items():
            #     for k1, v1 in d.items():
            #         if v1 is None:
            #             self.remove_custom_attr(tl_nd, k, k1)
            #             break
            #         else:
            #             self.set_custom_attr(tl_nd, k, k1, v1)

            # if tl.get_article_id() is None:
            #     continue
            # tl_nd = cls.get_child_by_id(nd, tl.id)[0]
            # cls.set_custom_attr(tl_nd, "structure", "id", tl.get_article_id())
            # cls.set_custom_attr(tl_nd, "structure", "type", "article")

    # =========== CREATION ===========
    def create_page_xml_document(self, creator_name=sCREATOR, filename=None, img_w=0, img_h=0):
        """
            create a new PageXml document
        """
        xml_page_root = etree.Element('{%s}PcGts' % self.NS_PAGE_XML,
                                      attrib={"{" + self.NS_XSI + "}schemaLocation": self.XSILOCATION},  # schema loc.
                                      nsmap={None: self.NS_PAGE_XML})  # Default ns
        self.page_doc = etree.ElementTree(xml_page_root)

        metadata = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sMETADATA_ELT))
        xml_page_root.append(metadata)
        creator = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sCREATOR_ELT))
        creator.text = creator_name
        created = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sCREATED_ELT))
        created.text = datetime.datetime.utcnow().isoformat() + "Z"
        last_change = etree.Element('{%s}%s' % (self.NS_PAGE_XML, self.sLAST_CHANGE_ELT))
        last_change.text = datetime.datetime.utcnow().isoformat() + "Z"
        metadata.append(creator)
        metadata.append(created)
        metadata.append(last_change)

        page_node = etree.Element('{%s}%s' % (self.NS_PAGE_XML, 'Page'))
        page_node.set('imageFilename', filename)
        page_node.set('imageWidth', str(img_w))
        page_node.set('imageHeight', str(img_h))

        xml_page_root.append(page_node)

        b_validate = self.validate(self.page_doc)
        assert b_validate, 'new file not validated by schema'

        return page_node

    @classmethod
    def create_page_xml_node(cls, node_name):
        """
            create a PageXMl element
        """
        node = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, node_name))

        return node

    def insert_page_xml_node(self, parent_nd, node_name):
        """ Add PageXml node as child node of ``parent_nd``.

        :param parent_nd: node where PageXml node is added as child
        :param node_name: name of the node
        :return: the inserted node
        """
        node = self.create_page_xml_node(node_name)
        parent_nd.append(node)

        return node

    def load_page_xml(self, path_to_xml):
        """Load PageXml file located at ``path_to_xml`` and return a DOM node.

        :param path_to_xml: path to PageXml file
        :return: DOM document node
        :rtype: etree._ElementTree
        """
        page_doc = etree.parse(path_to_xml, etree.XMLParser(remove_blank_text=True))
        if not self.validate(page_doc):
            logging.warning("PageXml is not valid according to the Page schema definition {}.".format(self.XSILOCATION))

        return page_doc

    def write_page_xml(self, save_path, creator=sCREATOR, comments=None):
        """Save PageXml file to ``save_path``.

        @:param save_path:
        @:return: None
        """
        self.set_metadata(creator, comments)

        with open(save_path, "w") as f:
            f.write(etree.tostring(self.page_doc, pretty_print=True, encoding="UTF-8", standalone=True,
                                   xml_declaration=True).decode("utf-8"))


# =========== METADATA OF PAGEXML ===========
class Metadata:
    """
    <complexType name="MetadataType">
        <sequence>
            <element name="Creator" type="string"></element>
            <element name="Created" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="LastChange" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="Comments" type="string" minOccurs="0"
                maxOccurs="1"></element>
        </sequence>
    </complexType>
    """

    def __init__(self, creator, created, last_change, comments=None):
        self.Creator = creator  # a string
        self.Created = created  # a string
        self.LastChange = last_change  # a string
        self.Comments = comments  # None or a string


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--path_to_xml', default='', type=str, metavar="STR",
                        help="path to the PageXml file")
    flags = parser.parse_args()

    page = Page(flags.path_to_xml)

    print(page.get_article_dict())

    # textlines = page.get_textlines()
    # for tl in textlines:
    #     if tl.get_article_id() is not None:
    #         tl.set_article_id(None)
    # page.set_textline_attr(textlines)

    # page.write_page_xml("./test/resources/page_xml_no_meta_copy.xml")

    # textlines = page.get_textlines()
    # # set all textline article ids to "a1"
    # # textline attrs are changed via id -> for now adding textlines is not supported!
    # for tl in textlines:
    #     tl.set_article_id("a1")
    #     # print(tl.baseline.points_list)
    #     print(tl.surr_p.to_polygon().x_points)
    # page.set_textline_attr(textlines)
    # page.write_page_xml("./test/resources/page_xml_copy.xml")
