import collections
import functools
import os
import random
import re
import matplotlib.pyplot as plt
from PIL import Image, ImageFile
from matplotlib import colors as mcolors
from matplotlib.collections import PolyCollection
from citlab_python_util.geometry.polygon import Polygon
from citlab_python_util.parser.xml.page import page_constants
from citlab_python_util.parser.xml.page.page import Page
from citlab_python_util.logging.custom_logging import setup_custom_logger
from citlab_python_util.io.path_util import get_page_from_img_path

logger = setup_custom_logger(__name__, level="info")

DEFAULT_COLOR = "#000000"
COLORS = ["#1CE6FF", "#FF34FF", "#008941", "#006FA6", "#A30059", "#FFFF00", "#00846F",
          "#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
          "#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
          "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
          "#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#FF4A46",
          "#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
          "#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
          "#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",

          "#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
          "#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
          "#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
          "#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
          "#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
          "#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
          "#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
          "#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58"]
COLORS *= 5


# Two interfaces supported by matplotlib:
#   1. object-oriented interface using axes.Axes and figure.Figure objects
#   2. based on MATLAB using a state-based interface
# "In general, try to use the object-oriented interface over the pyplot interface"


def add_image(axes, path, height=None, width=None):
    """Add the image given by ``path`` to the plot ``axes``.

    :param axes: represents an individual plot
    :param path: path to the image
    :param height: (optional) resize image if both height and width are given
    :param width: (optional) resize image if both height and width are given
    :return: mpimg.AxesImage
    """
    try:
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        img = Image.open(path)
        if height is not None and width is not None:
            img = img.resize((int(height), int(width)), 0)
        img = img.convert("RGB")
        return axes.imshow(img)
    except ValueError:
        logger.error("Can't add image to the plot. Check if '{}' is a valid path.".format(path))


def add_polygons(axes, poly_list, color=DEFAULT_COLOR, closed=False, linewidth=1.2, alpha=1.0, filled=False):
    """poly_list = [[(x1,y1), (x2,y2), ... , (xN,yN)], ... , [(u1,v1), (u2, v2), ... , (uM, vM)]]
    else if poly_list if of type Polygon convert it to that form."""
    if check_type(poly_list, [Polygon]):
        poly_list = [list(zip(poly.x_points, poly.y_points)) for poly in poly_list]
    try:
        if filled:
            alpha = 0.5
            facecolors = color
        else:
            facecolors = "None"
        poly_collection = PolyCollection(poly_list, closed=closed, edgecolors=color, facecolors=facecolors,
                                         linewidths=linewidth, alpha=alpha)
        return axes.add_collection(poly_collection)
    except ValueError:
        raise ValueError(f"Could not handle the input polygon format {poly_list}")


