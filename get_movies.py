import argparse
from functools import partial, reduce
from itertools import zip_longest
import operator
import re

from CLIppy import convert_date, get_from_file, pprint_header_with_lines

from scrapers import *
from utils import filter_by_rating, get_theaters, NoMoviesException

# TODO fail gracefully around some central fn


def get_movies(theater, date, **kwargs):
    """Get movie names and times

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    theater = theater.lower()

    D_ACTIONS = dict(
        # bos:
        brattle_theatre=get_movies_brattle,
        coolidge_corner=get_movies_coolidge,
        harvard_film_archive=get_movies_hfa,
        mfa_boston=get_movies_mfa,
        kendall_cinema=get_movies_landmark,
        somerville_theatre=get_movies_somerville,
        amc_boston_common=get_movies_amc,
        regal_fenway=get_movies_showtimes,
        # nyc:
        alamo_drafthouse_brooklyn=get_movies_alamo,
        angelika_film_center=get_movies_village_east_or_angelika,
        anthology=get_movies_anthology,
        bam_rose_cinemas=get_movies_bam,
        cinema_village=get_movies_cinema_village,
        cobble_hill_cinemas=get_movies_cobble_hill,
        # film_forum=get_movies_film_forum, # custom is slow - have to open headless => fall back to default
        film_noir=get_movies_film_noir,
        ifc=get_movies_ifc,
        loews_jersey_theater=get_movies_loews_theater,
        lincoln_center=get_movies_filmlinc,
        metrograph=get_movies_metrograph,
        moma=get_movies_moma,
        museum_of_the_moving_image=get_movies_momi,
        nitehawk=get_movies_nitehawk,
        nitehawk_prospect_park=get_movies_nitehawk,
        quad_cinema=get_movies_quad,
        syndicated_bk=get_movies_syndicated,
        ua_court_st=get_movies_showtimes,
        village_east_cinema=get_movies_village_east_or_angelika,
        #videology=get_movies_videology, # RIP
        # pgh:
        regent_square_theater=get_movies_pghfilmmakers,
        harris_theater=get_movies_pghfilmmakers,
        melwood_screening_room=get_movies_pghfilmmakers,
        the_manor=get_movies_manor,
        row_house_cinema=get_movies_rowhouse,
        the_waterfront=get_movies_amc
    )

    def fallback(*args, **kwargs):
        try:
            return get_movies_google(*args, **kwargs)    # default to google search
        except(NoMoviesException):
            return get_movies_showtimes(*args, **kwargs) # or, last ditch effort, showtimes.com search

    action = D_ACTIONS.get(theater.replace(' ', '_'), fallback)

    return action(theater, date)


def get_movies_from_file(f, **kwargs):
    """
    path/to/file -> list of movienames
    """
    movie_names = get_from_file(f=f)
    movie_times = [''] * len(movie_names)

    return movie_names, movie_times # appropriately sized list of empty strings


def print_movies(theater, movie_names, movie_times, movie_ratings=[], sorted_=False):
    """Pretty-print movies

    :theater: str
    :movie_names: [strs]
    :movie_times: [strs]
    :movie_ratings: [floats]
    :sorted_: sort movies by descending rating ?
    """
    if not movie_names: # search found no movies
        print(f'skipping {theater}...')
        return

    SPACER = 2
    SEP_CHAR = '|' if reduce(operator.add, movie_times) else '' # no SEP if no times (list of empty strs)

    PATTERN = re.compile(', \[') # match movie type in timelist

    theater_space = len(theater)
    col_space = len(max(movie_names, key=len))

    def to_pprint_str(name, times, rating, with_rating=True):
        if with_rating:
            # tuple (str, strfmt)
            t_rating_fmt = ((rating, '.0%') if rating > 0 else
                            ('?', '^3')) # no rating found
            # TODO different fmt for IMDb ?
            rating_str = '{:7}'.format('({:{}})'.format(*t_rating_fmt))
        else:
            rating_str = ''

        # time_str = re.sub(PATTERN, '  [', ', '.join(times)) # reformat movie type
        time_str = re.sub(PATTERN, '  [', ', '.join(('{:>7}'.format(t) # reformat movie type
                                                     for t in times))) # & align time spacing

        return f'{rating_str}{name:{col_space}}{SEP_CHAR:^{SPACER * 2 + len(SEP_CHAR)}}{time_str}'

    with_rating = (movie_ratings != [])
    sorted_ = sorted_ and with_rating

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
    parser.add_argument('-f', type=str, default=None, help='path/to/moviefile')
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

    moviefile = args.f
    if moviefile is not None: # from file

        theaters = [moviefile.split('_')[-1]]
        moviegetter = partial(get_movies_from_file, f=moviefile)

    else:                     # from movies by city/date

        city_date = args.__getattribute__('city and/or date') # b/c spaces
        city_date.append(DATE) # pad with default
        maybe_city, maybe_date, *_ = city_date

        try:
            city = maybe_city
            theaters = get_theaters(city)
            date = maybe_date
        except(FileNotFoundError, AssertionError):     # date rather than city
            try:
                city = maybe_date # could be None..
                theaters = get_theaters(city)
            except(FileNotFoundError, AssertionError): # date rather than city
                city = CITY
                theaters = get_theaters(city)
            date = maybe_city if maybe_city is not None else DATE

        moviegetter = partial(get_movies, date=convert_date(date))

    # do stuff
    need_ratings = args.filter_by > 0 or not args.simple
    if need_ratings:
        d_cached = {}

        try:
            from ratings import get_ratings
        except(Exception) as e: # e.g. missing secrets
            msg, = e.args
            print(msg + '\n\n')

            need_ratings = False

    for theater in theaters:
        print()

        movie_names, movie_times = moviegetter(theater=theater)

        if need_ratings:
            try:
                movie_ratings, d_cached = get_ratings(movie_names, d_cached)

            except(Exception) as e: # e.g. API request failed
                msg, = e.args
                print(msg + '\n\n')

                movie_ratings = []
        else:
            movie_ratings = []

        print_movies(theater, *filter_by_rating(movie_names,
                                                movie_times,
                                                movie_ratings,
                                                args.filter_by),
                     sorted_=args.sorted)
    if theaters:
        print()
