# from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import zip_longest
import os
import requests
import sys

from bs4 import BeautifulSoup
from dateutil import parser

from secrets import API_KEY


def get_movies(theater, date):
    """Get movie names and times

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    D_ACTIONS = {
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
    # param_str = ' '.join((theater, *args, *kwargs.values()))
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
    movie_datetimes = [
        time_div.span.contents[0] for time_div
        in soup('div', class_='tribe-updated published time-details')]

    # filter past movie times
    now = datetime.now()
    is_past = lambda dt: (
        parser.parse(dt.replace('@', ',')) - now).total_seconds() < 0
    movie_times = [[dt.split(' @ ')[1].replace(' ', '')] # list of lists
                   if not is_past(dt) else [] for dt in movie_datetimes]

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
    #              for d in movie_json['Ratings']}
    # try:
    #     d_ratings = {d['Source']: rating2float(d['Value'])
    #                  for d in movie_json['Ratings']}
    # except(KeyError): # no ratings found
    #     import IPython; IPython.embed()

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




def print_movies(theater, movie_names, movie_times, movie_ratings=[]):
    """Pretty-print movies

    :theater: str
    :movie_names: [strs]
    :movie_times: [strs]
    :movie_ratings: [floats]
    """
    TIME_SPACE = len('xx:xxpm')
    RATING_SPACE = len('(xx%)')
    SPACER = 2

    SEP_CHAR = '|'
    UNDERLINE_CHAR = '_'

    extra_space = SPACER * 3 + len(SEP_CHAR) + TIME_SPACE #+ RATING_SPACE
    extra_space = (extra_space + RATING_SPACE) if movie_ratings else extra_space

    theater_space = len(theater)
    try:
        col_space = len(max(movie_names, key=len))
    except(ValueError): # search found no movies
        print('skipping {}...'.format(theater))
        return

    round_to_even = lambda x: int(x / 2) * 2
    underline_space = round_to_even(col_space + extra_space -
                                    theater_space) + theater_space

    print('{:{}^{}}'.format(theater.upper(), UNDERLINE_CHAR, underline_space))
    # for name, times, rating in zip(movie_names, movie_times, movie_ratings):

    NULL = 47
    for name, times, rating in zip_longest(movie_names, movie_times, movie_ratings,
                                           fillvalue=NULL):
        t_rating_fmt = ((rating, '.0%') if rating is not None else
                        ('?', '^3')) # tuple (str, strfmt)
        spacer = (SPACER - 1) if rating == 1. else SPACER
        t_spacer = ('', spacer)

        rating_str = ('({:{}}){:{}}'.format(*t_rating_fmt, *t_spacer)
                      if rating != NULL else '')

        # print('({:{}}){:{}}{:{}}{:^{}}{}'.format(*t_rating_fmt,
        #                                          *t_spacer,
                                                 # name,
                                                 # col_space,
                                                 # SEP_CHAR,
                                                 # SPACER * 2 + len(SEP_CHAR),
                                                 # ', '.join(times)))
        print('{}{:{}}{:^{}}{}'.format(rating_str,
                                       name, col_space,
                                       SEP_CHAR, SPACER * 2 + len(SEP_CHAR),
                                       ', '.join(times)))
        # print('({:{}}){}{:{}}  |  {}'.format(*t_rating_fmt, *t_spname, col_space,
        #                                      ', '.join(times)))


def get_theaters(city):
    """Get list of theaters by desired `city` from txt file

    :city: str
    :returns: list of theaters (str)
    """
    BASE_FNAME = 'theaters'
    COMMENT_CHAR = '#'

    dirname = os.path.dirname(os.path.realpath(__file__))
    fname = '_'.join((BASE_FNAME, city))

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
        date_out = parser.parse(date_out)
    except(AttributeError, TypeError): # already datetime
        date_out = date_out
    except(ValueError):
        print("I don't recognize that date.. try again ?")
        sys.exit(0)

    return date_out.strftime('%Y-%m-%d')


if __name__ == '__main__':
    # parse args
    try:
        CITY_IN = sys.argv[1]
    except(IndexError):
        CITY_IN = 'nyc'

    try:
        DATE_IN = sys.argv[2]
    except(IndexError):
        DATE_IN = 'today'

    # do stuff
    kwargs = {
        'date': convert_date(DATE_IN)
    }
    d_cached = {}
    for theater in get_theaters(CITY_IN):
        print('')
        kwargs['theater'] = theater
        # print_movies(theater, *action(**kwargs))

        # movie_names, movie_times = action(**kwargs)
        movie_names, movie_times = get_movies(**kwargs)

        if WITH_RATINGS or FILTER_BY > 0:
            movie_ratings, d_cached = get_ratings(movie_names, d_cached)
        else:
            movie_ratings = []

        print_movies(theater, movie_names, movie_times, movie_ratings)

    print('')
