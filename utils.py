from datetime import datetime, timedelta
import os
import sys

from dateutil import parser as dparser


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
    BASE_FNAME = 'theaters'
    COMMENT_CHAR = '#'

    dirname = os.path.dirname(os.path.realpath(__file__))
    fname = '_'.join((BASE_FNAME, str(city)))

    with open(os.path.join(dirname, fname), 'r') as f:
        theaters = [l.strip().lower() for l in f
                    if not l.startswith(COMMENT_CHAR)]
    return theaters


def convert_date(date_in):
    """Convert string to uniform `datetime` string

    :date_in: str
    :returns: str ('YYYY-MM-DD')
    """
    D_CONVERSIONS = {
        'today': datetime.now(),
        'tomorrow': datetime.now() + timedelta(days=1),
        'tomorr': datetime.now() + timedelta(days=1),
        'tom': datetime.now() + timedelta(days=1),
        'mon': 'monday',
        'tues': 'tuesday',
        'wed': 'wednesday',
        'thurs': 'thursday',
        'fri': 'friday'
    }

    # if abbrev, uncompress for parser
    date_out = D_CONVERSIONS.get(date_in.lower(), date_in)

    try: # if str, convert to datetime
        date_out = dparser.parse(date_out)
    except(AttributeError, TypeError): # already datetime
        date_out = date_out
    except(ValueError):
        print("I don't recognize that date.. try again ?")
        sys.exit(0)

    return date_out.strftime('%Y-%m-%d')
