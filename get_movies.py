import argparse
from itertools import zip_longest
import re

from CLIppy import convert_date, pprint_header_with_lines

from ratings import get_ratings
from scrapers import get_movies_google, get_movies_film_noir, get_movies_metrograph, get_movies_videology
from utils import filter_by_rating, get_theaters


def get_movies(theater, date):
    """Get movie names and times

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    D_ACTIONS = {
        'film noir': get_movies_film_noir,
        'metrograph': get_movies_metrograph,
        'videology': get_movies_videology
    }
    action = D_ACTIONS.get(theater, get_movies_google) # default to google search
    return action(theater, date)


def print_movies(theater, movie_names, movie_times, movie_ratings=[], sorted_=False):
    """Pretty-print movies

    :theater: str
    :movie_names: [strs]
    :movie_times: [strs]
    :movie_ratings: [floats]
    :sorted_: sort movies by descending rating ?
    """
    SPACER = 2
    SEP_CHAR = '|'

    PATTERN = re.compile(', \[') # match movie type in timelist

    theater_space = len(theater)
    try:
        col_space = len(max(movie_names, key=len))
    except(ValueError): # search found no movies
        print('skipping {}...'.format(theater))
        return

    def to_pprint_str(name, times, rating, with_rating=True):
        if with_rating:
            # tuple (str, strfmt)
            t_rating_fmt = ((rating, '.0%') if rating > 0 else
                            ('?', '^3')) # no rating found
            # TODO different fmt for IMDb ?
            rating_str = '{:7}'.format('({:{}})'.format(*t_rating_fmt))
        else:
            rating_str = ''

        time_str = re.sub(PATTERN, '  [', ', '.join(times)) # reformat movie type

        return '{}{:{}}{:^{}}{}'.format(rating_str,
                                        name, col_space,
                                        SEP_CHAR, SPACER * 2 + len(SEP_CHAR),
                                        time_str)

    with_rating = (movie_ratings != [])
    movie_strs = [to_pprint_str(name, times, rating, with_rating=with_rating)
                  for name, times, rating in zip_longest(
                          movie_names, movie_times, movie_ratings)]
    movie_strs = ([movie_str for _, movie_str in sorted(
        zip(movie_ratings, movie_strs), reverse=True)] # sort best -> worst
                  if sorted_ else movie_strs)

    pprint_header_with_lines(theater.upper(), movie_strs)


def get_parser():
    parser = argparse.ArgumentParser(description=(''))
    parser.add_argument('city and/or date', nargs='*', default=[None],
                        help='(default: nyc today)')
    parser.add_argument('--simple', action='store_true',
                        help='display without ratings? (default: false)')
    parser.add_argument('--sorted', action='store_true',
                        help='sort by rating? (default: false)')
    parser.add_argument('--filter-by', type=float, default=0,
                        help='minimum rating threshold (default: 0)')
    return parser


if __name__ == '__main__':
    # defaults
    CITY = 'nyc'
    DATE = 'today'

    # parse args
    args = get_parser().parse_args()

    city_date = args.__getattribute__('city and/or date') # b/c spaces
    city_date.append(DATE) # pad with default
    maybe_city, maybe_date, *_ = city_date

    try:
        city = maybe_city
        theaters = get_theaters(city)
        date = maybe_date
    except(FileNotFoundError): # date rather than city
        city = CITY
        theaters = get_theaters(city)
        date = maybe_city if maybe_city else DATE

    # do stuff
    kwargs = {
        'date': convert_date(date)
    }
    d_cached = {}

    for theater in theaters:
        print('')
        kwargs['theater'] = theater

        movie_names, movie_times = get_movies(**kwargs)

        if args.filter_by > 0 or not args.simple:
            movie_ratings, d_cached = get_ratings(movie_names, d_cached)
        else:
            movie_ratings = []

        print_movies(theater, *filter_by_rating(movie_names,
                                                movie_times,
                                                movie_ratings,
                                                args.filter_by),
                     sorted_=args.sorted)
    print('')
