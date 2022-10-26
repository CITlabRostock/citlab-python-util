from pathlib import Path
from argparse import ArgumentParser
from tqdm import tqdm
from citlab_python_util.parser.xml.page.page import Page
from citlab_article_separation.gnn.input.feature_generation import discard_text_regions_and_lines as discard_regions
from citlab_python_util.logging.custom_logging import setup_custom_logger

logger = setup_custom_logger(__name__, level="debug")


def find_paths(root=".", ending="xml", exclude=None):
    results = []
    for path in Path(root).rglob(f'*.{ending}'):
        results.append(str(path))
    if exclude:
        for ex in exclude.split(","):
            results = [res for res in results if ex not in res]
    return results


def run(page_path_list, overwrite):
    cont = True
    for page_path in tqdm(page_path_list):
        if "nfp_19330701_006" in page_path:
            cont = False
        if cont:
            continue

        logger.info(f"Updating {page_path}...")
        page = Page(page_path)

        text_regions = page.get_text_regions()

        for text_region in text_regions:
            # text_region_nd = page.get_child_by_id(page.page_doc, text_region.id)
            text_lines = []
            for text_line in text_region.text_lines:
                text_line_nodes = page.get_child_by_id(page.page_doc, text_line.id)
                # duplicate found
                if len(text_line_nodes) > 1:
                    logger.debug(f"\tFound {len(text_line_nodes)} duplicate text lines for id {text_line.id}")
                    if len(text_line_nodes) >= 3:
                        raise Exception(f"Expected at most two text lines with the same id, but found "
                                        f"{len(text_line_nodes)}.")
                    # check which one is the duplicate (has no text region ancestor)
                    line1 = text_line_nodes[0]
                    line1_has_region = bool(page.get_ancestor_by_name(line1, "TextRegion"))
                    line2 = text_line_nodes[1]
                    line2_has_region = bool(page.get_ancestor_by_name(line2, "TextRegion"))
                    if line1_has_region and not line2_has_region:
                        duplicate = line2
                    elif line2_has_region and not line1_has_region:
                        duplicate = line1
                        # set article id only if the duplicate was line1, otherwise the article id was already correct
                        article_id = page.parse_custom_attr(duplicate.get("custom"))["structure"]["id"]
                        text_line.set_article_id(article_id)
                    else:
                        raise Exception(f"Can't correctly determine duplicate text line.")
                    # remove duplicate
                    page.remove_page_xml_node(duplicate)
                # aggregate (partly updated) text lines
                text_lines.append(text_line)
            # overwrite text lines in text region
            page.set_text_lines(text_region, text_lines, overwrite=True)

        # overwrite text regions
        # (do this after the text lines, so we also catch duplicates of text regions that get discarded)
        text_regions, _ = discard_regions(text_regions)
        page.set_text_regions(text_regions, overwrite=True)

        # save page
        # if overwrite:
        #     page.write_page_xml(page_path)
        # else:
        #     page_path = Path(page_path).parent / (Path(page_path).stem + "_removed.xml")
        #     page.write_page_xml(page_path)
        # logger.info(f"\tWrote page with removed incorrect regions and lines to {page_path}")


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('--xml_list', type=str, help="lst file containing pageXML paths (exclusive with --xml_dir)")
    parser.add_argument('--xml_dir', type=str, help="directory containing pageXML paths (exclusive with --xml_list)")
    parser.add_argument('--overwrite', dest='overwrite', default=False, action='store_true',
                        help="Whether to overwrite the pageXML files or save new ones.")
    args = parser.parse_args()

    # XML variants
    if args.xml_dir and args.xml_list:
        logger.error(f"Only one XML input variant can be chosen at a time (either --xml_list or --xml_dir)!")
        exit(1)
    if not args.xml_dir and not args.xml_list:
        logger.error(f"Either --xml_list or --xml_dir is needed!")
        exit(1)
    if args.xml_dir:
        xml_paths = find_paths(root=args.xml_dir)
        logger.info(f"Using XML directory '{set([str(Path(path).parent) for path in xml_paths])}'")
    else:  # args.xml_list
        xml_paths = [path.rstrip() for path in open(args.xml_list, "r")]
        logger.info(f"Using XML list '{args.xml_list}'")

    run(xml_paths, args.overwrite)