def toggle_view(event, views):
    """Switch between different views in the current plot by pressing the ``event`` key.

    :param event: the key event given by the user, various options available, e.g. to toggle the baselines
    :param views: dictionary of different views given by name:object pairs
    :type event: matplotlib.backend_bases.KeyEvent
    :return: None
    """

    # toggle polygons function
    def _toggle_polys(event_key, poly_collection_name):
        if event.key == event_key and poly_collection_name in views:
            is_same_visibility = all(
                [polygon.get_visible() if views[poly_collection_name][0].get_visible() else not (polygon.get_visible())
                 for polygon in views[poly_collection_name]])
            if is_same_visibility:
                for polygon in views[poly_collection_name]:
                    is_visible = polygon.get_visible()
                    polygon.set_visible(not is_visible)
            else:
                for polygon in views[poly_collection_name]:
                    polygon.set_visible(True)
            plt.draw()

    if event.key == 'i' and "image" in views:
        is_visible = views["image"].get_visible()
        views["image"].set_visible(not is_visible)
        plt.draw()
    _toggle_polys('b', 'baselines')
    _toggle_polys('p', 'surr_polys')
    _toggle_polys('w', 'word_polys')
    _toggle_polys('r', 'regions')
    _toggle_polys('1', page_constants.sTEXTREGION)
    _toggle_polys('1', page_constants.TextRegionTypes.sHEADING)
    _toggle_polys('2', page_constants.sSEPARATORREGION)
    _toggle_polys('3', page_constants.sGRAPHICREGION)
    _toggle_polys('4', page_constants.sIMAGEREGION)
    _toggle_polys('5', page_constants.sTABLEREGION)
    _toggle_polys('6', page_constants.sADVERTREGION)
    _toggle_polys('7', page_constants.sLINEDRAWINGREGION)
    _toggle_polys('7', page_constants.sCHARTREGION)
    _toggle_polys('7', page_constants.sCHEMREGION)
    _toggle_polys('7', page_constants.sMATHSREGION)
    _toggle_polys('7', page_constants.sMUSICREGION)
    _toggle_polys('8', page_constants.sNOISEREGION)
    _toggle_polys('9', page_constants.sUNKNOWNREGION)

    if event.key == 'n':
        plt.close()

    if event.key == 'q':
        print("Terminate..")
        exit(0)

    if event.key == 'h':
        print("Usage:\n"
              "\ti: toggle image\n"
              "\tb: toggle baselines\n"
              "\tp: toggle surrounding polygons\n"
              "\tw: toggle world polygons\n"
              "\tr: toggle all regions\n"
              "\t\t1: TextRegion\n"
              "\t\t2: SeparatorRegion\n"
              "\t\t3: GraphicRegion\n"
              "\t\t4: ImageRegion\n"
              "\t\t5: TableRegion\n"
              "\t\t6: AdvertRegion\n"
              "\t\t7: LineDrawingRegion / ChartRegion / ChemRegion / MathsRegion / MusicRegion\n"
              "\t\t8: NoiseRegion\n"
              "\t\t9: UnknownRegion\n"
              "\tn: next image\n"
              "\tq: quit\n"
              "\th: show this help")
    else:
        return


def check_type(lst, t):
    """Checks if all elements of list ``lst`` are of one of the types in ``t``.

    :param lst: list to check
    :param t: list of types that the elements in list should have
    :return: Bool
    """
    for el in lst:
        if type(el) not in t:
            return False
    return True


def compare_article_ids(a, b):
    if a is None and b is None:
        return 0
    elif a is None:
        return 1
    elif b is None:
        return -1
    elif int(a[1:]) < int(b[1:]):
        return -1
    elif int(a[1:]) == int(b[1:]):
        return 0
    else:
        return 1


def plot_ax(ax=None, img_path='', baselines_list=None, surr_polys=None, bcolors=None, region_dict_poly=None,
            rcolors=None, word_polys=None, plot_legend=False, fill_regions=False, height=None, width=None):
    if rcolors is None:
        rcolors = {}
    if region_dict_poly is None:
        region_dict_poly = {}
    if bcolors is None:
        bcolors = []
    if surr_polys is None:
        surr_polys = []
    if baselines_list is None:
        baselines_list = []
    if word_polys is None:
        word_polys = []
    if ax is None:
        fig, ax = plt.subplots(figsize=(16, 9))  # type: # (plt.Figure, plt.Axes)
        fig.canvas.set_window_title(img_path)
    views = collections.defaultdict(list)

    # # Maximize plotting window
    # mng = plt.get_current_fig_manager()
    # mng.resize(*mng.window.maxsize())
    # # mng.full_screen_toggle()

    try:
        img_plot = add_image(ax, img_path, height=height, width=width)
        views.update({"image": img_plot})
    except IOError as err:
        logger.error(f"Can't display image given by path: {img_path} - {err}")

    if len(bcolors):
        assert len(bcolors) >= len(baselines_list), f"There should be at least {len(baselines_list)}" \
                                                    f" colors but just got {len(bcolors)}"
    else:
        bcolors = [DEFAULT_COLOR] * len(baselines_list)

    if baselines_list:
        article_collection = []
        for i, blines in enumerate(baselines_list):
            baseline_collection = add_polygons(ax, blines, bcolors[i], closed=False)
            article_collection.append(baseline_collection)
            if bcolors[i] == DEFAULT_COLOR:
                baseline_collection.set_label("None")
            else:
                baseline_collection.set_label("a-id " + str(i + 1))
            views['baselines'].append(baseline_collection)
        if plot_legend:
            # Add article ids to the legend
            # TODO: Sometimes there are too many articles to display -> possibility to scroll?!
            # article_collection = [coll for coll in ax.collections if coll.get_label().startswith("a-id")]
            ax.legend(article_collection, [coll.get_label() for coll in article_collection],
                      bbox_to_anchor=[1.0, 1.0], loc="upper left")

    if surr_polys:
        surr_poly_collection = add_polygons(ax, surr_polys, DEFAULT_COLOR, closed=True)
        surr_poly_collection.set_visible(False)
        views['surr_polys'] = [surr_poly_collection]

    if word_polys:
        word_poly_collection = add_polygons(ax, word_polys, DEFAULT_COLOR, closed=True)
        word_poly_collection.set_visible(False)
        views['word_polys'] = [word_poly_collection]

    if region_dict_poly:
        for region_name, regions in region_dict_poly.items():
            region_collection = add_polygons(ax, regions, rcolors[region_name], closed=True, filled=fill_regions)
            region_collection.set_visible(False)
            views[region_name] = [region_collection]
            views['regions'].append(region_collection)

    # Toggle baselines with "b", image with "i", surrounding polygons with "p"
    plt.connect('key_press_event', lambda event: toggle_view(event, views))


