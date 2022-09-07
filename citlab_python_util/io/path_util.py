import os
import re
import glob


def get_path_from_exportdir(model_dir, pattern, not_pattern):
    """
    Extracts model pb path from given directory `model_dir`.

    Parameters `pattern` and `not_pattern` can be used to specify what pb files to match and not to match.

    :param model_dir: path to directory containing the model
    :param pattern: search for pb files matching this `pattern`
    :param not_pattern: exclude pb files containing this `not_pattern`
    :return: path to model pb file
    """
    export_dir = os.path.join(model_dir, "export")
    name = [x for x in glob.glob1(export_dir, pattern)]
    if not_pattern:
        name = [x for x in name if not_pattern not in x]
    if len(name) == 1:
        return os.path.join(export_dir, name[0])
    else:
        raise IOError(f"Found {len(name)} '{pattern}' files in '{export_dir}', there must be exactly one.")


def get_img_from_page_path(page_path):
    """
    Finds corresponding image file to given pageXML file, by matching its name and either removing or replacing
    the .xml extension with an image extension.

    It is assumed that the image file lies "up" one folder next to the "page" folder containing the pageXML file.

    :param page_path: path to pageXML file
    :return: path to matching image file
    """
    img_endings = ("tif", "jpg", "jpeg", "png")
    page_folder = os.path.dirname(os.path.abspath(page_path))
    page_name = os.path.splitext(os.path.basename(os.path.abspath(page_path)))[0]
    # go up the page folder
    folder = os.path.abspath(os.path.join(page_folder, ".."))
    # check for image file by substituting the .xml extension
    for ending in img_endings:
        img_path = os.path.join(folder, page_name + f".{ending}")
        if os.path.isfile(img_path):
            return img_path
    # check for image file by adding the image file extension
    for ending in img_endings:
        img_path = os.path.join(folder, page_name + f".xml.{ending}")
        if os.path.isfile(img_path):
            return img_path
    raise IOError(f"No image file (tif, png, jpg) found to given PageXML {page_path}")


def get_img_from_json_path(json_path):
    """
    Finds corresponding image file to given json file, by matching its name and either removing or replacing
    the .json extension with an image extension.

    It is assumed that the image file lies "up" one folder next to the "json" folder containing the json file.

    :param json_path: path to json file
    :return: path to matching image file
    """
    img_endings = ("tif", "jpg", "jpeg", "png")
    json_folder = os.path.dirname(os.path.abspath(json_path))
    json_name = os.path.splitext(os.path.basename(os.path.abspath(json_path)))[0]
    # go up the json folder
    folder = os.path.abspath(os.path.join(json_folder, ".."))
    # check for image file by substituting the .json extension
    for ending in img_endings:
        img_path = os.path.join(folder, json_name + f".{ending}")
        if os.path.isfile(img_path):
            return img_path
    # check for image file by adding the image file extension
    for ending in img_endings:
        img_path = os.path.join(folder, json_name + f".json.{ending}")
        if os.path.isfile(img_path):
            return img_path
    raise IOError(f"No image file (tif, png, jpg) found to given json {json_path}")


def get_page_from_img_path(image_path, page_folder_name="page"):
    """
    Finds corresponding pageXML file to given image file, by matching its name and either adding or subsituting
    the .xml extension.

    It is assumed that the page file lies in a `page_folder_name` folder next to the image file.

    :param image_path: path to image file
    :param page_folder_name: name of the folder where page file is stored in (defaults to "page")
    :return: path to matching page file
    """
    image_folder = os.path.dirname(image_path)
    image_name = os.path.basename(image_path)
    # go into page folder and look for pageXML file
    page_path = os.path.join(image_folder, page_folder_name, os.path.splitext(image_name)[0] + ".xml")
    if os.path.isfile(page_path):
        return page_path
    page_path = os.path.join(image_folder, page_folder_name, image_name + ".xml")
    if os.path.isfile(page_path):
        return page_path
    raise IOError("No pageXML file found to given image file ", image_path)


def get_page_from_json_path(json_path, page_folder_name="page"):
    """
    Finds corresponding pageXML file to given json file, by matching its name and replacing the .json
    extension with an .xml extension.

    It is assumed that the page file lies in a `page_folder_name` folder next to the json file, which lies
    in a "json*" folder.

    :param json_path: path to json file
    :param page_folder_name: name of the folder where page file is stored in (defaults to "page")
    :return: path to matching page file
    """
    json_folder = os.path.dirname(os.path.abspath(json_path))
    json_name = os.path.splitext(os.path.basename(os.path.abspath(json_path)))[0]
    # go up the json folder and check for pageXML file
    folder = os.path.join(json_folder, "..", page_folder_name)
    page_path = os.path.join(folder, json_name + ".xml")
    if os.path.isfile(page_path):
        return page_path
    raise IOError("No pageXML file found to given (confidence) json file ", json_path)


def get_page_from_conf_path(json_path, page_folder_name="page"):
    """
    Finds corresponding pageXML file to given confidence (json) file, by matching its name and replacing the .json
    extension with an .xml extension.

    It is assumed that the page file lies in a `page_folder_name` folder next to the confidence (json) file, which lies
    in a "confidences" folder.

    :param json_path: path to confidence (json) file
    :param page_folder_name: name of the folder where page file is stored in (defaults to "page")
    :return: path to matching page file
    """
    conf_folder = os.path.dirname(os.path.abspath(json_path))
    conf_name = os.path.splitext(os.path.basename(os.path.abspath(json_path)))[0]
    page_name = re.sub(r'(.+)_confidences$', r'\1', conf_name)
    # go up the confidences folder and check for pageXML file
    folder = os.path.join(conf_folder, "..", page_folder_name)
    page_path = os.path.join(folder, page_name + ".xml")
    if os.path.isfile(page_path):
        return page_path
    raise IOError("No pageXML file found to given (confidence) json file ", json_path)


def prepend_folder_name(file_path):
    folder_path = os.path.dirname(file_path)
    folder_name = os.path.basename(folder_path)
    file_name = os.path.basename(file_path)
    new_file_name = folder_name + "_" + file_name
    return os.path.join(folder_path, new_file_name)
