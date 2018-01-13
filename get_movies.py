from collections import OrderedDict
from datetime import datetime, timedelta
import requests
import sys

from bs4 import BeautifulSoup
from dateutil import parser


def get_movies(theater, date='', *args, **kwargs):
    """
    :theater: string
    :date: default to today
    :args: other search terms, e.g. date
    :kwargs: other search terms, e.g. date
    :returns: (list of movie names, list of movie times)
    """
    # param_str = ' '.join((theater, *args, *kwargs.values()))
    def safe_encode(*args, **kwargs):
        SPACE_CHAR = '+'
        return SPACE_CHAR.join((*args, *kwargs.values())).replace(
            ' ', SPACE_CHAR)

    BASE_URL = 'https://www.google.com/search'
    # PARAMS = [('q', param_str.replace(' ', '+'))]
    PARAMS = [('q', safe_encode(theater, *args, **kwargs))]

    soup = BeautifulSoup(requests.get(BASE_URL, PARAMS).content, 'lxml')

    time_contents2string = lambda t: ''.join((str(t[0]), *t[1].contents))

    movie_names = [movie_tag('a')[0].contents[0] for movie_tag
                   in soup('div', class_='_T5j')]

    movie_times = [[time_contents2string(time_div.contents)
                    for time_div in time_divs('div', class_='_wxj')]
                   for time_divs in soup('div', class_='_Oxj')]

    return (movie_names, movie_times)

def print_movies(theater, movie_names, movie_times):
    """
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
        print('{:{}}  |  {}'.format(name, col_space, ', '.join(times)))


def get_theaters(city):
    """
    :city: str
    :returns: list of theaters (str)
    """
    BASE_FNAME = 'theaters'
    with open('_'.join((BASE_FNAME, city)), 'r') as f:
        theaters = [l.strip() for l in f]
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
        date_out = D_CONVERSIONS[date_in]
    except(KeyError):
        date_out = date_in

    try: # if str, convert to datetime
        date_out = parser.parse(date_out)
    except(AttributeError, TypeError): # already datetime
        date_out = date_out
    except(ValueError):
        print("I don't recognize that date.. try again ?")
        sys.exit(0)

        d.strftime('%Y-%m-%d')

    return date_out


if __name__ == '__main__':
    CITY_IN = sys.argv[1]

    kwargs = {}
    try:
        DATE_IN = sys.argv[2]
        kwargs['date'] = convert_date(DATE_IN)
    except(IndexError):
        pass # default to today

    theaters = get_theaters(CITY_IN)
    for theater in theaters:
        print('')
        kwargs['theater'] = theater
        print_movies(theater, *get_movies(**kwargs))
    print('')

    # food = get_dishes(**kwargs)
    # print(''); print('__How about__'); print('\n'.join(food)); print('')
