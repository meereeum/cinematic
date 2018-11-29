# `cinematic`
cinema from the terminal

## Usage
1. Add/edit `theaters_${MY_FAVE_CITY}`
2. Find out what's playing :movie_camera::sparkles:

Default: today's movies in NYC

`$ python ./get_movies.py`

or try..

`$ python ./get_movies.py nyc tomorrow`

`$ python ./get_movies.py boston 1/13`

## Useful bash alias

`lsmovies() { python PATH/TO/DIR/get_movies.py "$@"; }`

## e.g.

```
$ lsmovies --sorted pgh tom

______REGENT SQUARE THEATER______
(79%)  Border  |  7:00pm, 9:15pm

________________ROW HOUSE CINEMA________________
(95%)  Paths of Glory         |  4:30pm
(93%)  2001: A Space Odyssey  |  6:30pm
(86%)  The Shining            |  1:30pm, 9:30pm

__________HARRIS THEATER__________
(70%)  Prospect  |  6:00pm, 8:00pm

skipping melwood screening room...

_____________________________________MANOR THEATRE_____________________________________
(95%)  Widows                                       |  2:20pm, 4:55pm, 7:30pm, 10:00pm
(90%)  Green Book                                   |  1:45pm, 4:25pm, 7:00pm, 9:35pm
(84%)  Bohemian Rhapsody                            |  2:00pm, 4:40pm, 7:20pm, 9:55pm
(40%)  Fantastic Beasts: The Crimes of Grindelwald  |  1:50pm, 4:30pm, 7:10pm, 9:50pm

```

## Full disclosure

```
usage: get_movies.py [-h] [-f F] [--simple] [--sorted] [--filter-by FILTER_BY]
                     [city and/or date [city and/or date ...]]

positional arguments:
  city and/or date      (default: nyc today)

optional arguments:
  -h, --help            show this help message and exit
  -f F                  path/to/moviefile
  --simple              display without ratings? (default: false)
  --sorted              sort by rating? (default: false)
  --filter-by FILTER_BY
                        minimum rating threshold (default: 0)
```
