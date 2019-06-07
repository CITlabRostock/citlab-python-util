def f_measure(precision, recall):
    """ Computes the F1-score for given precision and recall values.

    :param precision: float
    :param recall: float
    :return: F1-score (or 0.0 if both precision and recall are 0.0)
    """
    assert precision.dtype == float and recall.dtype == float, "precision and recall have to be floats"

    if precision == 0 and recall == 0:
        return 0.0
    else:
        return 2.0 * precision * recall / (precision + recall)
