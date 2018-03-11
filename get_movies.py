import argparse
from datetime import datetime, timedelta
from itertools import chain, zip_longest
import math
import os
import re
import requests
import sys

from bs4 import BeautifulSoup, element
from dateutil import parser as dparser

from secrets import API_KEY


## TODO
# http://omdbapi.com/apikey.aspx


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


def get_movies_google(theater, date):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    # :args: other search terms, e.g. date
    # :kwargs: other search terms, e.g. date
    :returns: (list of movie names, list of lists of movie times)
    """
    def safe_encode(*args, **kwargs):
        SPACE_CHAR = '+'
        return SPACE_CHAR.join((*args, *kwargs.values())).replace(
            ' ', SPACE_CHAR)

    BASE_URL = 'https://www.google.com/search'
    PARAMS = {'q': safe_encode(theater, date)}
    # PARAMS = {'q': safe_encode(theater, date, *args, **kwargs)}

    soup = BeautifulSoup(requests.get(BASE_URL, PARAMS).content, 'lxml')

    try:
        # check date
        date_found = soup('div', class_='_S5j _Y5j')[0].span.contents[0]
        assert convert_date(date_found) == date

        time_contents2string = lambda t: ''.join((str(t[0]), *t[1].contents))

        # no need to filter - tags only correspond to upcoming movie times
        movie_names = [movie_div.a.contents[0] for movie_div
                       in soup('div', class_='_T5j')]
        movie_times = [[time_contents2string(time_div.contents) for time_div
                        in time_divs('div', class_='_wxj')] for time_divs
                       in soup('div', class_='_Oxj')]

    except(AssertionError, IndexError):
        movie_names, movie_times = [], [] # no movies found for desired date

    # TODO currently fails if multiple time lists per movie, e.g. 70mm & standard
    if len(movie_names) != len(movie_times): # multiple timelists per movie
        # import IPython; IPython.embed()

        n = 0
        n_timelists_per_movie = []
        types_per_movie = []

        for elem in soup('div', class_='_T5j')[0].nextGenerator(): # after 1st movie
            if isinstance(elem, element.Tag):
                if elem.name == 'div' and elem.get('class') == ['_Oxj']: # time list
                    types_per_movie.append(elem.previous.previous.string) # standard, imax, 3d, ..
                    n += 1
                elif elem.name == 'td' and elem.get('class') == ['_V5j']: # movie divider
                    n_timelists_per_movie.append(n)
                    n = 0
        n_timelists_per_movie.append(n)

        movie_names = list(chain.from_iterable(
            [name] * n for name, n in zip(movie_names, n_timelists_per_movie)))
        movie_times = [(times if movie_type == 'Standard' else
                        times + ['[ {} ]'.format(movie_type)])
                    for times, movie_type in zip(movie_times, types_per_movie)]

    return movie_names, movie_times


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


def get_movies_metrograph(theater, date):
    """Get movie names and times from Metrograph website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://metrograph.com/film'
    # PARAMS = [('d', quote(date))]
    PARAMS = [('d', date)]

    soup = BeautifulSoup(requests.get(BASE_URL, PARAMS).content, 'lxml')

    movie_names = [movie_div.a.contents[0] for movie_div
                   in soup('h4', class_='title')]
    movie_times = [[time.contents[0] for time in time_div('a')] for time_div
                   in soup('div', class_='showtimes')]

    # filter movies with no future times
    movie_names, movie_times = filter_movies(movie_names, movie_times)

    return movie_names, movie_times


def get_movies_videology(theater, date):
    """Get movie names and times from Videology website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://videologybarandcinema.com/events/'

    soup = BeautifulSoup(requests.get(BASE_URL + date).content, 'lxml')

    movie_names = [movie_div.a['title'] for movie_div
                   in soup('h2', class_='tribe-events-list-event-title summary')]

    # get times filtered by past
    movie_datetimes = [ # date @ time
        time_div.span.contents[0] for time_div
        in soup('div', class_='tribe-updated published time-details')]
    movie_times = filter_past(movie_datetimes)

    # filter movies with no future times
    movie_names, movie_times = filter_movies(movie_names, movie_times)

    return movie_names, movie_times


def get_movies_film_noir(theater, date):
    """Get movie names and times from Film Noir website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.filmnoircinema.com/program'

    soup = BeautifulSoup(requests.get(BASE_URL).content, 'lxml')

    date = dparser.parse(date)
    movie_divs = soup('a', class_='eventlist-title-link',
                      href=re.compile('/program/{}/{}/{}/'.format(
                          date.year, date.month, date.day))) # no zero-padding
    movie_names = [movie_div.text for movie_div in movie_divs]

    # get times filtered by past
    movie_datetimes = chain.from_iterable((
        [' @ '.join((time_div['datetime'], time_div.text)) for time_div in
         movie_div.next.next.next('time', class_='event-time-12hr-start')]
        for movie_div in movie_divs))
    movie_times = filter_past(movie_datetimes)

    # filter movies with no future times
    movie_names, movie_times = filter_movies(movie_names, movie_times)

    return movie_names, movie_times


