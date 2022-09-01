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


def inverse_dict(dictionary):
    """
    Inverts a dictionary from key -> values to value -> key. Values are converted to lists and the method also
    handles duplicate values. The method is invertible, i.e. mydict = inverse_dict(inverse_dict(my_dict)).
    Since the original values become the new keys, the method only works for dictionaries whose values are hashable.
    """
    rev_dict = dict()
    for key, value in dictionary.items():
        if not isinstance(value, (list, tuple)):
            value = [value]
        for val in value:
            try:
                rev_dict[val] = rev_dict.get(val, [])
                rev_dict[val].append(key)
            except TypeError:
                print(f"Can not inverse dictionary with unhashable values: {val}")
                return None
    for key, value in rev_dict.items():
        if len(value) == 1:
            rev_dict[key] = value[0]
    return rev_dict
