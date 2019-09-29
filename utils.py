from datetime import datetime
from itertools import chain
from operator import itemgetter
import os
import re

from dateutil import parser as dparser
from more_itertools import groupby_transform

from CLIppy import get_from_file


DATETIME_SEP = ' @ '

error_str   = '[ {} ]'
# xed_out_str = '\e[9m{}\e[0m'


def clean_time(t):
    PATTERN = re.compile('m.*$', re.I)
    return re.sub(PATTERN, 'm', t) # ignore any junk after "{a,p}m"


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


def filter_past(datetimes, cutoff=None, sep=DATETIME_SEP):
    """Filter datetimes before cutoff

    :datetimes: list of strs ("date @ time") OR list of lists of strs
    :cutoff: datetime str (default: now)
    :returns: list of lists of (time) strs (or emptylist if past)
    """
    cutoff = datetime.now() if cutoff is None else dparser.parse(cutoff)

    if not datetimes:
        return []

    def clean_datetime(dt, sep=sep):
        date, time = dt.split(sep)
        return ', '.join((date, clean_time(time)))

    is_past = lambda dt: (
        dparser.parse(clean_datetime(dt))
        - cutoff
    ).total_seconds() < 0

    # date @ time -> time
    strftime = lambda dt: dt.split(DATETIME_SEP)[-1].replace(' ', '').lower()

    is_nested_list = isinstance(datetimes[0], list)

    return ([[strftime(dt) for dt in dts if not is_past(dt)]
             for dts in datetimes] if is_nested_list else
           [[strftime(dt)] # list of lists of "times"
            if not is_past(dt) else [] for dt in datetimes])


def combine_times(movie_names, movie_times):
    """Combine times for duplicate movienames

    :movie_names: [str]
    :movie_times: [[str], [str]]
    :returns: (list of movie names, list of lists of movie times)
    """
    assert len(movie_names) == len(movie_times), '{} != {}'.format(
        movie_name, movie_times)

    if not movie_names:
        return [], []

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


def index_into_days(days, date=None):
    """Get index into list of days that matches given `date`

    :days: list of days (strs that are parseable by datetime)
    :date: str (generally yyyy-mm-dd)
    :returns: int
    """
    date = dparser.parse(date) if date is not None else datetime.now()

    # get offset from day0 (which is prob today, but not sure about cutoff for today vs tomorrow)
    # this way, works for a list that says only: "wed, thu, fri, sat, sun, mon, tue, wed"
    iday = (date - dparser.parse(days[0])).days
    assert 0 <= iday <= len(days) - 1, '{} !<= {} !<= {}'.format(0, iday, len(days) - 1)

    try: # BUT, sometimes will skip a day
        assert (date - dparser.parse(days[iday])).days % 7 == 0 #, '{} != week multiple of {}'.format(days[iday], date)
    except(AssertionError):
        # then, fall back to direct indexing
        iday = [dparser.parse(day) for day in days].index(date)

    return iday


class NoMoviesException(Exception):
    pass
