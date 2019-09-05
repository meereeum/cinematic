from datetime import datetime
from itertools import chain
import json
import re
from time import sleep

from bs4 import element
from dateutil import parser as dparser

from CLIppy import AttrDict, convert_date, flatten, json_me, safe_encode, soup_me
from utils import combine_times, error_str, filter_movies, filter_past, index_into_days


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
    movie_datetimes = list(chain.from_iterable((
        [' @ '.join((time_div['datetime'], time_div.text)) for time_div in
         movie_div.next.next.next('time', class_='event-time-12hr-start')]
        for movie_div in movie_divs)))
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
        block, = [day for day in soup('caption')
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

    movie_headers = [h for h in soup('h3', class_="tribe-events-month-event-title")
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


def get_movies_syndicated(theater, date):
    """Get movie names and times from Syndicated's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://syndicatedbk.com/events/'

    soup = soup_me(BASE_URL)

    movie_strs = [div.text.strip() for div in soup(
        'div', id=re.compile('tribe-events-event-[0-9]*-{}'.format(date)))]

    matches = [re.search(' \([0-9:]* [ap]m\)', movie_str, re.I)
               for movie_str in movie_strs]

    movie_names = [movie_str[:m.start(0)]                 # extract name
                   for m, movie_str in zip(matches, movie_strs)]

    movie_datetimes = ['{} @ {}'.format(date, time) for time in
                       (movie_str[m.start(0)+2:m.end(0)-1] # extract time (while removing trailing " (" & ")")
                        for m, movie_str in zip(matches, movie_strs))]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_alamo(theater, date):
    """Get movie names and times from Alamo's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://feeds.drafthouse.com/adcService/showtimes.svc/calendar/2101/'

    djson = json_me(BASE_URL)

    # filter months -> weeks -> day
    day, = flatten([[d for d in week['Days'] if d['Date'].startswith(date)]
                    for week in flatten(month['Weeks'] for month in
                                        djson['Calendar']['Cinemas'][0]['Months'])])
    movies = day['Films']

    movie_names = [movie['FilmName'] for movie in movies]

    movie_times = [flatten([flatten([
        ['{}m'.format(sesh['SessionTime']) # e.g. p -> pm
         for sesh in f['Sessions'] if (sesh['SessionStatus'] != 'soldout' and # `onsale` only
                                       sesh['SessionStatus'] != 'past')]
        for f in series['Formats'] # format doesn't seem to mean anything here - e.g. 70mm still coded as "Digital"
        ]) for series in movie['Series']]) for movie in movies]

    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_ifc(theater, date):
    """Get movie names and times from IFC's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://www.ifccenter.com/'

    soup = soup_me(BASE_URL)

    day, = [day for day in soup('div', class_=re.compile('^daily-schedule'))
            if day.h3.text != 'Coming Soon'
            and convert_date(day.h3.text) == date]

    movie_divs = day('div')

    movie_names = [mdiv.h3.text for mdiv in movie_divs]
    movie_datetimes = [['{} @ {}'.format(date, time.text)
                        for time in mdiv('li')] for mdiv in movie_divs]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_film_forum(theater, date):
    """Get movie names and times from Film Forum's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://filmforum.org/'

    # soup_me(BASE_URL) # first request is blocked by ROBOTS
    # sleep(5)
    soup = soup_me(BASE_URL)

    try:
        assert not soup.meta.attrs['name'] == 'robots', 'robots'
    except(AssertionError) as e:
        print(error_str.format(e)) # error msg only
        return [], []              # blocked from getting movies :(

    days = [d.text for d in (soup.find('div', class_='sidebar-container')
                                 .findAll('li'))]
    iday = index_into_days(days, date=date)

    day = soup.find('div', id='tabs-{}'.format(iday))

    movie_names = [
        ''.join((txt for txt in mdiv.contents if isinstance(txt, str))).strip() # ignore txt in extra <span>s
        for mdiv in day('a', href=re.compile('^https://filmforum.org/film'))]

    # N.B. could have modifier like "♪" after time
    PATTERN = re.compile('([0-9])\*?$')

    movie_datetimes = [
        ['{} @ {}'.format(date, re.sub(PATTERN, r'\1 pm', time.text)) # only AM is labeled explicitly
         for time in p('span', class_=None)] for p in day('p')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_quad(theater, date):
    """Get movie names and times from Quad's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://quadcinema.com/all/'

    soup = soup_me(BASE_URL)

    day, = [d for d in soup('div', class_='now-single-day')
            if convert_date(d.h1.text) == date]

    movie_names = [movie.text for movie in day('h4')]
    movie_datetimes = [['{} @ {}'.format(date, time.text.replace('.', ':'))
                        for time in movie('li')]
                       for movie in day('div', class_='single-listing')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_cinema_village(theater, date):
    """Get movie names and times from Cinema Village's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.cinemavillage.com/showtimes/'

    soup = soup_me(BASE_URL)

    days = [day.contents[-1].strip().replace('.', '-')
            for day in soup('a', {'data-toggle': 'tab'})]
    iday = index_into_days(days, date=date)

    day = soup.find('div', id='tab_default_{}'.format(iday))

    movie_names = [movie.text for movie in day('a')]
    movie_datetimes = [['{} @ {}'.format(date, time.text)
                        for time in times('span')]
                       for times in day('div', class_='sel-time')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_village_east_or_angelika(theater, date):
    """Get movie names and times from Village East Cinema or Angelika Film Center's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.{}/showtimes-and-tickets/now-playing/{}'

    d_theaters = {'village east cinema': 'citycinemas.com/villageeast',
                  'angelika film center': 'angelikafilmcenter.com/nyc'}

    soup = soup_me(BASE_URL.format(d_theaters[theater], date))

    movie_names = [movie.text for movie in soup('h4', class_='name')]

    movie_datetimes = [['{} @ {}'.format(date, time.attrs['value']) for time in
                        times('input', class_='showtime reserved-seating')]
                       for times in soup('div', class_="showtimes-wrapper")]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_anthology(theater, date):
    """Get movie names and times from Anthology's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://anthologyfilmarchives.org/film_screenings/calendar?view=list'

    soup = soup_me(BASE_URL.format(date))

    days = soup('h3', class_='current-day')
    iday = index_into_days(
        [''.join((_ for _ in day.contents if isinstance(_, str))).strip()
         for day in days], date=date)

    border = (days[iday + 1] if iday < len(days) - 1 else
              soup.find('div', id='footer'))

    next_movies = days[iday].findAllNext('div', class_='showing-details')
    prev_movies = border.findAllPrevious('div', class_='showing-details')

    movies = list(set(next_movies) & set(prev_movies)) # get intersection b/w borders

    movie_names = [m.find('span', class_='film-title').text for m in movies]

    movie_datetimes = [['{} @ {}'.format(date, time.text) for time in
                        movie('a', {'name': re.compile("^showing-")})]
                       for movie in movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_coolidge(theater, date):
    """Get movie names and times from Coolidge Corner's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://coolidge.org/showtimes'
    PARAMS = {'date': date}

    soup = soup_me(BASE_URL, PARAMS)

    movies = soup('div', class_='film-card')

    movie_names = [m.h2.text for m in movies]

    movie_datetimes = [
        ['{} @ {}'.format(date, time.text) for time in
         m('span', class_='showtime-ticket__time')] for m in movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_brattle(theater, date):
    """Get movie names and times from Brattle Theater's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.brattlefilm.org/category/calendar-2'

    soup = soup_me(BASE_URL)

    PATTERN = re.compile('^https://www.brattlefilm.org/{}'.format(
        date.replace('-', '/')))

    relevant_movies = [
        movie for movie in soup('span', class_="calendar-list-item")
        if movie('a', href=PATTERN)]

    movie_names = [m.h2.text for m in relevant_movies]

    PATTERN = re.compile('([0-9])\ ?$')

    movie_datetimes = [
        ['{} @ {}'.format(date, re.sub(PATTERN, r'\1 pm', time)) # only last time is labeled explicitly
        for time in m.li.text.replace('at ', '').split(',')]
        for m in relevant_movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_somerville(theater, date):
    """Get movie names and times from Somerville Theater's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://somervilletheatre.com/wp-content/themes/somerville/showtimes.xml'
    
    soup = soup_me(BASE_URL)

    movies = soup('filmtitle')

    movie_names = [m.shortname.text for m in movies] # /or/ m.find('name').text

    convert = lambda date: (date[i:j] for i,j in ((4,8),(0,2),(2,4))) # mmddyyyy -> (yyyy, mm, dd)

    movie_datetimes = [
        ['{}-{}-{} @ {}'.format(*convert(d.text), t.text)
        for t, d in zip(m('time'), m('date'))
        if d.text == convert_date(date, fmt_out='%m%d%Y')] for m in movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_landmark(theater, date):
    """Get movie names and times from Kendall Landmark's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://movie-lmt.peachdigital.com/movies/GetFilmsByCinema/21/151'

    djson = json_me(BASE_URL)

    movie_names = [movie['Title'] for movie in djson['Result']]

    movie_datetimes = [
        flatten([['{} @ {}'.format(date, t['StartTime']) for t in sesh['Times']
                  if convert_date(sesh['DisplayDate']) == date] for sesh in seshes])
        for seshes in (movie['Sessions'] for movie in djson['Result'])]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_nitehawk(theater, date):
    """Get movie names and times from Nitehawk's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://nitehawkcinema.com/{}/{}'

    d_theaters = {'nitehawk cinema': 'williamsburg',
                  'nitehawk prospect park': 'prospectpark'}

    soup = soup_me(BASE_URL.format(d_theaters[theater], date))

    movie_names = [movie.text for movie in soup('div', class_='show-title')]

    movie_datetimes = [
        ['{} @ {}'.format(date, t.text.strip())
        for t in times('a', class_='showtime')]
        for times in soup('div', class_='showtimes-container clearfix')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_filmlinc(theater, date):
    """Get movie names and times from Film at Lincoln Center's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.filmlinc.org/wp-content/themes/filmlinc/api-events.php'

    PARAMS = {'start': date, 'end': date}

    djson = json_me(BASE_URL, PARAMS)

    movie_names = [movie['title'] for movie in djson]

    movie_datetimes = [
        (datetime.fromtimestamp(movie['start'] / 1000) # epoch (in ms) ->
                 .strftime('%Y-%m-%d @ %l:%M%P'))      # yyyy-mm-dd @ hh:mm {a,p}m
        for movie in djson]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times
