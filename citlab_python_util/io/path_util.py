import os
import re


def get_img_from_page_path(page_path):
    # go up the page folder, remove .xml ending and check for img file
    img_endings = ("tif", "jpg", "png")
    img_path = re.sub(r'/page/([-\w.]+)\.xml$', r'/\1', page_path)
    for ending in img_endings:
        if img_path.endswith(ending):
            if os.path.isfile(img_path):
                return img_path
    # go up the page folder, substitute .xml ending and check for img file
    img_path = re.sub(r'/page/([-\w.]+)\.xml$', r'/\1.tif', page_path)
    if not os.path.isfile(img_path):
        img_path = re.sub(r'tif$', r'png', img_path)
        if not os.path.isfile(img_path):
            img_path = re.sub(r'png$', r'jpg', img_path)
            if not os.path.isfile(img_path):
                raise IOError(f"No image file (tif, png, jpg) found to given pagexml {page_path}")
    return img_path


def get_img_from_json_path(json_path):
    # go up the json folder, remove .json ending and check for img file
    img_endings = ("tif", "jpg", "png")
    img_path = re.sub(r'/json\w*/([-\w.]+)\.json$', r'/\1', json_path)
    for ending in img_endings:
        if img_path.endswith(ending):
            if os.path.isfile(img_path):
                return img_path
    # go up the json folder, substitute .json ending and check for img file
    img_path = re.sub(r'/json\w*/([-\w.]+)\.json$', r'/\1.tif', json_path)
    if not os.path.isfile(img_path):
        img_path = re.sub(r'tif$', r'png', img_path)
        if not os.path.isfile(img_path):
            img_path = re.sub(r'png$', r'jpg', img_path)
            if not os.path.isfile(img_path):
                raise IOError("No image file (tif, png, jpg) found to given json ", json_path)
    return img_path


def get_page_from_img_path(img_path):
    # go into page folder, append .xml and check for pageXML file
    page_path = re.sub(r'/([-\w.]+)$', r'/page/\1.xml', img_path)
    if os.path.isfile(page_path):
        return page_path
    # go into page folder, substitute img ending for .xml and check for pageXML file
    page_path = re.sub(r'/([-\w.]+)\.\w+$', r'/page/\1.xml', img_path)
    if not os.path.isfile(page_path):
        raise IOError("No pagexml file found to given img file ", img_path)
    return page_path


def get_page_from_json_path(json_path):
    # go into page folder, append .xml and check for pageXML file
    page_path = re.sub(r'/json\w*/([-\w.]+)$', r'/page/\1.xml', json_path)
    if os.path.isfile(page_path):
        return page_path
    # go into page folder, substitute .json for .xml and check for pageXML file
    page_path = re.sub(r'/json\w*/([-\w.]+)\.json$', r'/page/\1.xml', json_path)
    if not os.path.isfile(page_path):
        raise IOError("No pagexml file found to given json file ", json_path)
    return page_path
