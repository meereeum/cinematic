from collections import OrderedDict
from datetime import datetime, timedelta
import requests
import sys

from bs4 import BeautifulSoup
from dateutil import parser


def get_movies(theater, date='', *args, **kwargs):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd)
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

        # movie_names = [movie_div('a')[0].contents[0] for movie_div
        movie_names = [movie_div.a.contents[0] for movie_div
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
    movie_names, movie_times = (([], []) if not movie_times else
                                zip(*((name, time) for name, time
                                    in zip(movie_names, movie_times) if time)))

    return (list(movie_names), list(movie_times))


def get_movies_videology(theater, date):
    """Get movie names and times from Videology website

    :theater: string
    :date: default to today
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://videologybarandcinema.com/events/'

    soup = BeautifulSoup(requests.get(BASE_URL + date).content, 'lxml')

    movie_names = [movie_div.a['title'] for movie_div
                   in soup('h2', class_='tribe-events-list-event-title summary')]
    # movie_times = [
    #     time_div.span.contents[0].split(' @ ')[1].replace(' ','') for time_div
    #     in soup('div', class_='tribe-updated published time-details')]
    movie_datetimes = [
        time_div.span.contents[0] for time_div
        in soup('div', class_='tribe-updated published time-details')]

    # filter movies with no future times
    now = datetime.now()
    is_past = lambda dt: (
        parser.parse(dt.replace('@', ',')) - now).total_seconds() < 0
    # list of strs (rather than list of lists)
    movie_times = [dt.split(' @ ')[1].replace(' ', '')
                   if not is_past(dt) else '' for dt in movie_datetimes]

    movie_names, movie_times = (([], []) if not ''.join(movie_times) else
                                zip(*((name, [time]) for name, time
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
    """Convert string to uniform `datetime` str

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
    try:
        CITY_IN = sys.argv[1]
    except(IndexError):
        CITY_IN = 'nyc'

    D_ACTIONS = {
        'metrograph': get_movies_metrograph,
        'videology': get_movies_videology
    }

    kwargs = {}
    try:
        DATE_IN = sys.argv[2]
    except(IndexError):
        DATE_IN = 'today'
    kwargs['date'] = convert_date(DATE_IN)

    theaters = get_theaters(CITY_IN)
    for theater in theaters:
        print('')
        kwargs['theater'] = theater
        action = D_ACTIONS.get(theater, get_movies) # default to google search
        print_movies(theater, *action(**kwargs))
    print('')
