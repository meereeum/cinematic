from datetime import datetime
from itertools import chain
from operator import itemgetter
import os

from dateutil import parser as dparser
from more_itertools import groupby_transform

from CLIppy import get_from_file


error_str='[ {} ]'


def filter_movies(movie_names, movie_times):
    """Filter movies that have no corresponding times

    :movie_names: [str]
    :movie_times: [[str], [str]]
    :returns: (list of movie names, list of lists of movie times)
    """
    is_empty = lambda lst: (all(map(is_empty, lst)) if isinstance(lst, list)
                            else False) # check if (nested) list is empty

    movie_names, movie_times = (([], []) if is_empty(movie_times) else
                                zip(*((name, time) for name, time in
                                      zip(movie_names, movie_times) if time)))
    return list(movie_names), list(movie_times)


def filter_past(datetimes, cutoff=None):
    """Filter datetimes before cutoff

    :datetimes: list of strs ("date @ time")
    :cutoff: datetime str (default: now)
    :returns: list of lists of strs (or emptylist if past)
    """
    cutoff = datetime.now() if cutoff is None else dparser.parse(cutoff)

    is_past = lambda dt: (
        dparser.parse(dt.replace('@', ',')) - cutoff).total_seconds() < 0

    # date @ time -> time
    strftime = lambda dt: dt.split(' @ ')[1].replace(' ', '').lower()

    return [[strftime(dt)] # list of lists of "times"
            if not is_past(dt) else [] for dt in datetimes]


def combine_times(movie_names, movie_times):
    """Combine times for duplicate movienames

    :movie_names: [str]
    :movie_times: [[str], [str]]
    :returns: (list of movie names, list of lists of movie times)
    """
    movie_names, movie_times = zip(
        *[(k, list(chain.from_iterable(g))) for k,g in groupby_transform(
            zip(movie_names, movie_times), itemgetter(0), itemgetter(1))])
    return list(movie_names), list(movie_times)


def filter_by_rating(movie_names, movie_times, movie_ratings, threshold=0):
    """Filter movies by minimum rating

    :movie_names: [strs]
    :movie_times: [[strs]]
    :movie_ratings: [floats]
    :threshold: float [0, 1] or % (1, 100]
    :returns: tuple(movie names, movie times, movie ratings)
    """
    threshold = threshold / 100 if threshold > 1 else threshold # % -> float

    tuple_in = (movie_names, movie_times, movie_ratings)
    tuple_out = (zip(*((name, time, rating) for name, time, rating in zip(*tuple_in)
                       if rating >= threshold or rating < 0)) # only if above threshold or rating not found
                 if threshold > 0 else tuple_in) # else, don't bother to filter
    tuple_out = tuple(tuple_out)
    tuple_out = (tuple_out if tuple_out else ((), (), ())) # don't return empty tuple if all filtered out

    return tuple_out


def get_theaters(city):
    """Get list of theaters by desired `city` from txt file

    :city: str
    :returns: list of theaters (str)
    """
    dirname = os.path.dirname(os.path.realpath(__file__))
    return get_from_file(suffix=city, prefix='theaters', dirname=dirname)