def get_ratings_per_movie(movie_name):
    """Get movie ratings (IMDb, Metacritic, Rotten Tomatoes)

    :movie_name: str
    :returns: dict { ratings site: float(rating) }
    """
    BASE_URL = 'http://www.omdbapi.com'
    PARAMS = {
        't': movie_name,
        'type': 'movie',
        'apikey': API_KEY
    }

    def rating2float(rating_str):
        """Movie rating (percent or fraction) -> float

        :rating_str: str
        :returns: float
        """
        a, b = (float(x) for x in rating_str.replace('%', '/100').split('/'))
        return a / b

    movie_json = requests.get(BASE_URL, PARAMS).json()
    # d_ratings = {d['Source']: d['Value'] for d in movie_json['Ratings']}
    # d_ratings = {d['Source']: rating2float(d['Value'])

    d_ratings = ({d['Source']: rating2float(d['Value'])
                  for d in movie_json['Ratings']}
                 if movie_json['Response'] == 'True' else {})

    return d_ratings


def get_ratings(movie_names, d_cached):
    """Get movie ratings corresponding to movies, using cached review lookups

    :movie_names: [strs]
    :d_cached: dictionary of cached ratings {'name': float(rating)}
    :returns: (list of ratings, updated dictionary)
    """
    movie_rating_ds = [d_cached.get(movie_name, # reuse if already cached
                                    get_ratings_per_movie(movie_name))
                       for movie_name in movie_names]
    movie_ratings = [d.get('Rotten Tomatoes', # 1st choice review
                           d.get('Internet Movie Database', -1)) # fallbacks
                     for d in movie_rating_ds]

    d_cached.update(zip(movie_names, movie_rating_ds)) # update cache

    return movie_ratings, d_cached


def filter_by_rating(movie_names, movie_times, movie_ratings, threshold=0):
    """Filter movies by minimum rating

    :movie_names: [strs]
    :movie_times: [[strs]]
    :movie_ratings: [floats]
    :threshold: float (0 - 1)
    :returns: tuple(movie names, movie times, movie ratings)
    """
    tuple_in = (movie_names, movie_times, movie_ratings)
    tuple_out = (zip(*((name, time, rating) for name, time, rating in zip(*tuple_in)
                       if rating >= threshold or rating < 0)) # only if above threshold or rating not found
                 if threshold > 0 else tuple_in) # else, don't bother to filter
    tuple_out = tuple(tuple_out)
    tuple_out = (tuple_out if tuple_out else ((), (), ())) # don't return empty tuple if all filtered out
    return tuple_out


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
    UNDERLINE_CHAR = '_'

    PATTERN = re.compile(', \[') # reformat movie type in timelist

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

        time_str = re.sub(PATTERN, '  [', ', '.join(times))

        return '{}{:{}}{:^{}}{}'.format(rating_str,
                                        name, col_space,
                                        SEP_CHAR, SPACER * 2 + len(SEP_CHAR),
                                        # ', '.join(times))
                                        time_str)

    # until fix for multiple times per movie
    if len(movie_names) != len(movie_times):
        movie_times = (('?') for _ in movie_names)

    with_rating = (movie_ratings != [])
    movie_strs = [to_pprint_str(name, times, rating, with_rating=with_rating)
                  for name, times, rating in zip_longest(
                          movie_names, movie_times, movie_ratings)]
    movie_strs = ([movie_str for _, movie_str in sorted(
        zip(movie_ratings, movie_strs), reverse=True)] # sort best -> worst
                  if sorted_ else movie_strs)

    round_up_to_even = lambda x: math.ceil(x / 2) * 2 # closest even int (>=)
    underline_space = round_up_to_even(len(max(movie_strs, key=len)) -
                                       theater_space) + theater_space
    theater_str = '{:{}^{}}'.format(theater.upper(), UNDERLINE_CHAR, underline_space)

    print(theater_str); print('\n'.join(movie_strs))
    # print('\n'.join([theater_str] + movie_strs))


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