def plot_pagexml(page, path_to_img, ax=None, plot_article=True, plot_legend=False, fill_regions=False,
                 use_page_image_resolution=False):
    if type(page) == str:
        page = Page(page)
    assert type(page) == Page, f"Type must be Page, got {type(page)} instead."

    # get baselines based on the article id
    article_dict = page.get_article_textline_dict()
    if not article_dict:
        bcolors = []
        blines_list = []
    else:
        unique_ids = sorted(set(article_dict.keys()))  # , key=functools.cmp_to_key(compare_article_ids))
        if None in unique_ids:
            article_colors = dict(zip(unique_ids, COLORS[:len(unique_ids) - 1] + [DEFAULT_COLOR]))
        else:
            article_colors = dict(zip(unique_ids, COLORS[:len(unique_ids)]))
        if plot_article:
            bcolors = [article_colors[id] for id in unique_ids]
        else:
            bcolors = [DEFAULT_COLOR] * len(article_dict)
        blines_list = [[textline.baseline.points_list for textline in article_dict[id] if textline.baseline]
                       for id in unique_ids]

    # import random
    # random.seed(1337)
    # random.shuffle(bcolors)

    # elif None in article_dict:
    #     if plot_article:
    #         bcolors = COLORS[:len(article_dict) - 1] + [DEFAULT_COLOR]
    #     else:
    #         bcolors = [DEFAULT_COLOR] * len(article_dict)
    #
    #     blines_list = [[tline.baseline.points_list for tline in tlines if tline.baseline]
    #                    for (a_id, tlines) in article_dict.items() if a_id is not None] \
    #                   + [[tline.baseline.points_list for tline in article_dict[None] if tline.baseline]]
    # else:
    #     if plot_article:
    #         bcolors = COLORS[:len(article_dict)]
    #     else:
    #         bcolors = [DEFAULT_COLOR] * len(article_dict)
    #     blines_list = [[tline.baseline.points_list for tline in tlines] for tlines in article_dict.values()]

    region_dict = page.get_regions()
    if not region_dict:
        rcolors = {}
        region_dict_polygons = {}
    else:
        rcolors = {page_constants.sTEXTREGION: "darkgreen", page_constants.sSEPARATORREGION: "darkviolet",
                   page_constants.sGRAPHICREGION: "darkcyan", page_constants.sIMAGEREGION: "darkblue",
                   page_constants.sTABLEREGION: "darkorange", page_constants.sADVERTREGION: "yellow",
                   page_constants.sLINEDRAWINGREGION: "salmon", page_constants.sCHARTREGION: "brown",
                   page_constants.sCHEMREGION: "navy", page_constants.sMATHSREGION: "crimson",
                   page_constants.sNOISEREGION: "darkkhaki", page_constants.sMUSICREGION: "firebrick",
                   page_constants.sUNKNOWNREGION: "darkorchid", page_constants.TextRegionTypes.sHEADING: "crimson"}
        region_dict[page_constants.sTEXTREGION] = page.get_text_regions(page_constants.TextRegionTypes.sPARAGRAPH)
        region_dict[page_constants.TextRegionTypes.sHEADING] = page.get_text_regions(
            page_constants.TextRegionTypes.sHEADING)
        region_dict_polygons = {region_name: [region.points.points_list for region in regions] for region_name, regions
                                in region_dict.items()}

    # get surrounding polygons
    textlines = page.get_textlines()
    surr_polys = [tl.surr_p.points_list for tl in textlines if (tl and tl.surr_p)]

    words = page.get_words()
    word_polys = [word.surr_p.points_list for word in words if (word and word.surr_p)]

    # # Maximize plotting window
    # mng = plt.get_current_fig_manager()
    # mng.resize(*mng.window.maxsize())

    if use_page_image_resolution:
        page_height, page_width = page.get_image_resolution()
    else:
        page_height = page_width = None

    plot_ax(ax, path_to_img, blines_list, surr_polys, bcolors, region_dict_polygons, rcolors, word_polys, plot_legend,
            fill_regions=fill_regions, height=page_height, width=page_width)


