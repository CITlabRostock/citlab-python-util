import os


def load_text_file(filename):
    """ Load text file ``filename`` and return the (stripped) lines as list entries.

    :param filename: path to the file to be loaded
    :type filename: str
    :return: list of strings consisting of the (stripped) lines from filename
    """
    res = []

    with open(filename, 'r') as f:
        for line in f:
            if line == "\n":
                res.append(line)
            else:
                res.append(line.strip())

        return res


def get_page_path(image_path, page_folder_name="page", append_extension=False):
    """
    Get the page path from the image path given that the page file lies in the "page" folder next to the image.
    If `append_extension` is True, just append the ".xml" extension to the image filename, otherwise replace it.
    :param append_extension: if True, append the ".xml" extension to the image filename, otherwise replace it
    :param page_folder_name: name of the folder where page file is stored in (defaults to "page")
    :param image_path: path to the image file we want the page file to
    :return: path to the page file that corresponds to `image_path`
    """
    dir_name = os.path.dirname(image_path)
    image_name = os.path.basename(image_path)
    if append_extension:
        return os.path.join(dir_name, page_folder_name, image_name + ".xml")
    return os.path.join(dir_name, page_folder_name, os.path.splitext(image_name)[0] + ".xml")
