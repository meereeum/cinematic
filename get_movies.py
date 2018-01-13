from collections import OrderedDict
from datetime import datetime, timedelta
import requests
import sys
# from urllib.parse import quote

from bs4 import BeautifulSoup
from dateutil import parser


def get_movies(theater, date='', *args, **kwargs):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd)
    :args: other search terms, e.g. date
    :kwargs: other search terms, e.g. date
    :returns: (list of movie names, list of movie times)
    """
    # param_str = ' '.join((theater, *args, *kwargs.values()))
    def safe_encode(*args, **kwargs):
        SPACE_CHAR = '+'
        return SPACE_CHAR.join((*args, *kwargs.values())).replace(
            ' ', SPACE_CHAR)
        # return quote(' '.join((*args, *kwargs.values()))).replace(
        #     '%20', '+')

    BASE_URL = 'https://www.google.com/search'
    # PARAMS = [('q', param_str.replace(' ', '+'))]
    PARAMS = {'q': safe_encode(theater, *args, **kwargs)}

    soup = BeautifulSoup(requests.get(BASE_URL, PARAMS).content, 'lxml')
    # TODO check that today (not tomorrow)

    # check date
    # date_found = soup('div', class_='_S5j _Y5j')[0]('span')[0].contents[0]
    # date_found = convert_date(date_found)

    try:
        date_found = soup('div', class_='_S5j _Y5j')[0]('span')[0].contents[0]
        assert convert_date(date_found) == date

        time_contents2string = lambda t: ''.join((str(t[0]), *t[1].contents))

        movie_names = [movie_div('a')[0].contents[0] for movie_div
                    in soup('div', class_='_T5j')]

        movie_times = [[time_contents2string(time_div.contents) for time_div
                        in time_divs('div', class_='_wxj')] for time_divs
                    in soup('div', class_='_Oxj')]
    except(AssertionError, IndexError):
        movie_names, movie_times = [], [] # no movies found for desired date

    return (movie_names, movie_times)


def get_movies_metrograph(theater, date):
    """Get movie names and times from Metrograph website

    :theater: string
    :date: default to today
    :returns: (list of movie names, list of movie times)
    """
    BASE_URL = 'http://metrograph.com/film'
    # PARAMS = [('d', quote(date))]
    PARAMS = [('d', date)]

    soup = BeautifulSoup(requests.get(BASE_URL, PARAMS).content, 'lxml')

    movie_names = [movie_div('a')[0].contents[0] for movie_div
                   in soup('h4', class_='title')]
    movie_times = [time_div('a') for time_div
                   in soup('div', class_='showtimes')]

    # filter movies with no future times
    movie_names, movie_times = ([], [] if not movie_times else
                                zip(*((name, time[0].contents[0]) for name, time
                                      in zip(movie_names, movie_times) if time)))

    return (list(movie_names), list(movie_times))


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
    with open('_'.join((BASE_FNAME, city)), 'r') as f:
        theaters = [l.strip().lower() for l in f]
    return theaters


def convert_date(date_in):
    """Convert string to `datetime`"""
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

    try: # if abbrev, uncompress for parser
        date_out = D_CONVERSIONS[date_in.lower()]
    except(KeyError):
        date_out = date_in

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
    CITY_IN = sys.argv[1]

    D_ACTIONS = {
        'metrograph': get_movies_metrograph
    }

    kwargs = {}
    try:
        DATE_IN = sys.argv[2]
        # kwargs['date'] = convert_date(DATE_IN)
    except(IndexError):
        # kwargs['date'] = convert_date('today')
        DATE_IN = 'today'
        # pass # default to today
    kwargs['date'] = convert_date(DATE_IN)

    theaters = get_theaters(CITY_IN)
    for theater in theaters:
        print('')
        kwargs['theater'] = theater
        action = D_ACTIONS.get(theater, get_movies) # default to google search
        print_movies(theater, *action(**kwargs))
    print('')

    # food = get_dishes(**kwargs)
    # print(''); print('__How about__'); print('\n'.join(food)); print('')
