"""
    Metrics for evaluation
    @author: João Gabriel Melo Barbirato
"""


def precision(correct, incorrect, as_percent=False):
    """
    Classic binary class precision metric
    :param correct: number of correct predictions
    :param incorrect: number of incorrect predictions
    :param as_percent: percent return modifier
    :return: precision value
    """
    try:
        p = float(correct) / (correct + incorrect)
        return p if not as_percent else p * 100
    except ZeroDivisionError:
        return 0


def recall(correct, total, as_percent=False):
    """
    Classic binary class recall metric
    :param correct: number of correct predictions
    :param total: total of instances
    :param as_percent: percent return modifier
    :return: recall value
    """
    try:
        r = float(correct) / total
        return r if not as_percent else r * 100
    except ZeroDivisionError:
        return 0


def f_measure(correct, incorrect, total, as_percent=False):
    """
    Classic binary class F-measure metric
    :param correct: number of correct predictions
    :param incorrect: number of incorrect predictions
    :param total: total of instances
    :param as_percent: percent return modifier
    :return: F-measure value
    """
    _p = precision(correct, incorrect)
    _r = recall(correct, total)
    try:
        f = 2. * (_p * _r) / (_p + _r)
        return f if not as_percent else f * 100
    except ZeroDivisionError:
        return 0


def p_r_f_metrics(correct, incorrect, total, as_percent=False):
    """
    Classic binary class metrics
    :param correct: number of correct predictions
    :param incorrect: number of incorrect predictions
    :param total: total of instances
    :param as_percent: percent return modifier
    :return: Tuple with precision, recall and F-measure values
    """
    return precision(correct, incorrect, as_percent), \
        recall(correct, total, as_percent), f_measure(correct, incorrect, total, as_percent)
