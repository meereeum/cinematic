from datetime import datetime
from itertools import chain
import json
import re
from time import sleep

from bs4 import element
from dateutil import parser as dparser
from more_itertools import split_before

from CLIppy import (AttrDict, compose_query, convert_date, flatten, safe_encode,
                    soup_me, json_me)
from utils import (clean_time, combine_times, error_str, index_into_days,
                   filter_movies, filter_past, NoMoviesException, DATETIME_SEP)


def get_movies_google(theater, date, *args, **kwargs):
    """Get movie names and times from Google search

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :args, kwargs: other search terms, e.g. zip code
    :returns: (list of movie names, list of lists of movie times)
    """
    FMT = '%m/%d' # formatted for search
    fdate = convert_date(date, fmt_out=FMT)
    fdate = fdate if fdate != convert_date('today', fmt_out=FMT) else 'today' #''

    BASE_URL = 'https://www.google.com/search'

    PARAMS = {
        'q': safe_encode('showtimes', f'"{theater}"', fdate),
        'ie': 'utf-8',
        'client': 'firefox-b-1-e'
    }

    # soup = soup_me(BASE_URL, PARAMS) #, **kwargs)
    # ^ passing params directly to requests gives problems with extraneous % encoding
    soup = soup_me(compose_query(BASE_URL, PARAMS))

    # TODO google static html only returns up to 10 movies..

    CLASS = AttrDict(
            timelist = 'lr_c_fcc',
            time = re.compile('^(std-ts)|(lr_c_stnl)$'),
            fmt = 'lr_c_vn'
    )

    try:
        relevant_div = soup.find('div', {'data-date': True})

        # check date
        date_found = relevant_div.attrs['data-date']
        assert convert_date(date_found) == date, f'{date_found} != {date}'

        movies = relevant_div('div', {'data-movie-name': True})

    except(AssertionError, AttributeError) as e:
        # print(error_str.format(e)) # error msg only
        # movies = []                # no movies found for desired theater/date
        print(error_str.format('No matching theater on google'))
        raise(NoMoviesException(e))

    movie_names = [m.span.text for m in movies]

    movie_times = [ # nested times per format per movie
        [[time.text for time in timelst('div', class_=CLASS.time)]
         for timelst in m('div', class_=CLASS.timelist)] for m in movies]

    movie_formats = [
        [getattr(timelst.find('div', class_=CLASS.fmt), 'text', None) # default if no format listed
         for timelst in m('div', class_=CLASS.timelist)] for m in movies]

    # flatten timelists for movies with multiple formats
    n_timelists_per_movie = [len(timelsts) for timelsts in movie_times]
    movie_names = list(chain.from_iterable(
        [name] * n for name, n in zip(movie_names, n_timelists_per_movie)))

    # annotate with format
    movie_times = [(times if fmt == 'Standard' or not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(flatten(movie_times),
                                         flatten(movie_formats))]

    # no need to filter - tags only correspond to upcoming movie times
    return movie_names, movie_times


def get_movies_showtimes(theater, date):
    """Get movie names and times from Showtimes' website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.showtimes.com/movie-theaters/{}'

    D_THEATERS = {
        'regal fenway': lambda *args: 'regal-fenway-stadium-13-rpx-6269',
        'ua court st':  lambda *args: 'ua-court-street-stadium-12-rpx-6608'
    }

    try:
        soup = soup_me(BASE_URL.format(
            D_THEATERS.get(theater.lower(),
                           get_theaterpg_showtimes)(theater))) # fallback for unlisted theater
                                                               # (phrased as functions, so theaterpg scraper won't run until necessary)

        movies = soup('li', class_='movie-info-box')

    except(Exception) as e:
        print(error_str.format(e)) # error msg only
        movies = []                # no matching theater

    movie_names = [
        ''.join((re.sub('[\r\n].*', '', name.text.strip())
                 for name in m('h2', class_='media-heading'))) for m in movies]

    nested_buttons = [ # [[day, time, time, day, time], ..] -> [[[day, time, time], [day, time]], ..]
        list(split_before((button.text for button in m('button', type='button')),
                          lambda txt: ',' in txt)) for m in movies]

    movie_datetimes = [flatten(
        [[DATETIME_SEP.join((day.replace(':',''), time)) for time in times]
         for day, *times in buttons if (convert_date(day.replace(':',''))
                                        == date)])
         for buttons in nested_buttons]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_theaterpg_showtimes(theater):
    """Get theater page from Showtimes' website

    :theater: str
    :returns: partial URL (str)
    """
    BASE_URL = 'https://www.showtimes.com/search'

    PARAMS = {'query': safe_encode(theater)}

    soup = soup_me(BASE_URL, PARAMS)

    PATTERN = re.compile('^/movie-theaters/')

    theater_pgs = [re.sub(PATTERN, '', hit.attrs['href'])
                   for hit in soup('a', href=PATTERN)]
    try:
        return theater_pgs[0] # best hit
    except(IndexError) as e:
        e.args = ('No matching theater on showtimes.com',)
        raise(e)


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
    movie_formats = [specs.text.split(' / ')[-1] for specs in
                     soup('span', class_='specs')]

    # annotate with format
    movie_times = [(times if fmt == 'DCP' or not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

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
    movie_divs = soup('a', class_='eventlist-title-link', href=re.compile(
        f'/program/{date.year}/{date.month}/{date.day}/')) # no zero-padding
    movie_names = [movie_div.text for movie_div in movie_divs]

    # get times filtered by past
    movie_datetimes = list(chain.from_iterable((
        [DATETIME_SEP.join((time_div['datetime'], time_div.text)) for time_div in
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

    soup = soup_me(BASE_URL.format(D_THEATERS[theater.lower()]))

    # get date block
    try:
        block, = [day for day in soup('caption')
                  if day.text == convert_date(date, fmt_out='%a, %b %-d')]
    except(ValueError): # indexing into empty list
        return [], []

    movie_names = [name.text for name in block.next.next.next(
                   'a', href=re.compile('/films/*'))]

    movie_datetimes = [
        DATETIME_SEP.join((date, div.next.next.next.text.strip()))
        for div in block.next.next.next(
            'td', class_='views-field views-field-field-location')]

    movie_times = filter_past(movie_datetimes)

    # filter movies with no future times
    # & combine times for same movie
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_rowhouse(theater, date):
    """Get movie names and times from Row House Cinema's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://rowhousecinema.com/{}'

    soup = soup_me(BASE_URL.format(date))

    movies = soup('div', class_='showtimes-description')

    movie_names = [m.h2.text.strip() for m in movies]
    movie_datetimes = [[DATETIME_SEP.join((date, time.text.strip()))
                        for time in m('a', class_='showtime')] for m in movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_manor(theater, date):
    """Get movie names and times from The Manor's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://plugin.retrieverapi.com/getSchedule'

    PARAMS = {'date': date}

    headers = {
        'Host': 'plugin.retrieverapi.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://plugin.retrieverapi.com/embed/4227729?print',
        'Authorization': 'Basic NDIyNzcyOToxMjM=',
        'DNT': '1',
        'Connection': 'keep-alive'
    }
    djson = json_me(BASE_URL, PARAMS, headers=headers)

    movies = djson['movies']

    movie_names = [m['movie_name'] for m in movies]

    movie_datetimes = [
        [(dparser.parse(show['date_time'])
                 .strftime(DATETIME_SEP.join(('%Y-%m-%d', '%l:%M%P')))) # yyyy-mm-dd @ hh:mm {a,p}m
         for show in m['showtimes']] for m in movies
    ]
    movie_times = filter_past(movie_datetimes)
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
        'div', id=re.compile(f'tribe-events-event-[0-9]*-{date}'))]

    matches = [re.search(' \([0-9:]* [ap]m\)', movie_str, re.I)
               for movie_str in movie_strs]

    movie_names = [movie_str[:m.start(0)]                 # extract name
                   for m, movie_str in zip(matches, movie_strs)]

    movie_datetimes = [DATETIME_SEP.join((date, time)) for time in
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
    day, *_ = flatten([[d for d in week['Days'] if d['Date'].startswith(date)]
                       for week in flatten(month['Weeks'] for month in
                                           djson['Calendar']['Cinemas'][0]['Months'])])
    movies = day['Films']

    movie_names = [movie['FilmName'] for movie in movies]

    # extract format from name, if any
    PATTERN = re.compile('in ((35|70)mm)$', re.I)
    def extract_fmt(m):
        m, *fmt = re.split(PATTERN, m)[:2] # only name and (35|70)mm, if any
        return m, ''.join(fmt).lower() # (cleaned) movie name, movie fmt

    movie_names, movie_formats = zip(*(extract_fmt(m) for m in movie_names))

    # TODO print sold-out times as xed-out ?
    movie_times = [flatten([flatten([
        ['{}m'.format((sesh['SessionTime'].lower() # e.g. p -> pm
                                          .replace('noon', '12:00p')))
         for sesh in f['Sessions'] if (sesh['SessionStatus'] != 'soldout' and # `onsale` only
                                       sesh['SessionStatus'] != 'past')]
        for f in series['Formats'] # format doesn't seem to mean anything here - e.g. 70mm still coded as "Digital"
        ]) for series in movie['Series']]) for movie in movies]

    # annotate with formats
    movie_times = [(times if not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

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
    movie_datetimes = [[DATETIME_SEP.join((date, time.text))
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

    soup = soup_me(BASE_URL, from_headless=True)
    # headers = {
    #     'Host': 'filmforum.org',
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #     'Accept-Language': 'en-US,en;q=0.5',
    #     'Accept-Encoding': 'gzip, deflate, br',
    #     'Cookie': 'exp_last_visit=1540095881; exp_last_activity=1541986743; prod_last_visit=1567621614; prod_last_activity=1567704700; visid_incap_2071502=8iHssZTnTnSmmcBr3w91Wt3MQ10AAAAAQUIPAAAAAACxMng+kgllZnm0qc4wuBX7; prod_tracker=%7B%220%22%3A%22index%22%2C%221%22%3A%22film%2Faga%22%2C%222%22%3A%22index%22%2C%22token%22%3A%220e8a94586278438a8abd9a2e22f6d71dc58ef797d480e691f6f7d52135be3b8604fc9bc72b9f98e33959ea6c363f6da7%22%7D; incap_ses_139_2071502=/FOyW/1BcEwESBAC4NjtAeH/b10AAAAAu5KRM62+voKYu930nS4qZA==; prod_csrf_token=add79bc2b230529b1baee4c15e4742a3599b154f; incap_ses_529_2071502=LeJGc8MKg19kn678pmNXB3xGcV0AAAAAk5FGgxjtbO141Wfk/d5SNg==',
    #     'DNT': '1',
    #     'Connection': 'keep-alive',
    #     'Upgrade-Insecure-Requests': '1',
    #     'Cache-Control': 'max-age=0, no-cache',
    #     'If-Modified-Since': 'Thu, 05 Sep 2019 17:31:41 GMT',
    #     'Pragma': 'no-cache'
    # }

    # soup_me(BASE_URL) # first request is blocked by ROBOTS
    # sleep(5)
    # soup = soup_me(BASE_URL, headers=headers)

    try:
        assert not soup.meta.attrs.get('name', '').lower() == 'robots', 'robots'
    except(AssertionError) as e:
        print(error_str.format(e)) # error msg only
        return [], []              # blocked from getting movies :(

    days = [d.text for d in (soup.find('div', class_='sidebar-container')
                                 .find_all('li'))]
    iday = index_into_days(days, date=date)

    day = soup.find('div', id=f'tabs-{iday}')

    movie_names = [
        ''.join((txt for txt in mdiv.contents if isinstance(txt, str))).strip() # ignore txt in extra <span>s
        for mdiv in day('a', href=re.compile('^https://filmforum.org/film'))]

    # N.B. could have modifier like "♪" after time
    PATTERN = re.compile('([0-9])\*?$')

    movie_datetimes = [
        [DATETIME_SEP.join((date, re.sub(PATTERN, r'\1 pm', time.text))) # only AM is labeled explicitly
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

    movies = day('div', class_='single-listing')

    PATTERN = re.compile('^time')
    movie_datetimes = [[DATETIME_SEP.join((date, time.text.replace('.', ':')))
                        for time in m('li', class_=PATTERN)] for m in movies]
    movie_times = filter_past(movie_datetimes)

    ANTIPATTERN = re.compile('^[^(time)]') # non-showtime `li`s
    movie_formats = [[fmt.text for fmt in m('li', class_=ANTIPATTERN)]
                     for m in movies]

    # annotate with formats
    movie_times = [(times if not times or not fmt else
                    times + ['[ {} ]'.format(','.join(fmt))])
                   for times, fmt in zip(movie_times, movie_formats)]

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

    day = soup.find('div', id=f'tab_default_{iday}')

    movie_names = [movie.text for movie in day('a')]
    movie_datetimes = [[DATETIME_SEP.join((date, time.text))
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

    D_THEATERS = {
        'village east cinema': 'citycinemas.com/villageeast',
        'angelika film center': 'angelikafilmcenter.com/nyc'
    }

    soup = soup_me(BASE_URL.format(D_THEATERS[theater.lower()], date))

    movie_names = [movie.text for movie in soup('h4', class_='name')]

    movie_datetimes = [[DATETIME_SEP.join((date, time.attrs['value'])) for time in
                        times('input', class_='showtime reserved-seating')]
                       for times in soup('div', class_="showtimes-wrapper")]

    movie_times = filter_past(movie_datetimes)

    # extract format from name, if any
    PATTERN = re.compile('in ((35|70)mm)$', re.I)
    def extract_fmt(m):
        m, *fmt = re.split(PATTERN, m)[:2] # only name and (35|70)mm, if any
        return m, ''.join(fmt).lower() # (cleaned) movie name, movie fmt

    movie_names, movie_formats = zip(*(extract_fmt(m) for m in movie_names))

    # annotate with format
    movie_times = [(times if not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

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
    try:
        iday = index_into_days(
            [''.join((_ for _ in day.contents if isinstance(_, str))).strip()
             for day in days], date=date)
    except(AssertionError): # no matching days
        return [], []

    border = (days[iday + 1] if iday < len(days) - 1 else
              soup.find('div', id='footer'))

    next_movies = days[iday].find_all_next('div', class_='showing-details')
    prev_movies = border.find_all_previous('div', class_='showing-details')

    movies = list(set(next_movies) & set(prev_movies)) # get intersection b/w borders

    movie_names = [m.find('span', class_='film-title').text for m in movies]

    movie_datetimes = [[DATETIME_SEP.join((date, time.text)) for time in
                        movie('a', {'name': re.compile("^showing-")})]
                       for movie in movies]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_momi(theater, date):
    """Get movie names and times from Museum of the Moving Image's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'http://www.movingimage.us/visit/calendar/{}/day/type/1'

    soup = soup_me(BASE_URL.format(date.replace('-', '/')))

    PATTERN = re.compile('calendar/{}'.format(date.replace('-', '/')))
    movies = soup('a', href=PATTERN)

    movie_names = [m.find('span', class_=re.compile("^color")).text for m in movies]

    movie_datetimes = [
        [DATETIME_SEP.join((date, (m.em.text.split(' | ')[0]
                                            .replace('.',''))))] for m in movies
    ]
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
        [DATETIME_SEP.join((date, time.text)) for time in
         m('span', class_='showtime-ticket__time')] for m in movies
    ]
    movie_times = filter_past(movie_datetimes)

    PATTERN = re.compile('^film-program__title')
    is_relevant = lambda s: s.endswith('mm')
    movie_formats = [
        ', '.join((tag.text for tag in m('span', class_=PATTERN)
                   if is_relevant(tag.text))) for m in movies
    ]

    # annotate with format
    movie_times = [(times if not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_brattle(theater, date):
    """Get movie names and times from Brattle Theatre's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.brattlefilm.org/category/calendar-2'

    soup = soup_me(BASE_URL)

    # PATTERN = re.compile('^https://www.brattlefilm.org/{}'.format(
    #     date.replace('-', '/')))

    # relevant_movies = [
    #     movie for movie in soup('span', class_="calendar-list-item")
    #     if movie('a', href=PATTERN)]

    PATTERN = re.compile('y{} m{} d{}'.format(*date.split('-')))
    relevant_movies = soup('div', class_=PATTERN)

    movie_names = [m.h2.text for m in relevant_movies]
    movie_formats = [
        ', '.join((tag.replace('tag-', '') for tag in m['class']
                   if tag.startswith('tag-'))) for m in relevant_movies]

    # only last time is labeled explicitly -- assume rest are p.m. (unless already annotated)
    DEFAULT_TIME_OF_DAY = 'pm'
    PATTERN1 = re.compile('^([0-9: apm\.]*)', re.I)                         # capture time
    PATTERN2 = re.compile(f'([apm\.]+) ?{DEFAULT_TIME_OF_DAY}', re.I) # rm extraneous
    movie_datetimes = [
        [DATETIME_SEP.join((date, re.sub(PATTERN2, r'\1',                 # 2. strip extraneous default (i.e. if already labeled)
                                         re.sub(PATTERN1, r'\1{}'.format( # 1. pad with default time just in case
                                             DEFAULT_TIME_OF_DAY), time))))
        for time in m.li.text.replace('at ', '').split(',')]
        for m in relevant_movies]

    movie_times = filter_past(movie_datetimes)

    PATTERN1 = re.compile('^[0-9:]*((p|a)m)?')                  # time only
    PATTERN2 = re.compile('^[^a-z0-9]*(.*[a-z0-9])[^a-z0-9]*$') # string format only (e.g. no parens)

    # capture extra showing info
    movie_formats_extra = [[re.sub(PATTERN2, r'\1', re.sub(PATTERN1, '', t)) # extract dirty format, then clean
                           for t in ts] for ts in movie_times]

    # .. & further clean times
    movie_times = [[re.match(PATTERN1, t).group(0) for t in ts]
                   for ts in movie_times]
    # before possibly re-annotating (per-showtime)
    movie_times = [[t if not fmt else t + f' [ {fmt} ]'
                    for t, fmt in zip(ts, fmts)]
                   for ts, fmts in zip(movie_times, movie_formats_extra)]

    # annotate with (per-movie) format
    movie_times = [(times if not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_hfa(theater, date):
    """Get movie names and times from Harvard Film Archive's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://harvardfilmarchive.org'

    soup = soup_me(BASE_URL)

    try:
        day, = [d for d in soup('div', class_='grid m-calendar__row')
                if d.time.attrs['datetime'] == date]
    except(ValueError): # no matching days
        return [], []

    movie_names = [m.text.strip() for m in day('h5')]

    movie_datetimes = [DATETIME_SEP.join((date, time.text))
                       for time in day('div', class_='event__time')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_mfa(theater, date):
    """Get movie names and times from Museum of Fine Arts' website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.mfa.org/programs/film'

    PARAMS = {'field_date_value_1': date}

    soup = soup_me(BASE_URL, PARAMS)

    relevant_movies = [
        div for div in soup('div', class_='col-sm-8')
        if div.span and convert_date(div.span.contents[0]) == date
    ]
    movie_names = [m.a.text for m in relevant_movies]

    def convert(contentlst):
        date, _, timestr = contentlst
        start, end = timestr.split('–')
        return DATETIME_SEP.join((convert_date(date), start))

    movie_datetimes = [convert(m.span.contents) for m in relevant_movies]

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

    PATTERN = re.compile(' ((35|70)mm)$', re.I)
    def extract_fmt(m):
        m, *fmt = re.split(PATTERN, m)[:2] # only name and (35|70)mm, if any
        return m, ''.join(fmt).lower() # (cleaned) movie name, movie fmt

    movie_names, movie_formats = zip(*(extract_fmt(m) for m in movie_names))

    convert = lambda date: date[-4:] + date[:-4] # mmddyyyy -> yyyymmdd

    movie_datetimes = [
        [(dparser.parse(' '.join((convert(d.text), t.text)))            # yyyymmdd hhmm ->
                 .strftime(DATETIME_SEP.join(('%Y-%m-%d', '%l:%M%P')))) # yyyy-mm-dd @ hh:mm {a,p}m
         for d, t in zip(m('date'), m('time'))
         if d.text == convert_date(date, fmt_out='%m%d%Y')] for m in movies
    ]
    movie_times = filter_past(movie_datetimes)

    # annotate with formats
    movie_times = [(times if not times or not fmt else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, movie_formats)]

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
        flatten([[DATETIME_SEP.join((date, t['StartTime'])) for t in sesh['Times']
                  if convert_date(sesh['DisplayDate']) == date] for sesh in seshes])
        for seshes in (movie['Sessions'] for movie in djson['Result'])]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_amc(theater, date):
    """Get movie names and times from AMC's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.amctheatres.com/movie-theatres/{}/{}/showtimes/all/{}/{}/all'

    D_THEATERS = {
        'amc boston common': ('boston', 'amc-boston-common-19'),
        'the waterfront': ('pittsburgh', 'amc-waterfront-22')
    }
    theaterplace, theatername = D_THEATERS[theater.lower()]

    soup = soup_me(BASE_URL.format(theaterplace, theatername, date, theatername))

    movies = soup('div', class_='ShowtimesByTheatre-film')

    movie_names = [m.h2.text for m in movies] #soup('h2')]

    movie_datetimes = [
        [[DATETIME_SEP.join((date, clean_time(time.text)))
          for time in times('div', class_='Showtime')
          if not time.find('div', {'aria-hidden':"true"}).text == 'Sold Out']
        # TODO print sold-out times as xed-out ?
         for times in m(
             'div', class_=re.compile('^Showtimes-Section Showtimes-Section'))]
        for m in movies]

    # flatten timelists for movies with multiple formats
    # TODO sometimes lists separate times for same format -- combine ?
    n_timelists_per_movie = [len(timelsts) for timelsts in movie_datetimes]
    movie_names = list(chain.from_iterable(
        [name] * n for name, n in zip(movie_names, n_timelists_per_movie)))
    movie_datetimes = flatten(movie_datetimes)

    movie_times = filter_past(movie_datetimes)

    # annotate with format
    movie_formats = [[fmt.text for fmt in m('h4')] for m in movies]
    movie_times = [(times if fmt == 'Digital' or not times else
                    times + [f'[ {fmt} ]'])
                   for times, fmt in zip(movie_times, flatten(movie_formats))]

    # movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times)) # TODO combine does not know formats
    movie_names, movie_times = filter_movies(movie_names, movie_times)

    return movie_names, movie_times


def get_movies_nitehawk(theater, date):
    """Get movie names and times from Nitehawk's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://nitehawkcinema.com/{}/{}'

    D_THEATERS = {
        'nitehawk': 'williamsburg',
        'nitehawk prospect park': 'prospectpark'
    }

    soup = soup_me(BASE_URL.format(D_THEATERS[theater.lower()], date))

    movie_names = [movie.text for movie in soup('div', class_='show-title')]

    movie_datetimes = [
        [DATETIME_SEP.join((date, clean_time(t.text.strip()))) # ignore any junk after {a,p}m
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
        (datetime.fromtimestamp(movie['start'] / 1000)                  # epoch (in ms) ->
                 .strftime(DATETIME_SEP.join(('%Y-%m-%d', '%l:%M%P')))) # yyyy-mm-dd @ hh:mm {a,p}m
        for movie in djson
    ]
    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_bam(theater, date):
    """Get movie names and times from BAM Rose Cinema's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://www.bam.org/Filmsection'

    soup = soup_me(BASE_URL)

    relevant_movies = soup('div', {'data-sort-date': re.compile('^{}'.format(
                                      date.replace('-', '')))})
    movie_names = [m.find('div', class_='listModuleTitleMed listBlock').text
                   for m in relevant_movies]

    PATTERN = re.compile('[ap]m,?$', re.I)

    movie_sortedtimes = [sorted( # not always time-ordered
        [time.text.strip().replace(',', '') for time in m('li')],
        key = lambda t: float(re.sub(PATTERN, '', t.replace(':', '.')))) # 7:40PM -> 7.4
        for m in relevant_movies]
    movie_datetimes = [[DATETIME_SEP.join((date, time)) for time in times]
                       for times in movie_sortedtimes]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times


def get_movies_cobble_hill(theater, date):
    """Get movie names and times from Cobble Hill Cinema's website

    :theater: str
    :date: str (yyyy-mm-dd) (default: today)
    :returns: (list of movie names, list of lists of movie times)
    """
    BASE_URL = 'https://64785.formovietickets.com:2235/T.ASP?WCI=BT&Page=schedule&SelectedDate={}'

    soup = soup_me(BASE_URL.format(date.replace('-', '')))

    movie_names = [m.text for m in soup('a', class_='displaytitle')]

    movie_datetimes = [[DATETIME_SEP.join((date, time.text + 'm'))
                        for time in m('a', class_='showtime')]
                       for m in soup('div', class_='showings')]

    movie_times = filter_past(movie_datetimes)
    movie_names, movie_times = combine_times(*filter_movies(movie_names, movie_times))

    return movie_names, movie_times
