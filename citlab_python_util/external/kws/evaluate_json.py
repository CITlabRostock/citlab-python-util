import json
import argparse
import re


def list_img_intersect(l1, l2):
    # check intersection over images
    img1 = [val[0] for val in l1]
    img2 = [val[0] for val in l2]
    img_intersect = [t for t in img1 if t in img2]
    # return images with baselines
    l1_intersect = [val for val in l1 if val[0] in img_intersect]
    l2_intersect = [val for val in l2 if val[0] in img_intersect]
    res = l1_intersect + l2_intersect
    return res


def get_kws_from_query(js, query):
    matched_kws = []
    for kw in js:
        if re.match(kw, query.upper()):
            matched_kws.append(kw)
    return matched_kws


def get_imgs_from_kw(js, kw):
    image_list = []
    for pos in js[kw]:
        bl = pos["bl"]
        image = pos["image"]
        image = re.sub(r"/storage", "", image)
        image = re.sub(r"/container.bin", "", image)
        image_list.append((image, bl))
    return image_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_to_json', help="Path to json file with kws results")
    parser.add_argument('--query', nargs='+', help="Keyword pattern to match. Supports AND/OR. E.g. 'Hello AND World'")
    args = parser.parse_args()

    with open(args.path_to_json, "r") as json_file:
        # load json file
        js = json.load(json_file)
        # print(json.dumps(js, indent=4, sort_keys=True))

        # extract keywords and corresponding matches
        # keywords = []
        kws_results = {}
        for kw in js["keywords"]:
            # keywords.append(kw["kw"])
            kws_results[kw["kw"]] = kw["pos"]

        # Analyze query
        query_list = []
        for query in args.query:
            # Look at non-special queries
            if query not in ('AND', 'OR', '(', ')'):
                query_img_matches = []
                # Get the matching keywords from the json
                matched_kws = get_kws_from_query(kws_results, query)
                for kw in matched_kws:
                    # Get the corresponding image results from the json
                    query_img_matches += get_imgs_from_kw(kws_results, kw)
                # print(f"{query:10} matches {kw:20} -- {query_img_matches[query]}")
                query_list.append(query_img_matches)
            else:
                query_list.append(query)

        # Evaluate boolean expression in query iteratively
        # The query is a list containing items and special expressions (booleans, brackets etc.)
        # TODO: How to evaluate brackets? (find last opening bracket + first closing bracket -> eval inbetween)
        while len(query_list) > 2:
            # Evaluate triple aRb (this only works when items and expressions alternate,
            # i.e. just OR/AND, no brackets/NOT, e.g. aRbRcRd...)
            sub_list = query_list[-3:]
            print(sub_list)
            if sub_list[1].upper() == 'AND':
                eval_list = list_img_intersect(sub_list[0], sub_list[2])
            elif sub_list[1].upper() == 'OR':
                eval_list = list(set(sub_list[0] + sub_list[2]))
            else:
                raise ValueError(f"Unkown keyword {sub_list[1]}")
            # Substitute triple aRb in query with the evaluation of it
            query_list = query_list[:-3]
            query_list.append(eval_list)
        # Result is a single list containing the images & baselines
        query_results = query_list[0]

        print(f"\nQuery {args.query} results in the following matches:\n")
        print(json.dumps(query_results, indent=2))

        # TODO: Write output textfile with [query, matching images, corresponding transcription (of lines or
        # TODO: baseline clusters)], optionally (maybe via --debug parameter?) display images with overlaid rectangle










