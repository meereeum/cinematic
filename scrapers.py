from datetime import datetime
from itertools import chain
import json
import re

from bs4 import element
from dateutil import parser as dparser

from CLIppy import AttrDict, convert_date, safe_encode, soup_me
from utils import combine_times, error_str, filter_movies, filter_past


def get_movies_google(theater, date, *args, **kwargs):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :args, kwargs: other search terms, e.g. zip code
    :returns: (list of movie names, list of lists of movie times)
    """
    # date = convert_date(date, fmt_out='%A %m/%d')
    fdate = convert_date(date, fmt_out='%A') # formatted for search
    # date = convert_date(date, fmt_out='%m/%d') # /%y')

    BASE_URL = 'https://www.google.com/search'
    # PARAMS = {'q': safe_encode(theater, date, *args, **kwargs)}
    PARAMS = {'q': safe_encode('showtimes at', theater, fdate,
                               *args, **kwargs)}

    soup = soup_me(BASE_URL, PARAMS)

    # TODO google static html only returns up to 10 movies..

    CLASS = AttrDict(
            movie = 'JLxn7',
            date = 'r0jJne AyRB2d',
            timelist = 'e3wEkd',
            time = 'ovxuVd',
            divider = 'Qlgfwc'
    )

    try:
        # check date
        date_found, = soup('div', class_=CLASS.date)[0].span.contents
        assert convert_date(date_found) == date, '{} != {}'.format(date_found, date)

        time_contents2string = lambda t: ''.join((str(t[0]), *t[1].contents))

        # no need to filter - tags only correspond to upcoming movie times
        movie_names = [movie_div.a.contents[0] for movie_div
                       in soup('div', class_=CLASS.movie)]
        movie_times = [[time_contents2string(time_div.contents)
                        for time_div in time_divs('div', class_=CLASS.time)]
                       for time_divs in soup('div', class_=CLASS.timelist)]

    except(AssertionError, IndexError) as e:
        #import IPython; IPython.embed()
        print(error_str.format(e))        # error msg only
        movie_names, movie_times = [], [] # no movies found for desired date

    if len(movie_names) != len(movie_times): # multiple timelists per movie
        n = 0
        n_timelists_per_movie = []
        types_per_movie = []

        PATTERN = re.compile('^.*\((.*)\)') # capture movietype in parens

        for elem in soup('div', class_=CLASS.movie)[0].nextGenerator(): # after 1st movie
            if isinstance(elem, element.Tag):
                # time list:
                if elem.name == 'div' and elem.get('class') == [CLASS.timelist]:
                    movietype = re.sub(PATTERN, '\\1',
                                       elem.previous.previous.string)
                    types_per_movie.append(movietype) # standard, imax, 3d, ..
                    n += 1

                # movie divider:
                elif elem.name == 'td' and elem.get('class') == [CLASS.divider]:
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


def get_movies_metrograph(theater, date):
    """Get movie names and times from Metrograph website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://metrograph.com/film'
    PARAMS = {'d': date}

    soup = soup_me(BASE_URL, PARAMS)

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
    BASE_URL = 'https://videologybarandcinema.com/events/{}'

    soup = soup_me(BASE_URL.format(date))

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

    soup = soup_me(BASE_URL)

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
    # & combine times for same movie
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_pghfilmmakers(theater, date):
    """Get movie names and times from Pittsburgh Filmmakers website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://cinema.pfpca.org/films/showtimes?location={}'

    D_THEATERS = {
        'regent square theater': 24,
        'harris theater': 20,
        'melwood screening room': 18
    }

    soup = soup_me(BASE_URL.format(D_THEATERS[theater]))

    # get date block
    try:
        block, = [day for day in soup.findAll('caption')
                  if day.text == convert_date(date, fmt_out='%a, %b %-d')]
    except(ValueError): # indexing into empty list
        return [], []

    movie_names = [name.text for name in block.next.next.next.findAll(
                   'a', href=re.compile('/films/*'))]

    movie_datetimes = [
        ' @ '.join((date, div.next.next.next.text.strip()))
        for div in block.next.next.next.findAll(
            'td', class_='views-field views-field-field-location')]

    movie_times = filter_past(movie_datetimes)

    # filter movies with no future times
    # & combine times for same movie
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_loews_theater(theater, date):
    """Get movie names and times from Landmark Loew's Jersey website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://loewsjersey.org/calendar/?tribe-bar-date={}'

    soup = soup_me(BASE_URL.format(date[:-3])) # yyy-mm

    movie_headers = [h for h in soup.findAll('h3', class_="tribe-events-month-event-title")
                     if h.text.lower().startswith("film screening")]

    relevant_movies = [h for h in movie_headers if
                       h.parent.attrs['id'][-10:] == date]

    if relevant_movies:
        movie_names = [h.text.replace('Film Screening: “', '').replace('”','')
                       for h in relevant_movies]
        movie_datetimes = [json.loads(h.parent.attrs['data-tribejson'])['startTime'] # date @ time
                           for h in relevant_movies]

        movie_times = filter_past(movie_datetimes)
        movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    else:
        movie_names, movie_times = [], []

    return movie_names, movie_times
