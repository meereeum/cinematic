from datetime import datetime
from itertools import chain
import re
import requests

from bs4 import BeautifulSoup, element
from dateutil import parser as dparser

from utils import convert_date


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

    # TODO google static html only returns up to 10 movies..

    CLASS = {'movie': 'JLxn7',
             'timelist': 'e3wEkd',
             'time': 'ovxuVd',
             'divider': 'Qlgfwc'}

    try:
        # check date
        date_found, = soup('div', class_='r0jJne AyRB2d')[0].span.contents
        assert convert_date(date_found) == date

        time_contents2string = lambda t: ''.join((str(t[0]), *t[1].contents))

        # no need to filter - tags only correspond to upcoming movie times
        movie_names = [movie_div.a.contents[0] for movie_div
                       in soup('div', class_=CLASS['movie'])]
        movie_times = [[time_contents2string(time_div.contents) for time_div
                        in time_divs('div', class_=CLASS['time'])] for time_divs
                       in soup('div', class_=CLASS['timelist'])]

    except(AssertionError, IndexError):
        movie_names, movie_times = [], [] # no movies found for desired date

    if len(movie_names) != len(movie_times): # multiple timelists per movie
        n = 0
        n_timelists_per_movie = []
        types_per_movie = []

        for elem in soup('div', class_=CLASS['movie'])[0].nextGenerator(): # after 1st movie
            if isinstance(elem, element.Tag):
                if elem.name == 'div' and elem.get('class') == [CLASS['timelist']]: # time list
                    types_per_movie.append(elem.previous.previous.string) # standard, imax, 3d, ..
                    n += 1
                elif elem.name == 'td' and elem.get('class') == [CLASS['divider']]: # movie divider
                    n_timelists_per_movie.append(n)
                    n = 0
        n_timelists_per_movie.append(n)

        movie_names = list(chain.from_iterable(
            [name] * n for name, n in zip(movie_names, n_timelists_per_movie)))
        movie_times = [(times if movie_type == 'Standard' else
                        times + ['[ {} ]'.format(movie_type)])
                    for times, movie_type in zip(movie_times, types_per_movie)]

        assert len(movie_names) == len(movie_times), '{} != {}'.format(
            len(movie_names), len(movie_times))

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
