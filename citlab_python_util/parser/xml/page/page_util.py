class PageXmlException(Exception):
    pass


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


def reverse_dict(dictionary: dict) -> dict:
    """
    Inverts a dictionary from key -> values to value -> key. Values are converted to lists and the method also
    handles duplicate values. The method is invertible, i.e. mydict = reverse_dict(reverse_dict(my_dict))
    """
    rev_dict = dict()
    for key, value in dictionary.items():
        if not isinstance(value, (list, tuple)):
            value = [value]
        for val in value:
            rev_dict[val] = rev_dict.get(val, [])
            rev_dict[val].append(key)
    return rev_dict
