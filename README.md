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

##

```
:::oyy++dNNNNNNNNNNNNNNNNmyo/////+oshdmmmmNNNNNNNNNNNNNdhsossshmNNhyss+sdmmmmmmmmNNNNNNNNds/::::/sdm
:oydmmdmmNNNNNNNNNNNNNNhoo/::::://+ohdmNNNNNNNNNNNNNNNNNNmhyydmNNNmhhddddmmdmmdmmmNNNNNm+oo+:/oo//dm
oo//+ymmNmmmmmNNNNNNNNNy/yy::sh+:/+oydmNNNNNNNNNNNNNNNNNNNNNNNNddNNmdy+//++shmmmmNNNNNNNdhyy++yo/odm
/::::sdmmmmNNNNNNNNNNNNmd+/++//+/+oyho+dNNNNNNNNNNNNNNNNNNNNNNmsymdyo//::::/+sdmmNNNmdmNNNmh+/+soyys
o:-//::+ymNNNNNNNNNNNNNNdo++/////+yho+ohNNNNNNNNNNNNNNNNNNNNNNNNNNsohs::oo/:+omNmmmNmhhmNNNdo//oyhhh
//:+s/:/oydmmmNNNNNNNNNmhso+///+/ohdydmNNNNNNNNNNNNNNNNNNNNNNNNNNNmo+++/os+/oshdhmmNNmNNNNNms//odmhd
++/:::+oyshmNNNNNNNNNNmddhso+syhdmmmmmmmmmNNNNNNNNNNNNNNdyooosyhdmho++o+///+syyoodmNNNNNNNNNd+/omd++
mmdhyyyhsodNNNNNNNNNNNNNmmmhdmhyyyhddmdmmdmmmNNNNNNNNNmy+////++ooymmmhso//+oyyoyhmmNNNNNNNNNd+/+mNmm
mmmNmmmmmmmNNNNNNNNNNNNNNNNddy/::::/+ydmmdmmmmNNNNNNNms/////+++++ydmNmo++oshddmNmmmNNNNNNNNNd+/+dNNN
ooshdmmmmmNNNNNNNNNNNNNNNNy+o+::///:/oyhdmmNNNNNNNd+os+::+o+//++ossymNyydmNNNNNNNNNNNNNNNNNNy//+hNNN
oyhdmmNNNmNNNNNNNNNNNNNNNNhoyy/:oys:/++oydmNNNNNNNmsshs//syo/++ooso/ohyhNNNNNNNNNNNNNNNNNNNNho++smNN
ssyyyyhhmNNNNNNNNNNNNNNNNNmd////::/oyhhdmmmNNNNNNNNNm+++++////+syyo//shmNNNNNNNNNNNNNNNNNNNNNmhysdNm
:::://osymNNNNNNNNNNNNNNNmNd:+++/:ymNNNmmNmNNNNNNNNNNysooo///+oyhsosydmNNNNNNNNNNNNNNNNNNNNNNNNNNmNd
::::://+smNNNNNNNNNNNNNNNNNm:+sooymmdddmmmmmmmmNNNNNNdhyoo++ooydddhddmNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
:::::/+oydmNNNNNNNNNNNNNNNNm+/++ohy+///+hdmmmmmmmmNNNNNmddhhhdmNNNmNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
syo:://ososdNNNNNNNNNNNNNNNNmmmh+o+:::::/+oymmmmmmmNNNNNNNmhyyyyhdmNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
///:/+oyh+/shmNNNNNNNNNNNNNNNNNmoso/::///:/+ydddddmNNNNNNdo+////+oymNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
::::/oyhh++oymNNNNNNNNNNNNNNNNNhoyho/+hhsosooydysssmNNysso////////oymNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN
////+shddhdoymNNNNNNNNNNNNNNNNNs++/////+///+shhoodmmNm+sdh+//yhs:/osdmNNNNNNNNNNNNNNNNNNNNNNNNNNNNNy
ooosshdhsodmmmNNNNNNNNNNNNNNmmmdmhoo/::::/+sssoohNNNNNmyooos+sso+ossyhmNNNNNNNNNNNNNNNNNNNNNNNNNNNs+
mdddhs+:/ymNNNNNNNNmddhyyyyyhddmmmNmhs/:/+osyddmNNNNNNNd+oos+///+osymNmNNNNNNNNNNNNNNNNNNNNNNNNNdyyd
Nmmmms/odmNNNNNNNNNmdo:::::/shshmmNmmmy//+syhhNNNNNNNNNmosooo//++syyhddNNNNNNNNNNNNNNNNNNNNNNNmhsyNd
mmNNNmmNNNNNNNNNNNNmy:::---:::/hmmmmNNNdyso+smNNNNNNNNNmso++++/+osyhsyhdNNNNNNNNNNNNNNNNNNNNNNmmdmNy
mNNNNNNNNNNNNNNNNhoo+:-:///:::/oddmmNNNNmsoymNNNNNNNNNNNho+++++oyhyos+ohNNNNNNNNNNNNNNNNNNNNNNNNNNNh
mmmNNNNNNNNNNNNNNy/hdo::yhy::+//+sydmNNNNmdNNNNNNNNNNNNmmdyssyyyso+++sdNNNNNmdhhhdmNNNNNNNNNNNNNNNdy
mmNNNNNNNNNNNNNNNmhy+::::::::::/+shmNNNNNNNNNNNNNNNNNNhshs/oo//////+shmNNNhs/::::/+hmNNNNNNNNNNNNmyy
mmNmmNNNNNNNNNNNNNNNs::::::::://:/+smNNNNNNNNNNNNNNNNNNmo///o+////odmmmhys/:::::::/sdNNNNNNNNNNNNNNm
NNNNNNNNNNNNNNNNNNNNm++/:::::::/+/smmmmNNNNNNNNNNNNNNNNy://+o+//:+mNmdd/ydy::ydh////+ydmNNNNNNNNNNNN
mNNNNNNNNNNNNNNNNNNNmo//:::::/+ss+ymmmmNNNNNNNNNNNNNNNh+:o++/:::+dNNmNmysyo//+so/oo++syshmNNNNNNNNNN
NmNNNNNNNNNNNNNNNNNNNs::::ohdmNNNNNNNNNNNNNNNNNNNNNNNms//+/::::+mNNNNNmmNs/++/::::/+oyss/omNNNNNNNNN
yNNNNNNNNNNNNNNNNNNNNNdhhdmdddhhhdmmNmmmmNNNNNNNNNNNNs:://::/yddmmNmmmmNmsoo+/::://+sy/+ymNNNNNNNNNN
/dNNNNNNNNNNNNNNNNNNNNNNds//:::///+shdmmNNNNNNNNNNNNm/:::::/sNmmmmmNNNNmmhhys+/://+sdddNNNNNNNNNNNNN
+ddmNNNNNNNNNNNNNNNNNNmh+:::::::////+dmNNNNNdhdddmNNNd/::::/hNmmNNmNNNNmNms//://+shhyymNNNNNNNNNNNNN
dhhddmNNNNNNNNNNNNNNNmh+:::::::::///+smNNNNNm+//+yNNNNmhs+/sNNNmmNNNmNNNNNmhyyhmmdhhhdmNNNNNNNNNNNNN
mmmmmNNNNNNNNNNNNNNdo+/::::://::://+oymmmNNNNo///+sNNNNNNNmmdNmNdmNNmmmNNNNNNNNNNNNNNmmNNNNmNNNNNNNN
NmmNNNNNNNNNNNNNNNNd:ymmo::dmm+:+o+++so+/odNd///+oymNNNNNNNNNNmmNNNmmmmmNNNmmmNNNmmNmmmNNNNNNNNNNNdy
NNNNNNNNNNNNNNNNNNNNho+o////+//oo///odh///sd+//++sddNNNNNNNNNNNNNNNmNNNNNNNmmmmNddmNNNNNNNNNNNNNNs++
dmmNNNNNNNNNNNNNNNNds++//+o+:::::/+ooyso/+s+:://ohhdNNNNNNNNNNNNNNNNmNdyso+++oyyhmNNNNNNNNNNNNNNh+++
mNNNNNNNNNNNNNNNNNdhs++++///:::::/ossho+sdo///+oydNNNNNNNNNNNNNNNNNNmms/::::::/ohmNNNNNNNNNNNNNNyyyh
NNNNNNNNNNNNNNNNNNNNdyoooo+//:::/+syhmhhmh///+oydNNNNNNNNNNNNNNNNNNhss//:::::::/shddmmmmNmNNNNNNmmmN
NNNNNNNNNNNNNNNNNNNNNNdyssosssyo+shdmmhhysy/+yhhmmNNNNNNNNNNNNNNNNNyodh+:/yhh+:/+ooshdyhNNNNNNNNNNNN
NNNNNNNNNNNNNNNNNNNNNNmds+/oyydhhyymNmdo/ymdsosyhdNNNNNNNNNNNNNNNNNmyhh+//yhh+/oysoyymmmmNNNNNNNNNNN
NNNNNNNNNNNNNNNNNNNNmds++///soyyhhhdmNmmmNNmmdhhhdNNNNNNNNNNNNNNNNNNNms////////++ooo+hNNmNNmNNNNNNNN
NNNNNNNNNNNNNNNNmNNmh+:::::://shyhhhdmNNNNNNmmmmmNNNNNNNNNNNNNNNNNNNNNdo+//:::/++oosdyNNNNNNNNNNNNNN
NNNNNNNNNNNNNNNNNNNh/:::::::::/shmmmmNNmNNNNNNmmmmmNNNNNNNNNNNNNNNNNNNNhyso++++++sydhyNNNNNNNNNMNNMM
mmNNNNNNNNNNNNmddmh/:::::::::::/oydmmNNNNNNNNNNmmmmmmmNNNNNNNMNNNNNNNNNmdmmNmmmmdmdyoyNNmNNNmNMMMMMN
NNNNMNNNNNMNNm/+oo/:::///:::::////+shNNNNNNNNNNmmmmmmmmmNNNNNNNNNMNNNNNNNNNNNNNNNNNNmmNmhdmmdmNMMMMM
NNNNNNNNMNNNNm/yNNh::ymmh::+////++oydmNNmhmNNNNmmmmmNNNNNNNNNNNNNNNNNNmdddddmmmmmNNNNNNNmdhhdmNNMMNN
NNNNNNNNNNNNNNdyys/::+yyooss+////+ooooshdhNNNNNNNNNNNNNNNNNNNNNNNNNNNh////+oosyhyydNNNNMNNNdddmmmNNN
NNNNNNMNNNNNNNNNd////::/+/:::://+shys/+osdNNNNNNNNNNNMNNNMNNNNNNNNNNNy//:::::/+syyydNNNNNNNNmddddddm
hs++oshmNNNNNNNNm+////::::::///++++o+/+syymNNNNNNNNNNMNNNNNNNNNNNNNNmy+/:::::::/++osydNNNNMNNNmddddd
::::://ohNNNNNNNNs/::::::::///////oo/oymmNNNNNNNNNNNNNMNNNMNNNNNNNNNmo/::::::::::////+sdNNMNNNmddddd
::::::://ymNNNNNNmyyso+/:///////++/symNNNNNNNNNNNNNMNNNNNNMMMNNNdoosso/::::::::/::::///+sdNNNNNhmddd
::::::://+sdNNNNNNyoo+/:::///+/+ohdmNNNNNNNNNNNNNNNNNNNNNNMNMNNNh/yddy/:/syso::/+++/+///++sdNNmddddh
:::///++osyhNNNNNNysoo+////+oo+++shdNmNNNNNNNNNNNNNNNNNNNNMNNNNNmsymmd///dNNm//syyyo+/////+syhNddNdd
/+ossyyhhhhdNNNNNNNNNNNmmmmmdyo+/sdNmNNNNNNNNNNNNNNMNNNNNNMNNNNNNNmdh+////+ooossso++//++/+soohmdmNdm
hdmmNNNNNNNNNNNNNNNNNNNNNNNMNNNmdmmmmmNmmmNNNNNNNNNMNNNNNMMNNMMMNNNNNoo+++:::///+ooo//s//ssosdmmmNNN
NNNMNNNNNNNNhoooo+oshdmNNNNNNNNNNNNNmmmmmmNNmmNNNNNNNNNMNMMNNNMMMMMNNy+////:///+oooos+ssyyoohmNmNNNM
NNNMNNNNNNmo:::::::///+ohNNNNNNMNNNNNmmmmmmmmmmNNNNNNNNNNMMNMMNNMNNNNhhyss+////++oyhdsyddyyydNmmNNNN
NNNNNNNNNd+:::::::::///osmNNNNNNNNNNNNmmmmmmmmmmmmmNNNMMNNNNMMNNMNNNNdo+//////+ohhdh++hdyhdmNNNNNNNN
NNNdhhhdm+::/:://:::::/sdmNNNNNNNNNNMNNmmmmmmmmmmmmNNNNNMMMMNNmdmmdmmms+/++syyhdhoo+/shssddNNNNNNNNN
NNy:+yso/:::/++/://////+ydNNNNNNNNNNNNNmmmmmmmmmmNNNNNNNMNNmhyhdmmmNNNNmmmdhooo+//++ososmNNmNNNmNNNN
NNs/mNNNs/:yNNNd/://:///+ohmNNNNNNNNMNNmmmmmmmmmmmNNNNNMMNmmmNNNNMNNNNNNNNoo+///+++ooohNNNNNmdmNNNNN
NNmsoyys//:oddho/shyoo+++oo+yyhmNNNNNNNNNmmmmNmmmmNNNNNMNNNNNMNMNNNNNNNNNmohs+++++ssdmNNNNNmNNNNNNNN
NNNNNd+/+//s//ohdh+////++ydhyo///smNNNmNNmmmmmmmmNNNNNNNNNNNNMMMNNNNNMMMNmsmhyoo+oyhNNNNNmmdmNNNNNNm
NMMNNo///++/+oss+::://++osdNms+s+/oNNmmNmmmmmmmNNNmmmNNNNNMMNNNNNNNNNNMMNNdNmyso+hhNNmmNmmmmNNNNNNmN
NMNNNNso++o:::::::::+ooo+yddo+s/:/:yNmNNmmmmmmmNNmmmNNNNNNNMNMNMNNNNMNNNNNmNmhoydmNNNNNNNmmNNNNNNNNN
NMNNNNy+////:::::::/+sssshds+y+::+ommmNmmmmmNNNNmmNNNNNNMNNMMNNNNMMNNNNNNmmNNmydNNNNNNNNNNNNNNNNNNNN
NMNNNmsso+++/::::::/ossyyyho////sdmmmNNmmmmmmmmmmmNNMMNNNMMMMNNNNNMNNNNNNmmNNNNMNNMMNNNNNNNNNNMMNNNN
NNNNNmoo+//::://///+osyyhdmsosdNNNmmNNmmmmmmmmNNNNNNNNNNMMMNNMNNNNMNMMNMNNNNNNNNMNMNNNMMNNNNNMMNNNNN
NNNNMNs+/////++++++osyhdmmmmddNNNmmmNmmmmmmmmNNNNNNMNNNNNMMMNNNNNNMNNMNNNNNNNMMMNNMNNMNMNNNNNNMMMNNM
NNNNNNhssoosyhhhhyhhhdmmmdhyymNNNmmmNNmmmmmmNNNNNMNNNNNNNMMNNNMNNNNNNNNNMNNNNNNNNNNNNNMNNNNMNMMMNNNM
NNNMMNNNNNmmmddhyyyyyyysoo+ohmNNNNNNNNmmmmmmNNNNMNNNNMNNNNMMMNMNNNNNMMNNNmmNNNNNNNNNNNNNNNNMMNMNMMNN
NNNNNNNNNNNNNyo+++++++++//+oyyNNNNNNNNmmmmmmmNNNNNNmNNMNNMNNNNMNNNNNNNNm+//+oo+yhhysooosymNNMMMMMMNN
NNNNNNNNNNNNNs/////////////:/dNNNNNNNNNNmmmNNNNNNNNNNNMNNNMMMNNNNNNNNNNs////:::::::://+ohmNNNMNMNNNN
NNNNNNNNNNNNN+///////::::::omNNNNNNNNNNNNNNNNNNNNNNmNNNMMNNMNNMNMNyyyys//////:::::://+osdNNNNMNMNNMN
NNNNNNNNNNNNm:://::::----:smNNNNNNNNNNNNNNNNNNNmNNNNNNNMMNNMNNNNNd/+yyo+::::///::://+ossdmNNNNNMNNMN
NNNNNNNNNNNNd:::::-------sNNNNNNNNNNNNNMNNNNNNNNNNNNNNMNMNNNNNNNNd/sNNNm+/:smmmds//oysyysdmmmNNMNNMM
NNNNNNNNNNNh///:::-----:sNNNNNNNNNNNNNNNNNNNNNNNMNNNNNNNNNNNNNNMNNdsyhdy/o/omNNNs//yhhhhhhdddmNNNNNM
NNNNNNNNNNh:::///:----:sNNNNNNNNNNNNNNNNNNNNNMMNNNMNNNNNNNNNNNNNNNNNd+++oo+/++oo+oyhysssydNNmmNNNNNN
MNMNNNNNNd/::/+/:----:yNNNNNNNNNNNNNNNNNNNNNNNNNNNMMNNNNNNNNNNNNNNNNm+/+ooys///++///+oyyhdmdydyhdmNN
MNNNNNNNd/::/o+:----:yNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNMNNNNNNNNNNNNNd//+//oo//::://+shddhhy+yy::/yNN
NNNNNNNNy::://:/---:hNNNNNNNNNNNNNNNNNNNNNNNNNNNNNMMNNNNNNNNNNMNNNNNd+hys+///:::///oyddhhyo:/+++yNNM
NNNNNNNNd+::::/+--:hNNNNNNNNNNNNNNNNNNNNNNNNNNNMNNNNNNNNNNNNNNNNNNNNmodddhy+::::///oyhhdmmd/+hdmNNNM
NNNNNNNNN+::::+:-/dNNNNNNNNNNNNNNNNNNNNNNNNNNNNNMMNNNNNNNNNNNNNNNNNNNsoo+++/:::://+shhdNNmyyNNNNNNNM
NNNNNNNNN+::://-/dNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNMNNNNNNNNNNNNNNNNNNms/:::::::://+sydmNmdoomNMNNNNNM
NNNNNNNNm/:::/-/dNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmdyso+++//::://++oshmmdhso/+ymNNNNNNNN
NNNNNNNNd:::::+mNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmy+/::::::::///shddddhyo/::://ymNNmmmNNN
ysoooshmo::::+mNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNdo/:::------:::://+//:::::::::+ydhys++sdN
oooo/::/::::omNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNho/:::-----:::::::::/:::::::://o+++/:::/o
Nmsoyy+/:::hNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmho/:::-:::::::::/::::::::::::::/::----::
Nddooh:/-:yNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNho/::-::::::::://::::---:::::----------
mNh::s//:sNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmy::::::::::--:-:::::--::-----------::
dmy::o/:sNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNho:--:----------------------------::
h/o+/+:oNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNh/:----------------------------::-
:-:ydsomNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmys+:--------------------------::
+oymmomNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmmmNNNmdyo/-----------------:/syhhd
NNNNNmNNNNNNNmmmmmmmNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNmmNNNmmmho/////////osssyhdmNNNNN
```
