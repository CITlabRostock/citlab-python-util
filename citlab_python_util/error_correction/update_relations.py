import os
import glob
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from citlab_python_util.parser.xml.page.page import Page, Relation
from citlab_python_util.logging.custom_logging import setup_custom_logger

logger = setup_custom_logger(__name__, level="debug")


def find_dirs(name, root='.', exclude=None):
    results = []
    for path, dirs, files in os.walk(root):
        if name in dirs:
            # return os.path.join(path, name)
            results.append(os.path.join(path, name))
    if exclude:
        for ex in exclude.split(","):
            results = [res for res in results if ex not in res]
    return results


def find_paths(root=".", ending="xml", exclude=None):
    results = []
    for path in Path(root).rglob(f'*.{ending}'):
        results.append(str(path))
    if exclude:
        for ex in exclude.split(","):
            results = [res for res in results if ex not in res]
    return results


def build_relations(article_ids, text_region_ids):
    # gather regions belonging to same cluster in dict
    article_region_pairs = zip(article_ids, text_region_ids)
    article_region_dict = dict()
    for a_id, tr_id in article_region_pairs:
        try:
            article_region_dict[a_id].append(tr_id)
        except KeyError:
            article_region_dict[a_id] = [tr_id]

    # create (article) relations
    relations = []
    for a_id, text_region_ids in article_region_dict.items():
        relation = Relation("link", region_refs=text_region_ids)
        relation.set_article_id(a_id)
        relations.append(relation)

    return relations


def update_article_relations(page_paths, overwrite=False):
    """Method to update the (article) relations in a pageXML based on the given textline article ids."""
    overall_ambiguous = 0
    for page_path in page_paths:
        logger.info(f"Updating {page_path}...")
        page = Page(page_path)
        text_regions = page.get_text_regions()
        num_ambiguous = 0
        tr_article_ids = []
        # get text region article ids from corresponding textlines
        for text_region in text_regions:
            # get all article_ids for textlines in this region
            textline_article_ids = []
            for text_line in text_region.text_lines:
                textline_article_ids.append(text_line.get_article_id())
            # count article_id occurences
            unique_article_ids = list(set(textline_article_ids))
            article_id_occurences = np.array([textline_article_ids.count(a_id) for a_id in unique_article_ids],
                                             dtype=np.int32)
            # assign article_id by majority vote
            if article_id_occurences.shape[0] > 1:
                num_ambiguous += 1
                assign_index = np.argmax(article_id_occurences)
                assign_id = unique_article_ids[int(assign_index)]
                tr_article_ids.append(assign_id)
                logger.debug(f"\tTextRegion {text_region.id}: "
                             f"assign article_id '{assign_id}' (from {unique_article_ids})")
            else:
                tr_article_ids.append(unique_article_ids[0])
        overall_ambiguous += num_ambiguous
        logger.debug(f"\t{num_ambiguous}/{len(text_regions)} text regions contained textlines of differing article_ids")

        # format article ids
        final_article_ids = []
        for a_id in tr_article_ids:
            if a_id[0] == "a" and a_id[1] != "_":
                a_id = "a_" + a_id[1:]
            final_article_ids.append(a_id)

        # build and overwrite (article) relations
        relations = build_relations(final_article_ids, [tr.id for tr in text_regions])
        page.set_relations(relations, overwrite=True)
        if overwrite:
            page.write_page_xml(page_path)
        else:
            page_path = Path(page_path).parent / (Path(page_path).stem + "_relations.xml")
            page.write_page_xml(page_path)
        logger.info(f"\tWrote update relations to {page_path}")
    logger.info(f"Overall there were {overall_ambiguous} text regions containing textlines of differing article_ids")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--xml_list', type=str, help="lst file containing pageXML paths (exclusive with --xml_dir)")
    parser.add_argument('--xml_dir', type=str, help="directory containing pageXML paths (exclusive with --xml_list)")
    parser.add_argument('--overwrite', dest='overwrite', default=False, action='store_true')
    args = parser.parse_args()

    # XML variants
    if args.xml_dir and args.xml_list:
        logger.error(f"Only one XML input variant can be chosen at a time (either --xml_list or --xml_dir)!")
        exit(1)
    if not args.xml_dir and not args.xml_list:
        logger.error(f"Either --xml_list or --xml_dir is needed!")
        exit(1)
    if args.xml_dir:
        # xml_path = find_dirs("page", root=args.xml_dir)[0]
        # xml_paths = [os.path.join(xml_path, file_path) for file_path in glob.glob1(xml_path, '*.xml')]
        xml_paths = find_paths(root=args.xml_dir)
        logger.info(f"Using XML directory '{set([str(Path(path).parent) for path in xml_paths])}'")
    else:  # args.xml_list
        xml_paths = [path.rstrip() for path in open(args.xml_list, "r")]
        logger.info(f"Using XML list '{args.xml_list}'")

    # Run
    update_article_relations(xml_paths, args.overwrite)
