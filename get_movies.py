# from collections import OrderedDict
from datetime import datetime, timedelta
import os
import requests
import sys

from bs4 import BeautifulSoup
from dateutil import parser

from secrets import API_KEY


def get_movies(theater, date='', *args, **kwargs):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :args: other search terms, e.g. date
    :kwargs: other search terms, e.g. date
    :returns: (list of movie names, list of lists of movie times)
    """
    # param_str = ' '.join((theater, *args, *kwargs.values()))
    def safe_encode(*args, **kwargs):
        SPACE_CHAR = '+'
        return SPACE_CHAR.join((*args, *kwargs.values())).replace(
            ' ', SPACE_CHAR)

    BASE_URL = 'https://www.google.com/search'
    PARAMS = {'q': safe_encode(theater, date, *args, **kwargs)}

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


def get_ratings(movie_name):
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


def print_movies(theater, movie_names, movie_times):
    """Pretty-print movies

    :theater: str
    :movie_names: [strs]
    :movie_times: [strs]
    """
    TIME_SPACE = 7
    EXTRA_SPACE = 7

    theater_space = len(theater)
    try:
        col_space = len(max(movie_names, key=len))
    except(ValueError): # search found no movies
        print('skipping {}...'.format(theater))
        return

    underline_space = int(
        ((col_space + TIME_SPACE + EXTRA_SPACE) - theater_space) / 2)

    print('{}{}{}'.format('_' * underline_space,
                          theater.upper(),
                          '_' * underline_space))
    for name, times in zip(movie_names, movie_times):
        # avoid joining chars in string iterable
        times = (times if isinstance(times, list) else [times])
        print('{:{}}  |  {}'.format(name, col_space, ', '.join(times)))


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
    # return date_out


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
    D_ACTIONS = {
        'metrograph': get_movies_metrograph,
        'videology': get_movies_videology
    }

    kwargs = {
        'date': convert_date(DATE_IN)
    }
    d_ratings = {}
    for theater in get_theaters(CITY_IN):
        print('')
        kwargs['theater'] = theater
        action = D_ACTIONS.get(theater, get_movies) # default to google search
        # print_movies(theater, *action(**kwargs))

        movie_names, movie_times = action(**kwargs)

        movie_rating_ds = [d_ratings.get(movie_name, # reuse if already cached
                                         get_ratings(movie_name))
                           for movie_name in movie_names]
        d_ratings.update(zip(movie_names, movie_rating_ds)) # update cache

        # ratings_rt = [d.get('Rotten Tomatoes', None)
        movie_ratings = [d.get('Rotten Tomatoes',
                               d.get('Internet Movie Database', None))
                         for d in movie_rating_ds]
    print('')