def plot_list(img_lst, hyp_lst, gt_lst=None, plot_article=True, plot_legend=False, force_equal_names=True,
              fill_regions=False, use_page_image_resolution=False):
    if not img_lst:
        raise IOError(f"No valid image list found: '{img_lst}'.")
    if not img_lst.endswith((".lst", ".txt")) and not os.path.isfile(img_lst):
        raise IOError(f"Image list doesn't have a valid extension or doesn't exist: '{img_lst}'.")
    if not hyp_lst:
        raise IOError(f"No valid hypothesis list found: '{hyp_lst}'.")
    if not hyp_lst.endswith((".lst", ".txt")) and not os.path.isfile(hyp_lst):
        raise IOError(f"Hypothesis list doesn't have a valid extension or doesn't exist: '{hyp_lst}'.")
    # if not gt_lst:
    #     raise IOError(f"No valid groundtruth list found: '{gt_lst}'")
    # elif not gt_lst.endswith((".lst", ".txt")) and not os.path.isfile(gt_lst):
    #     raise IOError(f"Groundtruth list doesn't have a valid extension or doesn't exist: '{gt_lst}'.")

    if gt_lst is not None:
        with open(img_lst, 'r') as img_paths:
            with open(hyp_lst, 'r') as hyp_paths:
                with open(gt_lst, 'r') as gt_paths:
                    for img_path, hyp_path, gt_path in zip(img_paths, hyp_paths, gt_paths):
                        img_path = img_path.strip()
                        hyp_path = hyp_path.strip()
                        gt_path = gt_path.strip()
                        if not img_path.endswith((".jpg", ".jpeg", ".png", ".tif")) and os.path.isfile(img_path):
                            logger.warning(f"File '{img_path}' does not have a valid image extension "
                                           f"(jpg, jpeg, png, tif) or is not a file, skipping.")
                            continue
                        if force_equal_names:
                            hyp_page = os.path.basename(hyp_path)
                            gt_page = os.path.basename(gt_path)
                            img_name = os.path.basename(img_path)
                            img_wo_ext = str(img_name.rsplit(".", 1)[0])
                            if hyp_page != img_wo_ext + ".xml":
                                logger.warning(f"Hypothesis: Filenames don't match: "
                                               f"'{hyp_page}' vs. '{img_wo_ext + '.xml'}', skipping.")
                                continue
                            if gt_page != img_wo_ext + ".xml":
                                logger.warning(f"Groundtruth: Filenames don't match: "
                                               f"'{gt_page}' vs. '{img_wo_ext + '.xml'}', ignoring.")
                                fig, ax = plt.subplots()
                                fig.canvas.set_window_title(img_path)
                                ax.set_title('Hypothesis')

                                # Should be save to use without opening all images of the loop in a different window
                                # The program should wait until one window is closed
                                plot_pagexml(hyp_path, img_path, ax, plot_article, plot_legend, fill_regions,
                                             use_page_image_resolution)
                            else:
                                fig, (ax1, ax2) = plt.subplots(1, 2)
                                fig.canvas.set_window_title(img_path)
                                ax1.set_title('Hypothesis')
                                ax2.set_title('Groundtruth')

                                plot_pagexml(hyp_path, img_path, ax1, plot_article, plot_legend, fill_regions,
                                             use_page_image_resolution)
                                plot_pagexml(gt_path, img_path, ax2, plot_article, plot_legend, fill_regions,
                                             use_page_image_resolution)

                        else:
                            fig, (ax1, ax2) = plt.subplots(1, 2)
                            fig.canvas.set_window_title(img_path)
                            ax1.set_title('Hypothesis')
                            ax2.set_title('Groundtruth')

                            plot_pagexml(hyp_path, img_path, ax1, plot_article, plot_legend, fill_regions,
                                         use_page_image_resolution)
                            plot_pagexml(gt_path, img_path, ax2, plot_article, plot_legend, fill_regions,
                                         use_page_image_resolution)

                        plt.show()

    else:
        with open(img_lst, 'r') as img_paths:
            with open(hyp_lst, 'r') as hyp_paths:
                for img_path, hyp_path in zip(img_paths, hyp_paths):
                    img_path = img_path.strip()
                    hyp_path = hyp_path.strip()
                    if not img_path.endswith((".jpg", ".jpeg", ".png", ".tif")) and os.path.isfile(img_path):
                        logger.warning(f"File '{img_path}' does not have a valid image extension "
                                       f"(jpg, jpeg, png, tif) or is not a file, skipping.")
                        continue
                    if force_equal_names:
                        hyp_page = os.path.basename(hyp_path)
                        img_name = os.path.basename(img_path)
                        img_wo_ext = str(img_name.rsplit(".", 1)[0])
                        if hyp_page != img_wo_ext + ".xml":
                            logger.warning(f"Hypothesis: Filenames don't match: "
                                           f"'{hyp_page}' vs. '{img_wo_ext + '.xml'}', skipping.")
                            continue
                    fig, ax = plt.subplots()
                    fig.canvas.set_window_title(img_path)

                    ax.set_title('Hypothesis')

                    plot_pagexml(hyp_path, img_path, ax, plot_article, plot_legend, fill_regions,
                                 use_page_image_resolution)
                    # save_path = "/home/johannes/devel/projects/tf_rel/debug_output/DEL_PICS/Koeln112_alpha_gt_BERTnew_merge/"
                    # save_path += os.path.splitext(os.path.basename(hyp_path))[0] + ".jpg"
                    # plt.axis('off')
                    # plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=300)
                    # print(f"Saved figure {save_path}")
                    # plt.close(fig)
                    plt.show()


