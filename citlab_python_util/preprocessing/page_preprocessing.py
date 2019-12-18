import os
from shutil import copyfile
from pathlib import Path

import citlab_python_util.parser.xml.page.page as page
from citlab_python_util.basic.list_util import filter_by_attribute
from citlab_python_util.io import file_loader


class PagePreProcessor:
    """
    PagePreProcessor is a tool that corrects PAGE-XML files, e.g. deleting PAGE objects with the same ID.
    """

    def __init__(self, page_path_list):
        self.page_path_list = file_loader.load_text_file(page_path_list)
        self.page_object_list = self.create_page_objects()

    def create_page_objects(self):
        return [page.Page(path_to_page) for path_to_page in self.page_path_list]

    def delete_textlines_with_same_id(self):
        print("Start deleting redundant text lines..")
        for i, page_object in enumerate(self.page_object_list):
            textlines = page_object.get_textlines(ignore_redundant_textlines=False)

            tl_id_dict = filter_by_attribute(textlines, "id")
            redundant_textline_count = 0
            for tl_id, tl_list in tl_id_dict.items():
                if len(tl_list) > 1:
                    redundant_textline_count += 1
                    nds = page_object.get_child_by_id(page_object.page_doc, tl_id)
                    for nd in nds[:1]:
                        page_object.remove_page_xml_node(nd)
            print(
                f"{int((i+1)/len(self.page_object_list) * 100):>3}%: Found {redundant_textline_count} text line ids with multiple"
                f" assigned text lines in page file '{self.page_path_list[i]}'")

    def save_page_files(self, overwrite=False, save_folder=None):
        """
            Saving the (modified) page files coming from the preprocessor. There are four cases for the tuple (`overwrite`, `save_folder`):
            - (True, None) or (True, path): overwrite the (modified) page files
            - (False, None): backup the loaded page file (just append a '.bak') before saving the modified version
            - (False, path): save the (modified) page file to the directory given by save_folder
        """
        common_prefix = ""
        if save_folder:
            common_prefix = os.path.dirname(os.path.commonprefix(self.page_path_list)) + os.path.sep
        for page_path, page_object in zip(self.page_path_list, self.page_object_list):
            page_path_folder = os.path.dirname(page_path)
            # abs_save_folder = os.path.abspath(save_folder)
            # abs_page_path_folder = os.path.abspath(page_path_folder)
            real_save_folder = os.path.realpath(save_folder) if save_folder is not None else None
            real_page_path_folder = os.path.realpath(page_path_folder)

            if not overwrite and (save_folder is None or real_save_folder == real_page_path_folder):
                save_path = page_path
                copyfile(page_path, page_path + '.bak')
            elif overwrite or save_folder is None or real_save_folder == real_page_path_folder:
                save_path = page_path
            else:
                page_suffix = page_path.split(common_prefix)[-1]
                save_path = os.path.join(save_folder, page_suffix)
                if save_path == page_path:
                    raise ValueError("This behavior should not occur! "
                                     "If the save folder is equal to the path where the page is stored, "
                                     "the file should be backed up.")
                path = Path(os.path.dirname(save_path))
                path.mkdir(parents=True, exist_ok=True)

            page_object.write_page_xml(save_path)