def plot_folder(path_to_folder, plot_article=True, plot_legend=False, fill_regions=False):
    file_paths = []
    try:
        for root, dirs, files in os.walk(path_to_folder, followlinks=True):
            file_paths += [os.path.join(root, file) for file in files]
    except StopIteration:
        raise ValueError(f"No directory {path_to_folder} found.")
    if not any(fname.endswith((".jpg", ".png", ".tif")) for fname in file_paths):
        raise ValueError("There are no images (jpg, png, tif) to be found, choose another folder.")

    # Iterate over the images
    for img_path in [path for path in file_paths if path.endswith((".jpg", ".png", ".tif"))]:
        page_path = get_page_from_img_path(img_path)
        plot_pagexml(Page(page_path), img_path, plot_article=plot_article, plot_legend=plot_legend,
                     fill_regions=fill_regions)
        plt.show()


if __name__ == '__main__':
    # Example for plotting folder
    # path_to_folder = "/home/johannes/devel/data/NewsEye_GT/AS_BC/NewsEye_BNF_183_updated_gt"
    # plot_folder(path_to_folder, plot_article=True, plot_legend=False, fill_regions=False)

    # Example for plotting list (GT list can be omitted)
    path_to_img_lst = "/home/johannes/devel/projects/tf_rel/lists/koeln112/koeln_112_images.lst"
    path_to_hyp_lst = "/home/johannes/devel/projects/tf_rel/lists/koeln112/koeln112_alpha_gt_3bbBERTnew_cluster_merge.lst"
    path_to_gt_lst = None
    # path_to_gt_lst = "./test/resources/newseye_as_test_data/gt_xml_paths.lst"
    plot_list(path_to_img_lst, path_to_hyp_lst, path_to_gt_lst, plot_article=True, force_equal_names=False,
              use_page_image_resolution=True)

    # # Example for plotting PAGE file
    # path_to_xml = "/home/johannes/devel/19200115_1-0001_clustering.xml"
    # path_to_img = "/home/johannes/devel/19200115_1-0001.jpg"
    # plot_pagexml(Page(path_to_xml), path_to_img, plot_article=True, plot_legend=False)
    # save_path = "/home/johannes/devel/nlf.png"
    # plt.axis('off')
    # plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=300)
    # plt.show()
